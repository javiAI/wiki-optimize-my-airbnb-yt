"""
retrieve.py — Token-free vault retrieval using BM25-style scoring.

Navigates wiki/{lang}/ without consuming Claude tokens.
Returns the top-K most relevant atom files for a given query,
pre-loaded as a JSON block ready for Claude to consume directly.

Usage:
    python3 .claude/scripts/retrieve.py --query "¿Cómo subo mi precio base?" --lang es
    python3 .claude/scripts/retrieve.py --query "pricing strategy" --lang en --top 5
    python3 .claude/scripts/retrieve.py --query "PriceLabs occupancy" --lang es --output paths

Integration:
    Use at the start of /query skill to pre-load atoms without Claude navigating the vault.
    Claude reads the returned JSON and responds immediately — no index/MOC reads needed.

Approach:
    Pure-Python BM25 (no external deps). Indexes atom claims, topics, and body text.
    Scoring: BM25 term frequency over query tokens, with topic-match boost.
"""

import argparse
import json
import math
import pickle
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import kind_dir  # noqa: E402
from frontmatter import parse_frontmatter  # noqa: E402

CACHE_VERSION = 6


# BM25 parameters
K1 = 1.5
B = 0.75
TOPIC_BOOST = 3.0     # Score multiplier when query token matches a topic
CLAIM_BOOST = 2.0     # Score multiplier for matches in claim vs body

# Hub-shape boost: multiplied onto the BM25 score of a hub whose slug/aliases
# match the query, so a curated entity/comparison page outranks the atoms it
# cites. Tuned so a hub almost always lands in the top-3 when shape matches.
HUB_BOOST_MULTIPLIER = 4.0


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _fold(text: str) -> str:
    """NFKD-normalise + strip combining marks so 'qué' and 'que' tokenise alike.

    Without folding, accent variation kills BM25 recall across atoms vs queries.
    """
    if text.isascii():
        return text
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def tokenize(text: str) -> list[str]:
    """Lowercase, NFKD-fold, then split on word boundaries."""
    return _TOKEN_RE.findall(_fold(text.lower()))


# Query-shape detection: cheap heuristics. The vault grew up around atoms, so
# default ("auto") falls through to atom-shape unless an explicit signal fires.
COMPARISON_CUE_RE = re.compile(
    r"\b(vs\.?|versus|compared to|alternative to|frente a|en lugar de|comparado con|"
    r"diferenc(?:ia|es) entre|cómo elijo entre|cómo decido entre|elegir entre)\b",
    re.IGNORECASE,
)
TOPIC_CUE_RE = re.compile(
    r"\b(panorama|estrategia|overview|landscape|how does \w+ work|cómo funciona)\b",
    re.IGNORECASE,
)


def detect_query_shape(query: str, registry_aliases: set[str]) -> str:
    """Return 'comparison' | 'entity' | 'topic' | 'atom'.

    Order: comparison cues first (most specific) → registered entity mention →
    topic cue → atom (default). `registry_aliases` is the folded-lowercased set
    of all aliases declared in meta/entities-registry.yaml — empty set if the
    file is missing or unreadable.
    """
    if COMPARISON_CUE_RE.search(query):
        return "comparison"
    if registry_aliases:
        q_folded = _fold(query.lower())
        for alias in registry_aliases:
            if alias and re.search(r"\b" + re.escape(alias) + r"\b", q_folded):
                return "entity"
    if TOPIC_CUE_RE.search(query):
        return "topic"
    return "atom"


_REGISTRY_ALIASES_CACHE: dict[Path, set[str]] = {}


