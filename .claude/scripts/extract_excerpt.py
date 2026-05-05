#!/usr/bin/env python3
"""
extract_excerpt.py — Pull verbatim transcript text at an atom's locator.

Used by propagate_atom.py to lift a native-language excerpt from
raw/{LANG}/{video}.md without invoking the LLM.

Input:
  - raw_file: path to raw/{LANG}/{video}.md (output of ingest.sh)
  - locator:  string in MM:SS-MM:SS or HH:MM:SS-HH:MM:SS form (or single-point)

Output:
  - stdout: the concatenated text of [MM:SS] blocks whose timestamp falls
    in the locator window (with ±tolerance seconds slack).
  - exit 0 on success, 2 on bad locator/raw file, 3 if window yields empty text.

Usage:
  python3 .claude/scripts/extract_excerpt.py \\
      --raw-file ~/vault/raw/es/2024-01-01--video.md \\
      --locator 01:06-01:50

  # As a library:
  from extract_excerpt import extract_at_locator
  text = extract_at_locator(Path("raw/es/v.md"), "01:06-01:50")
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_TOLERANCE_SEC = 3.0
BLOCK_PREFIX_RE = re.compile(r"^\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)$")
LOCATOR_RE = re.compile(
    r"^(?P<sh>\d{1,2}):(?P<sm>\d{2})(?::(?P<ss>\d{2}))?"
    r"(?:\s*-\s*(?P<eh>\d{1,2}):(?P<em>\d{2})(?::(?P<es>\d{2}))?)?$"
)


def parse_locator(locator: str) -> Tuple[float, float]:
    """Parse 'MM:SS-MM:SS' / 'HH:MM:SS-HH:MM:SS' / 'MM:SS' into (start_sec, end_sec).

    Single-point locators get a 20-second default window so they still match a
    block.
    """
    s = locator.strip()
    m = LOCATOR_RE.match(s)
    if not m:
        raise ValueError(f"Unrecognized locator format: {locator!r}")

    def _to_sec(h: Optional[str], mm: str, ss: Optional[str]) -> float:
        if ss is None:
            return int(h) * 60 + int(mm)
        return int(h) * 3600 + int(mm) * 60 + int(ss)

    start = _to_sec(m.group("sh"), m.group("sm"), m.group("ss"))
    if m.group("eh") is not None:
        end = _to_sec(m.group("eh"), m.group("em"), m.group("es"))
    else:
        end = start + 20.0  # single-point: assume one ~20s block
    return float(start), float(end)


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4:].lstrip()


def parse_blocks(body: str) -> list:
    """Return list of (start_sec, text) tuples, one per [MM:SS] block."""
    blocks = []
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        first_line, _, rest = chunk.partition("\n")
        m = BLOCK_PREFIX_RE.match(first_line)
        if not m:
            continue
        h_or_m = int(m.group(1))
        mm = int(m.group(2))
        ss_grp = m.group(3)
        if ss_grp is None:
            start = h_or_m * 60 + mm
        else:
            start = h_or_m * 3600 + mm * 60 + int(ss_grp)
        first_text = m.group(4).strip()
        rest = rest.strip()
        text = (first_text + " " + rest).strip() if rest else first_text
        blocks.append((float(start), text))
    return blocks


def extract_at_locator(raw_file: Path, locator: str,
                       tolerance: float = DEFAULT_TOLERANCE_SEC) -> str:
    """Return the verbatim transcript text in the locator window."""
    if not raw_file.exists():
        raise FileNotFoundError(f"raw file not found: {raw_file}")
    text = raw_file.read_text(encoding="utf-8", errors="replace")
    body = strip_frontmatter(text)
    blocks = parse_blocks(body)
    if not blocks:
        return ""

    start_sec, end_sec = parse_locator(locator)
    lo = start_sec - tolerance
    hi = end_sec + tolerance

    pieces = [t for s, t in blocks if lo <= s <= hi]
    return " ".join(pieces).strip()


def main():
    p = argparse.ArgumentParser(description="Extract excerpt at locator from raw/{LANG}/ transcript")
    p.add_argument("--raw-file", required=True, help="Path to raw/{LANG}/{video}.md")
    p.add_argument("--locator", required=True, help="Locator e.g. 01:06-01:50")
    p.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE_SEC,
                   help=f"Window tolerance in seconds (default {DEFAULT_TOLERANCE_SEC})")
    args = p.parse_args()

    raw_file = Path(args.raw_file).expanduser()
    try:
        text = extract_at_locator(raw_file, args.locator, args.tolerance)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    if not text:
        print(f"ERROR: locator {args.locator} yielded no text in {raw_file}", file=sys.stderr)
        sys.exit(3)

    print(text)


if __name__ == "__main__":
    main()
