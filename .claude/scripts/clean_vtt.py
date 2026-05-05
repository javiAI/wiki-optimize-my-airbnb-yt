#!/usr/bin/env python3
"""Clean a YouTube auto-caption VTT into timestamped ~20s blocks.

Default mode (no --start-sec/--end-sec):
    Input:  path to .vtt file
    Output: markdown with [MM:SS] prefix every ~20s, deduped lines.

Window mode (--start-sec N --end-sec M):
    Input:  path to .vtt file + start/end seconds
    Output: plain text of the cues whose start time falls in [start - tol,
            end + tol]. Used by extract_excerpt.py to lift the verbatim
            quote at an atom's locator from the target-lang transcript.

Auto-caption VTT pattern:
  - Each phrase appears in 2 consecutive cues: first with inline <c> word
    timings, then as "clean" plain text.
  - Next cue starts with the previous clean text + new words.
  We keep only plain-text lines, dedupe consecutive duplicates, and reset
  the block every BLOCK_SECS seconds.
"""
import argparse
import html
import re
import sys
from pathlib import Path

BLOCK_SECS = 20
WINDOW_TOLERANCE_SEC = 3.0

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


def parse_vtt_cues(path: Path) -> list:
    """Return (start_seconds, end_seconds, text) per cue with consecutive dedupe."""
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    cues = []
    i = 0
    while i < len(raw):
        m = TIMESTAMP_RE.match(raw[i])
        if not m:
            i += 1
            continue
        start = parse_ts(*m.groups()[:4])
        end = parse_ts(*m.groups()[4:])
        i += 1
        text_lines = []
        while i < len(raw) and raw[i].strip() and not TIMESTAMP_RE.match(raw[i]):
            text_lines.append(raw[i])
            i += 1
        cues.append((start, end, text_lines))

    emitted = []
    last_text = None
    for start, end, lines in cues:
        for line in lines:
            cleaned = clean_line(line)
            if not cleaned or cleaned == last_text:
                continue
            emitted.append((start, end, cleaned))
            last_text = cleaned
    return emitted


def render_blocks(emitted: list) -> str:
    """Group emitted cues into BLOCK_SECS markdown blocks."""
    out = []
    block_start = None
    block_lines = []

    def flush():
        if not block_lines:
            return
        mm = int(block_start // 60)
        ss = int(block_start % 60)
        out.append(f"[{mm:02d}:{ss:02d}] " + " ".join(block_lines))

    for start, _end, text in emitted:
        if block_start is None:
            block_start = start
        if start - block_start >= BLOCK_SECS:
            flush()
            block_start = start
            block_lines = []
        block_lines.append(text)
    flush()
    return "\n\n".join(out)


def render_window(emitted: list, start_sec: float, end_sec: float,
                  tolerance: float = WINDOW_TOLERANCE_SEC) -> str:
    """Return plain text of cues whose start falls in [start_sec - tol, end_sec + tol].

    The tolerance window absorbs sub-second drift between subtitle tracks (e.g.
    EN manual subs vs ES auto-translate may not align to the millisecond).
    """
    lo = start_sec - tolerance
    hi = end_sec + tolerance
    pieces = [text for start, _end, text in emitted if lo <= start <= hi]
    return " ".join(pieces).strip()


def main():
    p = argparse.ArgumentParser(description="Clean a YouTube VTT into 20s blocks or a time window.")
    p.add_argument("vtt", help="Path to .vtt file")
    p.add_argument("--start-sec", type=float, default=None,
                   help="Window mode: start of window in seconds")
    p.add_argument("--end-sec", type=float, default=None,
                   help="Window mode: end of window in seconds")
    p.add_argument("--tolerance", type=float, default=WINDOW_TOLERANCE_SEC,
                   help=f"Window tolerance in seconds (default {WINDOW_TOLERANCE_SEC})")
    args = p.parse_args()

    emitted = parse_vtt_cues(Path(args.vtt))

    if args.start_sec is not None and args.end_sec is not None:
        print(render_window(emitted, args.start_sec, args.end_sec, args.tolerance))
    elif args.start_sec is not None or args.end_sec is not None:
        print("ERROR: --start-sec and --end-sec must be used together", file=sys.stderr)
        sys.exit(2)
    else:
        print(render_blocks(emitted))


if __name__ == "__main__":
    main()
