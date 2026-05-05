"""Tiny flat-YAML frontmatter parser shared by extract-meta.py and rank-sources.py.

Both scripts read raw/{lang}/*.md video metadata where every field is flat
(key: value), so the heavier .claude/scripts/frontmatter.parse_frontmatter is
overkill. This helper handles that simple case.
"""
import re

FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FIELD_RE = re.compile(r"^(\w+):\s*(.*)$", re.MULTILINE)


def parse_fm(text: str) -> dict:
    m = FM_RE.match(text)
    if not m:
        return {}
    return {k: v.strip().strip('"') for k, v in FIELD_RE.findall(m.group(1))}
