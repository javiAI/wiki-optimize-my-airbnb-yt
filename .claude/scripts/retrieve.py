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
from collections import Counter, defaultdict
from pathlib import Path
from frontmatter import parse_frontmatter

CACHE_VERSION = 2  # bump if VaultIndex layout changes


# BM25 parameters
K1 = 1.5
B = 0.75
TOPIC_BOOST = 3.0     # Score multiplier when query token matches a topic 
CLAIM_BOOST = 2.0     # Score multiplier for matches in claim vs body 


def tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return re.findall(r'[a-záéíóúüñ\w]+', text.lower())




class VaultIndex:
    """In-memory BM25 index over vault atoms."""

    def __init__(self, vault_path: Path, lang: str, cache_dir: Path = None):
        self.vault_path = vault_path
        self.lang = lang
        self.atoms: dict[str, dict] = {}  # stem → {fm, body, tokens_claim, tokens_body, path}
        self.df: Counter = Counter()       # document frequency per term
        self.avgdl: float = 0.0
        self._cache_path = (cache_dir / f"retrieve-{lang}.pkl") if cache_dir else None
        if not self._load_cache():
            self._build()
            self._save_cache()

    def _wiki_dir(self) -> Path:
        return self.vault_path / "wiki" / self.lang

    def _wiki_mtime(self) -> float:
        """Latest mtime across the wiki dir + its atoms. 0 if dir missing."""
        wiki = self._wiki_dir()
        if not wiki.exists():
            return 0.0
        latest = wiki.stat().st_mtime
        for p in wiki.glob("*.md"):
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
        if blob.get("mtime", 0) < self._wiki_mtime():
            return False
        self.atoms = blob["atoms"]
        self.df = blob["df"]
        self.avgdl = blob["avgdl"]
        return True

    def _save_cache(self):
        if not self._cache_path:
            return
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            blob = {
                "version": CACHE_VERSION,
                "mtime": self._wiki_mtime(),
                "atoms": self.atoms,
                "df": self.df,
                "avgdl": self.avgdl,
            }
            with open(self._cache_path, "wb") as f:
                pickle.dump(blob, f)
        except Exception:
            pass  # cache is best-effort; query still works without it

    def _build(self):
        wiki_dir = self._wiki_dir()
        if not wiki_dir.exists():
            return

        total_len = 0
        for p in wiki_dir.glob("*.md"):
            text = p.read_text(errors="replace")
            fm, body = parse_frontmatter(text)
            claim = fm.get("claim", "")
            topics = fm.get("topics", [])

            tokens_claim = tokenize(claim)
            tokens_body = tokenize(body)
            # Weight: claim tokens appear CLAIM_BOOST times, topic tokens TOPIC_BOOST times
            tokens_doc = (
                tokens_claim * int(CLAIM_BOOST) +
                [t for topic in topics for t in tokenize(topic)] * int(TOPIC_BOOST) +
                tokens_body
            )

            # Pre-compute term frequencies to avoid O(L) list.count() per term in score()
            tf_counter = Counter(tokens_doc)

            self.atoms[p.stem] = {
                "stem": p.stem,
                "path": str(p),
                "fm": fm,
                "body": body[:500],  # First 500 chars for preview
                "tf": tf_counter,
                "doc_len": len(tokens_doc),
                "topics": topics,
            }
            total_len += len(tokens_doc)
            for term in set(tokens_doc):
                self.df[term] += 1

        n = len(self.atoms)
        self.avgdl = total_len / max(n, 1)

    def score(self, query: str, top_k: int = 6) -> list[tuple[float, str]]:
        """Return [(score, stem), ...] sorted descending."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

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

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [(score, stem) for stem, score in ranked[:top_k] if score > 0]

    def get_atom_content(self, stem: str) -> dict:
        """Return full atom content for pre-loading into Claude context."""
        atom = self.atoms.get(stem)
        if not atom:
            return {}
        path = Path(atom["path"])
        full_text = path.read_text(errors="replace")
        fm, body = parse_frontmatter(full_text)
        return {
            "stem": stem,
            "path": atom["path"],
            "claim": fm.get("claim", ""),
            "topics": fm.get("topics", []),
            "confidence": fm.get("confidence", ""),
            "lang": fm.get("lang", self.lang),
            "body": body,
            "sources_url": fm.get("url", ""),
        }


def retrieve(query: str, lang: str, vault_path: Path, top_k: int = 6, output: str = "json",
             cache_dir: Path = None) -> str:
    """
    Main retrieval function.

    output modes:
      json  — full atom content as JSON array (for Claude to consume)
      paths — just the file paths, one per line
      brief — stem + claim only, compact
    """
    index = VaultIndex(vault_path, lang, cache_dir=cache_dir)
    ranked = index.score(query, top_k)

    if not ranked:
        if output == "json":
            return json.dumps({"query": query, "lang": lang, "results": [], "count": 0}, ensure_ascii=False)
        return ""

    if output == "paths":
        return "\n".join(index.atoms[stem]["path"] for _, stem in ranked)

    if output == "brief":
        lines = [f"# Retrieval results for: {query} [{lang}]\n"]
        for i, (score, stem) in enumerate(ranked, 1):
            atom = index.atoms[stem]
            claim = atom["fm"].get("claim", "")[:100]
            lines.append(f"{i}. [[wiki/{lang}/{stem}]] (score={score:.2f})")
            lines.append(f"   {claim}")
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
                      cache_dir=cfg.cache_dir())
    print(result)
