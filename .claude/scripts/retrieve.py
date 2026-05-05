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
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


# BM25 parameters
K1 = 1.5
B = 0.75
TOPIC_BOOST = 3.0     # Score multiplier when query token matches a topic 
CLAIM_BOOST = 2.0     # Score multiplier for matches in claim vs body 


def tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return re.findall(r'[a-záéíóúüñ\w]+', text.lower())


def _parse_frontmatter_simple(text: str) -> tuple[dict, str]:
    """Minimal frontmatter parser — extracts claim, topics, lang, sources[0].url."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end]
    body = text[end + 3:].strip()

    fm = {}
    topics = []
    in_sources = False
    for line in fm_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("claim:"):
            fm["claim"] = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("topics:"):
            raw = stripped.split(":", 1)[1].strip()
            topics = [t.strip().strip('"') for t in raw.strip("[]").split(",") if t.strip()]
        elif stripped.startswith("lang:"):
            fm["lang"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("confidence:"):
            fm["confidence"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("last_verified:"):
            fm["last_verified"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("sources:"):
            in_sources = True
        elif in_sources and stripped.startswith("url:"):
            # Extract first source's URL
            if "url" not in fm:
                fm["url"] = stripped.split(":", 1)[1].strip().strip('"')
            in_sources = False
        elif stripped.startswith("url:") and not in_sources:
            # Top-level url field
            fm.setdefault("url", stripped.split(":", 1)[1].strip().strip('"'))

    fm["topics"] = topics
    return fm, body


class VaultIndex:
    """In-memory BM25 index over vault atoms."""

    def __init__(self, vault_path: Path, lang: str):
        self.vault_path = vault_path
        self.lang = lang
        self.atoms: dict[str, dict] = {}  # stem → {fm, body, tokens_claim, tokens_body, path}
        self.df: Counter = Counter()       # document frequency per term
        self.avgdl: float = 0.0
        self._build()

    def _build(self):
        wiki_dir = self.vault_path / "wiki" / self.lang
        if not wiki_dir.exists():
            return

        total_len = 0
        for p in wiki_dir.glob("*.md"):
            text = p.read_text(errors="replace")
            fm, body = _parse_frontmatter_simple(text)
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

            self.atoms[p.stem] = {
                "stem": p.stem,
                "path": str(p),
                "fm": fm,
                "body": body[:500],  # First 500 chars for preview
                "tokens_doc": tokens_doc,
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
            idf = math.log((n - self.df.get(term, 0) + 0.5) / (self.df.get(term, 0) + 0.5) + 1)
            for stem, atom in self.atoms.items():
                tf = atom["tokens_doc"].count(term)
                if tf == 0:
                    continue
                dl = len(atom["tokens_doc"])
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
        fm, body = _parse_frontmatter_simple(full_text)
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


def retrieve(query: str, lang: str, vault_path: Path, top_k: int = 6, output: str = "json") -> str:
    """
    Main retrieval function.

    output modes:
      json  — full atom content as JSON array (for Claude to consume)
      paths — just the file paths, one per line
      brief — stem + claim only, compact
    """
    index = VaultIndex(vault_path, lang)
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
                        "auto-detect from --query → state.yaml.active_lang → enabled[0].")
    p.add_argument("--top", type=int, default=6, help="Number of results (default: 6)")
    p.add_argument("--vault", default=None, help="Vault path")
    p.add_argument("--output", default="json", choices=["json", "paths", "brief"],
                   help="Output format: json (full content), paths (file paths), brief (stem+claim)")
    p.add_argument("--lang-source", action="store_true",
                   help="Print resolution provenance to stderr (which step decided the lang).")
    args = p.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig, detect_language, read_state

    # Vault resolution: explicit arg > state.yaml > error
    if args.vault and args.vault.strip():
        cfg = VaultConfig(args.vault)
    else:
        # --vault not provided or empty; try state.yaml.active_vault
        repo_dir = Path(__file__).parent.parent.parent
        state = read_state(repo_dir)
        vault_name = state.get("active_vault")
        if vault_name:
            cfg = VaultConfig(vault_name)
        else:
            print(
                "ERROR: no vault specified. Either:\n"
                "  1) Pass --vault <path-or-name>\n"
                "  2) Set active vault: .claude/config/config.yaml with active_vault: <name>\n"
                "  3) Set $VAULT_NAME env var\n"
                "  4) Use resolve-vault.sh first: source .claude/scripts/resolve-vault.sh",
                file=sys.stderr
            )
            sys.exit(1)

    enabled = cfg.enabled_languages

    if args.lang:
        lang = args.lang
        source = "explicit"
    else:
        detected = detect_language(args.query, enabled)
        if detected:
            lang = detected
            source = "auto-detected"
        else:
            state_lang = read_state(cfg._repo_dir).get("active_lang")
            if state_lang and state_lang in enabled:
                lang = state_lang
                source = "state.yaml.active_lang"
            else:
                lang = enabled[0] if enabled else "en"
                source = "enabled[0] fallback"

    if args.lang_source:
        print(f"[lang={lang}, source={source}]", file=sys.stderr)

    result = retrieve(args.query, lang, cfg.vault_path, args.top, args.output)
    print(result)
