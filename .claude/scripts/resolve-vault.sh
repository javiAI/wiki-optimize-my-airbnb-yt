#!/usr/bin/env bash
# resolve-vault.sh — preamble for every vault-touching skill (/query, /ingest,
# /audit, /qa, /ingest-queue, ...).
#
# Behavior:
#   - Accepts per-call overrides:
#       --vault <name>   → exports VAULT_NAME (skips state lookup)
#       --lang  <code>   → exports WIKIFORGE_LANG (read by skills + retrieve.py)
#     This wires the same arg shape into every slash command, so a frontend
#     can do `/query --vault apt-101 --lang es "..."` without touching state.
#   - Resolves $VAULT_PATH / $VAULT_NAME via config.sh (state.active_vault,
#     single-bundle auto-pick, or loud-error on 2+ bundle ambiguity).
#   - On success: prints `[wikiforge] Using vault: <name> (<path>)` to stdout.
#   - On failure: exits non-zero (config.sh already printed the helpful error).
#
# Usage from a skill:
#   bash .claude/scripts/resolve-vault.sh [--vault NAME] [--lang CODE] || exit 1
#
# Or sourced (so the calling shell inherits VAULT_PATH/VAULT_NAME/WIKIFORGE_LANG):
#   source .claude/scripts/resolve-vault.sh [--vault NAME] [--lang CODE] || return 1

set -euo pipefail

_RV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_RV_REPO_DIR="$(cd "$_RV_SCRIPT_DIR/.." && pwd)"

# Parse per-call flags. Unknown args are left in "$@" so the caller can
# forward them to the actual command.
while [[ "${1:-}" == --* ]]; do
    case "$1" in
        --vault)
            export VAULT_NAME="${2:?--vault needs a value}"
            shift 2 ;;
        --lang)
            export WIKIFORGE_LANG="${2:?--lang needs a value}"
            shift 2 ;;
        --) shift; break ;;
        *)  break ;;  # unknown flag → leave for caller
    esac
done

# config.sh is idempotent — re-sourcing is safe. We don't pass QUIET because
# this script's whole job is to surface vault selection (or its failure).
# shellcheck disable=SC1091
source "$_RV_SCRIPT_DIR/config.sh"

if [[ -z "${VAULT_PATH:-}" ]]; then
    # config.sh already printed the helpful error to stderr.
    unset _RV_SCRIPT_DIR _RV_REPO_DIR
    if (return 0 2>/dev/null); then
        return 1  # sourced
    else
        exit 1    # executed
    fi
fi

# Sanity: vault data dir actually exists. Guards against a stale active-vault
# pointer or a vault.yml whose vault_path was moved/deleted.
if [[ ! -d "$VAULT_PATH" ]]; then
    echo "[wikiforge] ERROR: vault '${VAULT_NAME:-?}' resolved to $VAULT_PATH but the directory doesn't exist." >&2
    echo "[wikiforge] Fix the vault_path in vaults/${VAULT_NAME}/vault.yml, or recreate the data dir." >&2
    unset _RV_SCRIPT_DIR _RV_REPO_DIR
    if (return 0 2>/dev/null); then
        return 1
    else
        exit 1
    fi
fi

echo "[wikiforge] Using vault: ${VAULT_NAME:-?} ($VAULT_PATH)"

unset _RV_SCRIPT_DIR _RV_REPO_DIR
