#!/bin/bash
# on-session-start.sh — SessionStart hook
# Checks pending-atoms queue and notifies user.

set -euo pipefail

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

if [[ -f "$QUEUE" && -s "$QUEUE" ]]; then
    COUNT=$(grep -c . "$QUEUE" 2>/dev/null || echo 0)
    echo "[WikiForge] $COUNT source(s) pending atom creation. Run /ingest-queue to process."
fi

exit 0
