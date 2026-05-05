#!/usr/bin/env python3
"""Extract YAML frontmatter from all .md files in a dir and emit a markdown table row per file.
Sorted by 'published' desc. Output columns:
  | Published | Views | Likes | Dur (s) | Auth | Transcript |
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _fm import parse_fm


def main():
    d = Path(sys.argv[1])
    rows = []
    for p in sorted(d.glob("*.md")):
        fm = parse_fm(p.read_text(encoding="utf-8", errors="replace"))
        if not fm:
            continue
        rows.append({
            "published": fm.get("published", "0000-00-00"),
            "views": fm.get("views", "0"),
            "likes": fm.get("likes", "0"),
            "duration": fm.get("duration_sec", "0"),
            "auth": fm.get("channel_authority", "?"),
            "title": fm.get("title", "untitled"),
            "path": fm.get('title', p.stem),  # Link path varies by vault version; update manually
        })
    rows.sort(key=lambda r: r["published"], reverse=True)
    for r in rows:
        print(f"| {r['published']} | {r['views']} | {r['likes']} | {r['duration']} | {r['auth']} | {r['path']} |")


if __name__ == "__main__":
    main()
