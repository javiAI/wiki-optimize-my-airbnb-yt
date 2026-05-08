#!/bin/bash
# set-config.sh — write runtime state (active_vault / active_lang).
# Usage: set-config.sh active_lang es
# OR:    set-config.sh active_vault oma-test-1
#
# Writes to .claude/state/wikiforge.yaml (gitignored). Thin wrapper over
# config.write_state() — for richer updates, call config.py directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_YAML="$REPO_DIR/.claude/state/wikiforge.yaml"

KEY="${1:-}"
VALUE="${2:-}"

if [[ -z "$KEY" || -z "$VALUE" ]]; then
    echo "Usage: set-config.sh <key> <value>"
    echo "Example: set-config.sh active_lang es"
    echo ""
    echo "Valid keys: active_vault, active_lang"
    exit 1
fi

case "$KEY" in
    active_vault | active_lang) ;;
    *)
        echo "Error: unknown key '$KEY'"
        echo "Valid keys: active_vault, active_lang"
        exit 1
        ;;
esac

python3 - "$REPO_DIR" "$KEY" "$VALUE" << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / ".claude" / "scripts"))
from config import write_state
write_state(Path(sys.argv[1]), **{sys.argv[2]: sys.argv[3]})
PYEOF

echo "[state] Updated $KEY = $VALUE in $STATE_YAML"