def load_registry_aliases(vault_path: Path) -> set[str]:
    """Lowercased aliases from meta/entities-registry.yaml; empty on absence.

    Module-level cache by vault_path: the registry is process-stable for a
    CLI invocation, so re-reading on every retrieve() is wasted I/O.
    """
    if vault_path in _REGISTRY_ALIASES_CACHE:
        return _REGISTRY_ALIASES_CACHE[vault_path]
    p = vault_path / "meta" / "entities-registry.yaml"
    if not p.exists():
        _REGISTRY_ALIASES_CACHE[vault_path] = set()
        return _REGISTRY_ALIASES_CACHE[vault_path]
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import _load_yaml
        data = _load_yaml(p) or {}
    except Exception:
        _REGISTRY_ALIASES_CACHE[vault_path] = set()
        return _REGISTRY_ALIASES_CACHE[vault_path]
    out: set[str] = set()
    for slug, meta in (data.get("entities") or {}).items():
        meta = meta or {}
        title = meta.get("title") or slug.replace("-", " ").title()
        out.add(_fold(title.lower()))
        for a in (meta.get("aliases") or []):
            if a:
                out.add(_fold(a.lower()))
    _REGISTRY_ALIASES_CACHE[vault_path] = out
    return out




class VaultIndex:
    """In-memory BM25 index over vault atoms."""

    def __init__(self, vault_path: Path, lang: str, cache_dir: Path = None):
        self.vault_path = vault_path
        self.lang = lang
        self.atoms: dict[str, dict] = {}  # stem → {fm, body, tokens_claim, tokens_body, path}
        self.df: Counter = Counter()       # document frequency per term
        self.avgdl: float = 0.0
        self.hub_stems: dict[str, list[str]] = {"entity": [], "comparison": []}
        self._cache_path = (cache_dir / f"retrieve-{lang}.pkl") if cache_dir else None
        if not self._load_cache():
            self._build()
            self._save_cache()

    def _wiki_dir(self) -> Path:
        return kind_dir(self.vault_path, "wiki", self.lang)

    def _queries_dir(self) -> Path:
        return kind_dir(self.vault_path, "queries", self.lang)

    def _corpus_mtime(self) -> float:
        """Latest mtime across wiki/ + queries/ for this lang. 0 if both missing."""
        latest = 0.0
        for d in (self._wiki_dir(), self._queries_dir()):
            if not d.exists():
                continue
            m = d.stat().st_mtime
            if m > latest:
                latest = m
            for p in d.glob("*.md"):
                m = p.stat().st_mtime
                if m > latest:
                    latest = m
        return latest

    def _load_cache(self) -> bool:
        if not self._cache_path or not self._cache_path.exists():
            return False
        try:
            with open(self._cache_path, "rb") as f:
                blob = pickle.load(f)
        except Exception:
            return False
        if blob.get("version") != CACHE_VERSION:
            return False
        if blob.get("mtime", 0) < self._corpus_mtime():
            return False
        self.atoms = blob["atoms"]
        self.df = blob["df"]
        self.avgdl = blob["avgdl"]
        self.hub_stems = blob.get("hub_stems", {"entity": [], "comparison": []})
        return True

    def _save_cache(self):
        if not self._cache_path:
            return
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            blob = {
                "version": CACHE_VERSION,
                "mtime": self._corpus_mtime(),
                "atoms": self.atoms,
                "df": self.df,
                "avgdl": self.avgdl,
                "hub_stems": self.hub_stems,
            }
            with open(self._cache_path, "wb") as f:
                pickle.dump(blob, f)
        except Exception:
            pass  # cache is best-effort; query still works without it

    def _build(self):
        wiki_dir = self._wiki_dir()
        queries_dir = self._queries_dir()
        if not wiki_dir.exists() and not queries_dir.exists():
            return

        total_len = 0
        # Saved queries are cached answers; surfacing them at retrieval lets
        # /query short-circuit when a near-identical question was synthesised.
        sources: list[tuple[Path, str]] = []
        if wiki_dir.exists():
            sources.extend((p, "wiki") for p in wiki_dir.glob("*.md"))
        if queries_dir.exists():
            sources.extend((p, "query") for p in queries_dir.glob("*.md"))

        for p, source_kind in sources:
            text = p.read_text(errors="replace")
            fm, body = parse_frontmatter(text)
            claim = fm.get("claim", "") or fm.get("question", "")
            topics = fm.get("topics", [])

            tokens_claim = tokenize(claim)
            tokens_body = tokenize(body)
            # claim tokens count CLAIM_BOOST× and topic tokens TOPIC_BOOST× via
            # repetition — BM25 sees them as more frequent in the document.
            tokens_doc = (
                tokens_claim * int(CLAIM_BOOST) +
                [t for topic in topics for t in tokenize(topic)] * int(TOPIC_BOOST) +
                tokens_body
            )

            tf_counter = Counter(tokens_doc)

            if source_kind == "query":
                page_type = "query"
                # Atoms and queries both follow `<topic>--<slug>.md` and could
                # collide on stem; namespace the dict key to keep them separate.
                key = f"query::{p.stem}"
            else:
                page_type = (fm.get("type") or "atom").strip().lower()
                key = p.stem
            slug = _fold((fm.get("slug") or "").strip().lower())
            aliases = [_fold(str(a).lower()) for a in (fm.get("aliases") or []) if a]
            subjects = [_fold(str(s).lower()) for s in (fm.get("subjects") or []) if s]

            self.atoms[key] = {
                "stem": p.stem,
                "path": str(p),
                "fm": fm,
                "body": body[:500],
                "tf": tf_counter,
                "doc_len": len(tokens_doc),
                "topics": topics,
                "page_type": page_type,
                "slug": slug,
                "aliases": aliases,
                "subjects": subjects,
            }
            if page_type in self.hub_stems:
                self.hub_stems[page_type].append(key)
            total_len += len(tokens_doc)
            for term in set(tokens_doc):
                self.df[term] += 1

        n = len(self.atoms)
        self.avgdl = total_len / max(n, 1)

    def score(self, query: str, top_k: int = 6, shape: str = "atom") -> list[tuple[float, str]]:
        """Return [(score, stem), ...] sorted descending.

        `shape ∈ {atom, entity, comparison, topic}` activates hub boosts: when
        shape is `entity` or `comparison`, hub pages whose slug / aliases /
        subjects match the query get HUB_BOOST_MULTIPLIER applied to their
        BM25 score, so a curated hub outranks the atoms it cites.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        q_lower = _fold(query.lower())
        n = len(self.atoms)
        scores: dict[str, float] = defaultdict(float)

        for term in query_tokens:
            df_term = self.df.get(term, 0)
            idf = math.log((n - df_term + 0.5) / (df_term + 0.5) + 1)
            for stem, atom in self.atoms.items():
                tf = atom["tf"].get(term, 0)
                if tf == 0:
                    continue
                dl = atom["doc_len"]
                norm_tf = tf * (K1 + 1) / (tf + K1 * (1 - B + B * dl / self.avgdl))
                scores[stem] += idf * norm_tf

        # Hub boost — promote curated pages when the user is asking a hub-shape
        # question. Match slug / aliases (entity) or subjects (comparison)
        # against the raw query string (case-insensitive, word-bounded).
        if shape in ("entity", "comparison"):
            for stem in self.hub_stems.get(shape, ()):
                atom = self.atoms[stem]
                tags = list(atom["aliases"])
                if atom["slug"]:
                    tags.append(atom["slug"].replace("-", " "))
                if shape == "comparison":
                    tags.extend(s.replace("-", " ") for s in atom["subjects"])
                hit = False
                for tag in tags:
                    if not tag:
                        continue
                    if re.search(r"\b" + re.escape(tag) + r"\b", q_lower):
                        hit = True
                        break
                if hit and scores.get(stem, 0) > 0:
                    scores[stem] *= HUB_BOOST_MULTIPLIER

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [(score, stem) for stem, score in ranked[:top_k] if score > 0]

    def get_atom_content(self, key: str) -> dict:
        """Return full atom (or saved-query) content for pre-loading into Claude context."""
        atom = self.atoms.get(key)
        if not atom:
            return {}
        path = Path(atom["path"])
        full_text = path.read_text(errors="replace")
        fm, body = parse_frontmatter(full_text)
        return {
            "stem": atom["stem"],
            "path": atom["path"],
            "type": atom["page_type"],
            "claim": fm.get("claim", "") or fm.get("question", ""),
            "topics": fm.get("topics", []),
            "confidence": fm.get("confidence", ""),
            "lang": fm.get("lang", self.lang),
            "body": body,
            "sources_url": fm.get("url", ""),
        }


def retrieve(query: str, lang: str, vault_path: Path, top_k: int = 6, output: str = "json",
             cache_dir: Path = None, shape: str = "auto") -> str:
    """
    Main retrieval function.

    output modes:
      json  — full atom content as JSON array (for Claude to consume)
      paths — just the file paths, one per line
      brief — stem + claim only, compact

    shape ∈ {auto, atom, entity, comparison, topic}: when `entity` or
    `comparison`, hub pages matching the query are boosted (HUB_BOOST_MULTIPLIER).
    `auto` infers the shape from the query string + entity registry.
    """
    if shape == "auto":
        shape = detect_query_shape(query, load_registry_aliases(vault_path))

    index = VaultIndex(vault_path, lang, cache_dir=cache_dir)
    ranked = index.score(query, top_k, shape=shape)

    if not ranked:
        if output == "json":
            return json.dumps({"query": query, "lang": lang, "shape": shape,
                               "results": [], "count": 0}, ensure_ascii=False)
        return ""

    if output == "paths":
        return "\n".join(index.atoms[stem]["path"] for _, stem in ranked)

    if output == "brief":
        lines = [f"# Retrieval results for: {query} [{lang}]\n"]
        for i, (score, key) in enumerate(ranked, 1):
            atom = index.atoms[key]
            stem = atom["stem"]
            prefix = "queries" if atom["page_type"] == "query" else "wiki"
            claim = atom["fm"].get("claim", "") or atom["fm"].get("question", "")
            lines.append(f"{i}. [[{prefix}/{lang}/{stem}]] (score={score:.2f})")
            lines.append(f"   {claim[:100]}")
        return "\n".join(lines)

    # json (default) — full content for Claude
    results = []
    for score, stem in ranked:
        content = index.get_atom_content(stem)
        content["retrieval_score"] = round(score, 3)
        results.append(content)

    return json.dumps({
        "query": query,
        "lang": lang,
        "shape": shape,
        "count": len(results),
        "results": results,
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Token-free vault retrieval via BM25")
    p.add_argument("--query", "-q", required=True, help="Query string")
    p.add_argument("--lang", default=None,
                   help="Language code. If omitted, resolution chain is: "
                        "auto-detect from --query → config.yaml.active_lang → enabled[0].")
    p.add_argument("--top", type=int, default=6, help="Number of results (default: 6)")
    p.add_argument("--vault", default=None, help="Vault path")
    p.add_argument("--output", default="json", choices=["json", "paths", "brief"],
                   help="Output format: json (full content), paths (file paths), brief (stem+claim)")
    p.add_argument("--query-shape", default="auto",
                   choices=["auto", "atom", "entity", "comparison", "topic"],
                   help="Shape hint for hub boost. 'auto' infers from query + entity registry. "
                        "'entity' or 'comparison' boosts matching hub pages over their cited atoms.")
    p.add_argument("--lang-source", action="store_true",
                   help="Print resolution provenance to stderr (which step decided the lang).")
    args = p.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig, resolve_query_language

    # Vault resolution: explicit arg > config.yaml > config fallback > error
    # Let VaultConfig handle the full resolution chain (it covers all cases)
    cfg = VaultConfig(args.vault or None)

    enabled = cfg.enabled_languages
    repo_dir = Path(__file__).parent.parent.parent

    # Language resolution: explicit > auto-detect > config.active_lang > enabled[0]
    lang = resolve_query_language(repo_dir, enabled, explicit=args.lang, query_text=args.query)

    if args.lang_source:
        # Determine which step decided the language for diagnostic output
        if args.lang:
            source = "explicit"
        else:
            from config import detect_language
            detected = detect_language(args.query, enabled)
            if detected:
                source = "auto-detected"
            else:
                from config import read_config
                config_lang = read_config(repo_dir).get("active_lang")
                source = "config.yaml.active_lang" if (config_lang and config_lang in enabled) else "enabled[0] fallback"
        print(f"[lang={lang}, source={source}]", file=sys.stderr)

    result = retrieve(args.query, lang, cfg.vault_path, args.top, args.output,
                      cache_dir=cfg.cache_dir(), shape=args.query_shape)
    print(result)
