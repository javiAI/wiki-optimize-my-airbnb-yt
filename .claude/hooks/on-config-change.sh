#!/bin/bash
# on-config-change.sh — PostToolUse(Write) hook for vault.yml changes
# Validates per-vault config parse whenever vaults/{name}/vault.yml is written.

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

# Match vaults/{name}/vault.yml (current convention) or legacy vault.yaml inside a vault dir.
case "$FILE" in
    */vaults/*/vault.yml|*/vault.yaml) ;;
    *) exit 0 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[hook] config changed: $(basename "$FILE") — validating..."
cd "$REPO_DIR"
python3 .claude/scripts/config.py --vault "$FILE" --validate 2>&1 && true || {
    echo "[hook] ERROR: $(basename "$FILE") failed to parse — check syntax" >&2
    exit 1
}

exit 0
