#!/usr/bin/env python3
"""Clean a YouTube auto-caption VTT into timestamped ~20s blocks.

Input: path to .vtt file
Output (stdout): markdown with [MM:SS] prefix every ~20s, deduped lines.

Auto-caption VTT pattern:
  - Each phrase appears in 2 consecutive cues: first with inline <c> word
    timings, then as "clean" plain text.
  - Next cue starts with the previous clean text + new words.
  We keep only plain-text lines, dedupe consecutive duplicates, and reset
  the block every BLOCK_SECS seconds.
"""
import html
import re
import sys
from pathlib import Path

BLOCK_SECS = 20

TIMESTAMP_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
)
INLINE_TAG_RE = re.compile(r"<[^>]+>")


def parse_ts(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def clean_line(line: str) -> str:
    line = INLINE_TAG_RE.sub("", line)
    line = html.unescape(line)
    return line.strip()


def main():
    if len(sys.argv) != 2:
        print("usage: clean_vtt.py <file.vtt>", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # Parse cues: list of (start_seconds, text_lines)
    cues = []
    i = 0
    while i < len(raw):
        m = TIMESTAMP_RE.match(raw[i])
        if not m:
            i += 1
            continue
        start = parse_ts(*m.groups()[:4])
        i += 1
        text_lines = []
        while i < len(raw) and raw[i].strip() and not TIMESTAMP_RE.match(raw[i]):
            text_lines.append(raw[i])
            i += 1
        cues.append((start, text_lines))

    # Dedupe across cues: skip lines identical to the immediately previous emitted line.
    # Also skip empty lines after tag stripping.
    emitted = []  # list of (start_seconds, text)
    last_text = None
    for start, lines in cues:
        for line in lines:
            cleaned = clean_line(line)
            if not cleaned:
                continue
            if cleaned == last_text:
                continue
            emitted.append((start, cleaned))
            last_text = cleaned

    # Group into ~BLOCK_SECS blocks
    out = []
    block_start = None
    block_lines = []

    def flush():
        if not block_lines:
            return
        mm = int(block_start // 60)
        ss = int(block_start % 60)
        out.append(f"[{mm:02d}:{ss:02d}] " + " ".join(block_lines))

    for start, text in emitted:
        if block_start is None:
            block_start = start
        if start - block_start >= BLOCK_SECS:
            flush()
            block_start = start
            block_lines = []
        block_lines.append(text)
    flush()

    print("\n\n".join(out))


if __name__ == "__main__":
    main()
