#!/bin/bash
# on-config-change.sh — PostToolUse(Write) hook for vault.yaml changes
# Validates vault.yaml parse whenever it is written.

set -euo pipefail

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null || true)

[[ "$FILE" != *vault.yaml ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${VAULT_PATH:-}" ]]; then
    CONFIG_SH="$REPO_DIR/scripts/config.sh"
    if [[ -f "$CONFIG_SH" ]]; then
        VAULT_PATH=$(grep 'VAULT_PATH=' "$CONFIG_SH" | head -1 | cut -d= -f2- | tr -d '"' | sed "s|\$HOME|$HOME|g" | sed "s|~|$HOME|g")
    fi
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

echo "[hook] vault.yaml changed — validating..."
cd "$REPO_DIR"
python3 scripts/config.py --vault "$VAULT_PATH" --validate 2>&1 && true || {
    echo "[hook] ERROR: vault.yaml failed to parse — check syntax" >&2
    exit 1
}

exit 0
