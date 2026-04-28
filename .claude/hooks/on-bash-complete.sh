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
    CONFIG_SH="$REPO_DIR/scripts/config.sh"
    if [[ -f "$CONFIG_SH" ]]; then
        VAULT_PATH=$(grep 'VAULT_PATH=' "$CONFIG_SH" | head -1 | cut -d= -f2- | tr -d '"' | sed "s|\$HOME|$HOME|g" | sed "s|~|$HOME|g")
    fi
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

QUEUE="$VAULT_PATH/.claude/queue/pending-atoms.txt"
mkdir -p "$(dirname "$QUEUE")"
touch "$QUEUE"  # Ensure queue exists before using -newer

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
fi

exit 0
