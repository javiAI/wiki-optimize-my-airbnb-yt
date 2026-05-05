#!/bin/bash
# set-config.sh — Simple config.yaml writer
# Usage: set-config.sh active_lang es
# OR:    set-config.sh active_vault oma-test-1
#
# Note: This is a thin wrapper around config.py for bash convenience.
# For complex updates, use config.py directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_YAML="$REPO_DIR/.claude/config/config.yaml"

KEY="${1:-}"
VALUE="${2:-}"

if [[ -z "$KEY" || -z "$VALUE" ]]; then
    echo "Usage: set-config.sh <key> <value>"
    echo "Example: set-config.sh active_lang es"
    echo ""
    echo "Valid keys: active_vault, active_lang"
    exit 1
fi

# Validate key against known allowlist
case "$KEY" in
    active_vault | active_lang)
        ;;
    *)
        echo "Error: unknown key '$KEY'"
        echo "Valid keys: active_vault, active_lang"
        exit 1
        ;;
esac

# Use Python to update config (handles YAML parsing correctly)
python3 - "$REPO_DIR" "$KEY" "$VALUE" << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / ".claude" / "scripts"))
from config import write_config
write_config(Path(sys.argv[1]), **{sys.argv[2]: sys.argv[3]})
PYEOF

echo "[config] Updated $KEY = $VALUE in $CONFIG_YAML"
