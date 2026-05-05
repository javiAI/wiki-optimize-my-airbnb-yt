#!/bin/bash
# on-bash-complete.sh — PostToolUse(Bash) hook
# Detects ingest.sh completion and updates pending-atoms queue.

set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" 2>/dev/null || true)

[[ -z "$CMD" ]] && exit 0
[[ "$CMD" != *ingest* ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${VAULT_PATH:-}" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_DIR/.claude/scripts/config.sh" 2>/dev/null || true
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

VAULT_BUNDLE="${VAULT_NAME:-$(basename "$VAULT_PATH")}"
STATE_DIR="$REPO_DIR/vaults/$VAULT_BUNDLE/state"
QUEUE="$STATE_DIR/queue/pending-atoms.txt"
# Watermark is a separate sentinel file. Using QUEUE itself as the watermark
# was racy: appending to QUEUE bumped its mtime, so any raw/ file created
# during the append window got missed on the next run.
WATERMARK="$STATE_DIR/queue/.last-ingest-scan"
mkdir -p "$(dirname "$QUEUE")"
[[ ! -f "$QUEUE" ]] && touch "$QUEUE"
# First-run only: create watermark at epoch 0 so -newer matches everything.
[[ ! -f "$WATERMARK" ]] && touch -t 197001010000 "$WATERMARK"

RAW_DIR="$VAULT_PATH/raw"
if [[ ! -d "$RAW_DIR" ]]; then
    echo "[hook] WARN: raw/ directory not found at $RAW_DIR" >&2
    exit 0
fi

# Snapshot the watermark to "now" BEFORE the scan. Files created during the
# scan/append window will still have mtime > snapshot and get picked up next
# run.
NEXT_WATERMARK=$(mktemp)
NEW_FILES=$(find "$RAW_DIR" -name "*.md" -newer "$WATERMARK" 2>/dev/null || true)

if [[ -n "$NEW_FILES" ]]; then
    echo "$NEW_FILES" >> "$QUEUE"
    COUNT=$(echo "$NEW_FILES" | grep -c . || true)
    echo "[hook] Ingest complete: $COUNT new source(s) added to queue"
    echo "[hook] Run /ingest-queue to create atoms"

    # Append a chronological entry to log.md (vault-root, llm-wiki.md §2 spec).
    # Format: `## [YYYY-MM-DD] ingest | N source(s): stem1, stem2, ...`
    LOG_FILE="$VAULT_PATH/log.md"
    DATE=$(date +%Y-%m-%d)
    STEMS=""
    SHOWN=0
    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        STEM=$(basename "$f" .md)
        if [[ $SHOWN -lt 5 ]]; then
            STEMS="${STEMS:+$STEMS, }$STEM"
            SHOWN=$((SHOWN + 1))
        fi
    done <<< "$NEW_FILES"
    if [[ $COUNT -gt 5 ]]; then
        STEMS="$STEMS, +$((COUNT - 5)) more"
    fi
    [[ ! -f "$LOG_FILE" ]] && printf '# Log\n\nChronological record of vault operations.\n\n' > "$LOG_FILE"
    printf '## [%s] ingest | %d source(s): %s\n\n' "$DATE" "$COUNT" "$STEMS" >> "$LOG_FILE"
fi

# Promote the snapshot to the new watermark only after a successful scan,
# regardless of whether new files were found. Use mv so the swap is atomic.
mv "$NEXT_WATERMARK" "$WATERMARK"

exit 0
