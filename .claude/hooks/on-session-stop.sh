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
    # shellcheck disable=SC1091
    WIKIFORGE_CONFIG_QUIET=1 source "$REPO_DIR/.claude/scripts/config.sh" 2>/dev/null || true
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

STATE_DIR="$REPO_DIR/vaults/$(basename "$VAULT_PATH")/state"
LOG_DIR="$STATE_DIR/logs"
mkdir -p "$LOG_DIR"

# Check if any wiki/ moc/ raw/ files changed
CHANGED=0
if [[ -d "$VAULT_PATH/.git" ]]; then
    CHANGED=$(git -C "$VAULT_PATH" diff --name-only HEAD 2>/dev/null | grep -cE '^(wiki|moc|raw)/' || true)
fi

if [[ "$CHANGED" -gt 0 ]]; then
    echo "[hook] $CHANGED file(s) changed — running incremental vault audit..."
    cd "$REPO_DIR"
    python3 .claude/scripts/vault-agent.py --incremental --vault "$VAULT_PATH" >> "$LOG_DIR/audit.log" 2>&1
    echo "[hook] Audit complete. See meta/agent-reports/agent-report-$(date +%F).md"
fi

exit 0
