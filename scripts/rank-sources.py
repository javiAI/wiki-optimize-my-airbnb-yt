#!/usr/bin/env python3
"""Rank sources by §5 score (recency + popularity). specificity/authority omitted (flat).
Usage: rank-sources.py <sources_dir> [N]
Output: TSV: score<TAB>published<TAB>views<TAB>slug<TAB>title
"""
import math
import re
import sys
from datetime import date
from pathlib import Path

TODAY = date.today()
SIX_MO = 180
THREE_YR = 1095

FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FIELD_RE = re.compile(r"^(\w+):\s*(.*)$", re.MULTILINE)


def parse_fm(text):
    m = FM_RE.match(text)
    if not m:
        return {}
    return {k: v.strip().strip('"') for k, v in FIELD_RE.findall(m.group(1))}


def main():
    d = Path(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    rows = []
    for p in d.glob("*.md"):
        fm = parse_fm(p.read_text(encoding="utf-8", errors="replace"))
        try:
            pub = date.fromisoformat(fm.get("published", "2000-01-01"))
            views = int(fm.get("views", "0"))
        except (ValueError, TypeError):
            continue
        days_ago = (TODAY - pub).days
        if days_ago <= SIX_MO:
            recency = 1.0
        elif days_ago >= THREE_YR:
            recency = 0.0
        else:
            recency = 1.0 - (days_ago - SIX_MO) / (THREE_YR - SIX_MO)
        rows.append({
            "file": p.stem,
            "title": fm.get("title", "?"),
            "views": views,
            "pub": pub,
            "recency": recency,
        })

    max_views = max((r["views"] for r in rows), default=1)
    log_max = math.log10(max_views) if max_views > 1 else 1
    for r in rows:
        r["popularity"] = math.log10(max(r["views"], 1)) / log_max if log_max > 0 else 0
        # score = 0.40·recency + 0.30·popularity (+ 0.30 flat, dropped for ranking)
        r["score"] = 0.40 * r["recency"] + 0.30 * r["popularity"]

    rows.sort(key=lambda r: -r["score"])
    for r in rows[:n]:
        print(f"{r['score']:.3f}\t{r['pub']}\t{r['views']}\t{r['file']}\t{r['title']}")


if __name__ == "__main__":
    main()
