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

STATE_DIR="$REPO_DIR/vaults/$(basename "$VAULT_PATH")/state"
QUEUE="$STATE_DIR/queue/pending-atoms.txt"
mkdir -p "$(dirname "$QUEUE")"
# First-run only: create with epoch-0 mtime so -newer matches everything below.
# DO NOT `touch` on every run — that resets mtime to NOW, making -newer return
# zero results because all raw/ files predate the just-touched queue.
[[ ! -f "$QUEUE" ]] && touch -t 197001010000 "$QUEUE"

RAW_DIR="$VAULT_PATH/raw"
if [[ ! -d "$RAW_DIR" ]]; then
    echo "[hook] WARN: raw/ directory not found at $RAW_DIR" >&2
    exit 0
fi

# Find raw/ files created after the queue file's last-write time
NEW_FILES=$(find "$RAW_DIR" -name "*.md" -newer "$QUEUE" 2>/dev/null || true)

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

exit 0
