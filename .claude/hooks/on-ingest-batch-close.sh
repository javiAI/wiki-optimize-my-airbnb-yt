#!/bin/bash
# on-ingest-batch-close.sh — invoked by /ingest at end of batch.
#
# 1. Drains hub enrichment queues via refresh-hubs.py (when hubs.auto_refresh).
# 2. Bumps state/.ingest-counter by the number of atoms produced in this batch
#    (passed as $1; defaults to 1 if absent).
# 3. If counter ≥ vault.yml.maintenance.audit_every_n_ingests AND
#    audit_every_n_ingests > 0 → prints an audit advisory the user can act on
#    (the hook itself does not invoke /audit; that's a slash-command, not a
#    background script). Counter resets after the advisory.
#
# Usage from /ingest:
#   bash .claude/hooks/on-ingest-batch-close.sh [N_ATOMS_PRODUCED]

set -euo pipefail

INC="${1:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${VAULT_PATH:-}" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_DIR/.claude/scripts/config.sh" 2>/dev/null || true
fi

if [[ -z "${VAULT_PATH:-}" ]]; then
    echo "[hook] WARN: VAULT_PATH not set — skipping on-ingest-batch-close" >&2
    exit 0
fi

VAULT_BUNDLE="${VAULT_NAME:-$(basename "$VAULT_PATH")}"
STATE_DIR="$REPO_DIR/vaults/$VAULT_BUNDLE/state"
mkdir -p "$STATE_DIR"

cd "$REPO_DIR"

# ── 1. Hub enrichment ────────────────────────────────────────────────────────
# Read hubs.auto_refresh from vault.yml (default true if missing).
AUTO_REFRESH=$(VAULT_NAME="$VAULT_BUNDLE" python3 -c "
import sys; sys.path.insert(0, '.claude/scripts')
from config import VaultConfig
try:
    cfg = VaultConfig()
    hubs = cfg.get('hubs', {}) or {}
    print(str(hubs.get('auto_refresh', True)).lower())
except Exception:
    print('true')
" 2>/dev/null || echo "true")

E_QUEUE="$STATE_DIR/queue/entity-enrichment.txt"
C_QUEUE="$STATE_DIR/queue/comparison-enrichment.txt"
HAS_QUEUE_WORK=0
[[ -s "$E_QUEUE" ]] && HAS_QUEUE_WORK=1
[[ -s "$C_QUEUE" ]] && HAS_QUEUE_WORK=1

if [[ "$AUTO_REFRESH" == "true" && "$HAS_QUEUE_WORK" -eq 1 ]]; then
    echo "[hook] Draining hub enrichment queues..."
    VAULT_NAME="$VAULT_BUNDLE" python3 .claude/scripts/refresh-hubs.py --vault "$VAULT_PATH" 2>&1 || \
        echo "[hook] WARN: refresh-hubs failed; queues retained for next run" >&2
elif [[ "$HAS_QUEUE_WORK" -eq 1 ]]; then
    E_COUNT=$(wc -l < "$E_QUEUE" 2>/dev/null | tr -d ' ' || echo 0)
    C_COUNT=$(wc -l < "$C_QUEUE" 2>/dev/null | tr -d ' ' || echo 0)
    echo "[hook] Hub enrichment queued ($E_COUNT entity, $C_COUNT comparison) — auto_refresh disabled. Run /refresh-hubs manually."
fi

# ── 2. Bump ingest counter ───────────────────────────────────────────────────
COUNTER_FILE="$STATE_DIR/.ingest-counter"
[[ ! -f "$COUNTER_FILE" ]] && echo 0 > "$COUNTER_FILE"
CUR=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
# Guard against non-numeric content from a corrupt file.
[[ "$CUR" =~ ^[0-9]+$ ]] || CUR=0
[[ "$INC" =~ ^[0-9]+$ ]] || INC=1
NEW=$((CUR + INC))
echo "$NEW" > "$COUNTER_FILE"

# ── 3. Audit advisory threshold ──────────────────────────────────────────────
read -r EVERY MODE <<<"$(VAULT_NAME="$VAULT_BUNDLE" python3 -c "
import sys; sys.path.insert(0, '.claude/scripts')
from config import VaultConfig
try:
    cfg = VaultConfig()
    m = cfg.get('maintenance', {}) or {}
    print(int(m.get('audit_every_n_ingests', 0)), m.get('audit_mode', 'deep'))
except Exception:
    print(0, 'deep')
" 2>/dev/null || echo "0 deep")"

[[ "$EVERY" =~ ^[0-9]+$ ]] || EVERY=0
if [[ "$EVERY" -gt 0 && "$NEW" -ge "$EVERY" ]]; then
    FLAG=""
    [[ "$MODE" == "deep" ]] && FLAG=" --deep"
    echo "[hook] Audit threshold reached: $NEW atom(s) since last audit."
    echo "[hook] Run /audit$FLAG to refresh the structural+semantic report."
    echo 0 > "$COUNTER_FILE"
fi

exit 0
