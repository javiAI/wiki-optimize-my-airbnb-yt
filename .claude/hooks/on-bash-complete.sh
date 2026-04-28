#!/bin/bash
# on-bash-complete.sh — PostToolUse(Bash) hook
# Detects completion of ingest.sh / batch-ingest.sh runs.
# Checks if new files appeared in raw/ and updates pending-atoms queue.

set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || true)

[[ -z "$CMD" ]] && exit 0

# Only react to ingest commands
if [[ "$CMD" != *ingest* ]]; then
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${VAULT_PATH:-}" ]]; then
    CONFIG_SH="$REPO_DIR/scripts/config.sh"
    if [[ -f "$CONFIG_SH" ]]; then
        VAULT_PATH=$(grep 'VAULT_PATH=' "$CONFIG_SH" | head -1 | cut -d= -f2- | tr -d '"' | sed "s|\$HOME|$HOME|g")
    fi
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

QUEUE="$VAULT_PATH/.claude/queue/pending-atoms.txt"
mkdir -p "$(dirname "$QUEUE")"

# Find raw/ files written in last 5 minutes not yet in queue
RAW_DIR="$VAULT_PATH/raw"
if [[ -d "$RAW_DIR" ]]; then
    NEW_FILES=$(find "$RAW_DIR" -name "*.md" -newer "$QUEUE" 2>/dev/null || true)
    if [[ -n "$NEW_FILES" ]]; then
        echo "$NEW_FILES" >> "$QUEUE"
        COUNT=$(echo "$NEW_FILES" | wc -l | tr -d ' ')
        echo "[hook] Ingest complete: $COUNT new source(s) queued for atom creation"
        echo "[hook] Run /ingest-queue to process"
    fi
fi

exit 0
