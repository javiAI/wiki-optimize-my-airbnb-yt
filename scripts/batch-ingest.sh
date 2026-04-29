#!/usr/bin/env bash
# Batch-ingest sources from a list file or inline input.
# Usage:
#   batch-ingest.sh <list_file>
#   batch-ingest.sh <video_id_or_url> [<video_id_or_url> ...]
#
# Supported input formats (one per line in list file, or inline args):
#   Ek8m0ZAhMgA                              YouTube video ID
#   https://youtube.com/watch?v=Ek8m0ZAhMgA  Full YouTube URL
#   https://www.youtube.com/@ChannelName      YouTube channel (expands to all video IDs)
#   https://www.youtube.com/c/ChannelName     YouTube channel (alternate URL form)
#   Lines starting with # are treated as comments and ignored.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Resolve VAULT_NAME / VAULT_PATH
if [[ -z "${VAULT_NAME:-}" ]]; then
    source "${REPO_ROOT}/scripts/config.sh" 2>/dev/null || true
fi

LOG="${REPO_ROOT}/scripts/batch-ingest.log"

# ── Build the list of items to process ───────────────────────────────────────

TMPLIST=$(mktemp)
trap 'rm -f "$TMPLIST"' EXIT

if [[ $# -eq 0 ]]; then
    echo "usage: batch-ingest.sh <list_file | video_id | url> [...]" >&2
    exit 1
fi

# If first arg is a readable file, use it; otherwise treat all args as IDs/URLs
if [[ -f "$1" ]]; then
    # Filter comment lines and blanks
    grep -v '^\s*#' "$1" | grep -v '^\s*$' > "$TMPLIST"
else
    for arg in "$@"; do
        echo "$arg"
    done > "$TMPLIST"
fi

# ── Expand YouTube channel URLs to individual video IDs ──────────────────────

EXPANDED=$(mktemp)
trap 'rm -f "$TMPLIST" "$EXPANDED"' EXIT

while IFS= read -r line; do
    line=$(echo "$line" | tr -d '\r' | sed 's/[[:space:]]*$//')
    [[ -z "$line" ]] && continue

    if echo "$line" | grep -qE 'youtube\.com/(@|c/|channel/|user/)'; then
        echo "  [channel] Expanding: $line" >&2
        # yt-dlp --flat-playlist returns one URL per video; extract ID
        IDS=$(yt-dlp --flat-playlist --get-id "$line" 2>/dev/null || true)
        if [[ -z "$IDS" ]]; then
            echo "  [WARN] Could not expand channel: $line" >&2
        else
            COUNT=$(echo "$IDS" | wc -l | tr -d ' ')
            echo "  [channel] $COUNT videos found" >&2
            echo "$IDS" >> "$EXPANDED"
        fi
    else
        echo "$line" >> "$EXPANDED"
    fi
done < "$TMPLIST"

# ── Normalize: extract video ID from any YouTube URL ─────────────────────────

NORMALIZED=$(mktemp)
trap 'rm -f "$TMPLIST" "$EXPANDED" "$NORMALIZED"' EXIT

while IFS= read -r line; do
    line=$(echo "$line" | tr -d '\r' | sed 's/[[:space:]]*$//')
    [[ -z "$line" ]] && continue

    if echo "$line" | grep -q 'youtube\.com/watch'; then
        # https://youtube.com/watch?v=ID&... → extract ID
        ID=$(echo "$line" | grep -oE 'v=[A-Za-z0-9_-]{11}' | head -1 | cut -d= -f2)
    elif echo "$line" | grep -q 'youtu\.be/'; then
        ID=$(echo "$line" | grep -oE 'youtu\.be/([A-Za-z0-9_-]{11})' | head -1 | cut -d/ -f2)
    else
        # Assume it's already a bare video ID
        ID="$line"
    fi

    [[ -n "$ID" ]] && echo "$ID" >> "$NORMALIZED"
done < "$EXPANDED"

TOTAL=$(wc -l < "$NORMALIZED" | tr -d ' ')

if [[ "$TOTAL" -eq 0 ]]; then
    echo "No valid video IDs found in input." >&2
    exit 1
fi

OK=0; SKIP=0; FAIL=0; N=0

: > "$LOG"
echo "[$(date '+%F %T')] START batch: $TOTAL videos" | tee -a "$LOG"

while IFS= read -r VID; do
    [[ -z "$VID" ]] && continue
    N=$((N+1))
    printf "[%3d/%3d] %s " "$N" "$TOTAL" "$VID" | tee -a "$LOG"

    OUT=$("${REPO_ROOT}/scripts/ingest.sh" "$VID" 2>&1)
    RC=$?
    case $RC in
        0)
            if [[ "$OUT" == SKIP* ]]; then
                SKIP=$((SKIP+1)); echo "SKIP" | tee -a "$LOG"
            else
                OK=$((OK+1)); echo "OK" | tee -a "$LOG"
            fi
            ;;
        2)
            SKIP=$((SKIP+1)); echo "NO_SUBS" | tee -a "$LOG"
            ;;
        *)
            FAIL=$((FAIL+1)); echo "FAIL rc=$RC" | tee -a "$LOG"
            echo "    -> $OUT" | tee -a "$LOG"
            ;;
    esac
done < "$NORMALIZED"

echo "[$(date '+%F %T')] END  ok=$OK skip=$SKIP fail=$FAIL total=$N" | tee -a "$LOG"
