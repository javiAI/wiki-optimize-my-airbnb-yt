#!/bin/bash
# on-session-stop.sh — Stop hook
# Runs vault-agent.py --incremental if wiki/ or moc/ files changed this session.
# Guards against recursion via stop_hook_active.

set -euo pipefail

INPUT=$(cat)
STOP_ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('stop_hook_active', False)).lower())" 2>/dev/null || echo "false")

[[ "$STOP_ACTIVE" == "true" ]] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${VAULT_PATH:-}" ]]; then
    CONFIG_SH="$REPO_DIR/scripts/config.sh"
    if [[ -f "$CONFIG_SH" ]]; then
        VAULT_PATH=$(grep 'VAULT_PATH=' "$CONFIG_SH" | head -1 | cut -d= -f2- | tr -d '"' | sed "s|\$HOME|$HOME|g")
    fi
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

LOG_DIR="$VAULT_PATH/.claude/logs"
mkdir -p "$LOG_DIR"

# Check if any wiki/ moc/ raw/ files changed
CHANGED=0
if [[ -d "$VAULT_PATH/.git" ]]; then
    CHANGED=$(git -C "$VAULT_PATH" diff --name-only HEAD 2>/dev/null | grep -cE '^(wiki|moc|raw)/' || true)
fi

if [[ "$CHANGED" -gt 0 ]]; then
    echo "[hook] $CHANGED file(s) changed — running incremental vault audit..."
    cd "$REPO_DIR"
    python3 scripts/vault-agent.py --incremental --vault "$VAULT_PATH" >> "$LOG_DIR/audit.log" 2>&1
    echo "[hook] Audit complete. See meta/agent-report-$(date +%F).md"
fi

exit 0
