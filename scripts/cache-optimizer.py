#!/usr/bin/env python3
"""
cache-optimizer.py

Analyzes log.md to profile query frequency, identify top 20% cache candidates,
and generate meta/query-cache-stats.md.

Usage:
  python3 scripts/cache-optimizer.py
  python3 scripts/cache-optimizer.py --top 20   # show top N topics
  python3 scripts/cache-optimizer.py --dry-run
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_PATH = Path(os.environ.get(
    "VAULT_PATH",
    "/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt"
))

LOG_FILE = VAULT_PATH / "log.md"
QUERIES_DIR = VAULT_PATH / "queries"
META_DIR = VAULT_PATH / "meta"

QUERY_HEADER_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] query \| (.+)$", re.MULTILINE)
TOPIC_RE = re.compile(r"^- (?:Protocol|Scope|Coverage|Respuesta guardada|Confidence).*\[\[notes/([^\]]+)\]\]", re.MULTILINE)
CACHED_RE = re.compile(r"queries/([^\]]+)\.md", re.IGNORECASE)
TOPICS_FIELD_RE = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)


def parse_log():
    """Return list of (date, title, full_entry_text) from log.md query entries."""
    if not LOG_FILE.exists():
        return []

    text = LOG_FILE.read_text(errors="replace")
    entries = []
    for m in QUERY_HEADER_RE.finditer(text):
        entry_start = m.start()
        next_header = text.find("\n## [", entry_start + 1)
        entry_text = text[entry_start: next_header] if next_header != -1 else text[entry_start:]
        entries.append({
            "date": m.group(1),
            "title": m.group(2).strip(),
            "text": entry_text,
        })
    return entries


def extract_topics_from_entry(entry):
    """Extract topic hints from a query log entry."""
    topics = []
    for m in TOPIC_RE.finditer(entry["text"]):
        stem = m.group(1)
        topic = stem.split("--")[0] if "--" in stem else stem
        topics.append(topic)
    if not topics:
        title_lower = entry["title"].lower()
        for kw in ["pricing", "cleaning", "reviews", "hospitality", "ranking",
                   "direct-booking", "occupancy", "listing-optimization",
                   "market-selection", "regulations", "tools-tech", "investing"]:
            if kw.replace("-", " ") in title_lower or kw in title_lower:
                topics.append(kw)
    return topics or ["uncategorized"]


def find_cached_queries():
    """Return dict of stem → path for all files in queries/."""
    if not QUERIES_DIR.exists():
        return {}
    return {p.stem: p for p in sorted(QUERIES_DIR.rglob("*.md"))}


def load_cached_last_verified(queries):
    """Return dict of stem → last_verified date for cached queries."""
    lv_map = {}
    for stem, path in queries.items():
        text = path.read_text(errors="replace")
        m = re.search(r"answered_on:\s*(\S+)", text)
        if m:
            lv_map[stem] = m.group(1)
    return lv_map


def build_stats(entries, cached_queries, top_n):
    topic_freq = Counter()
    topic_titles = defaultdict(list)
    is_cached = Counter()

    for entry in entries:
        topics = extract_topics_from_entry(entry)
        for t in topics:
            topic_freq[t] += 1
            if len(topic_titles[t]) < 3:
                topic_titles[t].append(entry["title"][:60])

    total_queries = len(entries)
    cutoff_idx = max(1, int(len(topic_freq) * 0.20))
    top_topics = topic_freq.most_common()[:top_n]
    cache_candidates = [t for t, _ in topic_freq.most_common(cutoff_idx)]

    cached_count = sum(1 for q in cached_queries if any(
        t in q for t in cache_candidates))
    hit_pct = round(100 * cached_count / max(1, len(cached_queries)), 1)

    lv = load_cached_last_verified(cached_queries)
    stale_stems = [
        stem for stem, lv_date in lv.items()
        if lv_date < str(date.today().replace(month=max(1, date.today().month - 1)))
    ]

    return {
        "total_queries": total_queries,
        "topic_freq": topic_freq,
        "topic_titles": topic_titles,
        "top_topics": top_topics,
        "cache_candidates": cache_candidates,
        "cached_count": len(cached_queries),
        "hit_pct": hit_pct,
        "stale_stems": stale_stems,
    }


def render_md(stats, cached_queries):
    today = date.today().isoformat()
    lines = [
        f"# Query Cache Statistics — {today}",
        "",
        f"**Total queries in log**: {stats['total_queries']}",
        f"**Cached queries in queries/**: {stats['cached_count']}",
        f"**Estimated cache coverage**: {stats['hit_pct']}%",
        "",
        "## Top Topics by Query Frequency",
        "",
        "| Topic | Queries | Cached? | Example questions |",
        "|---|---|---|---|",
    ]
    for topic, count in stats["top_topics"]:
        is_cached = "✅" if any(topic in stem for stem in cached_queries) else "❌"
        examples = "; ".join(stats["topic_titles"][topic][:2])
        lines.append(f"| `{topic}` | {count} | {is_cached} | {examples} |")

    lines += [
        "",
        "## Cache Candidates (top 20% topics)",
        "",
    ]
    for t in stats["cache_candidates"]:
        lines.append(f"- `{t}` ({stats['topic_freq'][t]} queries)")

    if stats["stale_stems"]:
        lines += ["", "## Stale Cache Entries (may need refresh)", ""]
        for stem in stats["stale_stems"][:10]:
            lines.append(f"- `{stem}`")

    lines += [
        "",
        "## How to refresh a stale cache entry",
        "",
        "1. Delete or archive the stale `queries/<stem>.md`",
        "2. Re-ask the question — the agent will re-derive and save fresh",
        "",
        f"*Generated by `scripts/cache-optimizer.py` on {today}*",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--top", type=int, default=10,
                   help="Show top N topics (default: 10)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print stats without writing")
    args = p.parse_args()

    if not LOG_FILE.exists():
        print(f"ERROR: log.md not found at {LOG_FILE}", file=sys.stderr)
        sys.exit(1)

    entries = parse_log()
    print(f"Found {len(entries)} query entries in log.md")

    cached_queries = find_cached_queries()
    stats = build_stats(entries, cached_queries, args.top)

    md = render_md(stats, cached_queries)
    out_path = META_DIR / "query-cache-stats.md"

    if args.dry_run:
        print(md)
        print(f"\n[DRY-RUN] Would write: {out_path}")
    else:
        META_DIR.mkdir(exist_ok=True)
        out_path.write_text(md)
        print(f"[OK] {out_path}")

    print(f"\nTop topics: {dict(stats['topic_freq'].most_common(5))}")
    print(f"Cache candidates: {stats['cache_candidates']}")


if __name__ == "__main__":
    main()
