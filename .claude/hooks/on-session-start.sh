#!/bin/bash
# on-session-start.sh — SessionStart hook
# Notifies user if pending-atoms queue is non-empty, showing first filenames.

set -euo pipefail

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

if [[ -f "$QUEUE" && -s "$QUEUE" ]]; then
    # Count only lines that still point to existing files
    VALID=0
    PREVIEW=""
    SHOWN=0
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        if [[ -f "$line" ]]; then
            VALID=$((VALID + 1))
            if [[ $SHOWN -lt 3 ]]; then
                PREVIEW="${PREVIEW}  - $(basename "$line")\n"
                SHOWN=$((SHOWN + 1))
            fi
        fi
    done < "$QUEUE"

    if [[ $VALID -gt 0 ]]; then
        echo "[WikiForge] $VALID source(s) pending atom creation. Run /ingest-queue to process."
        echo -e "$PREVIEW" | head -4
        [[ $VALID -gt 3 ]] && echo "  ... and $((VALID - 3)) more"
    fi
fi

exit 0
