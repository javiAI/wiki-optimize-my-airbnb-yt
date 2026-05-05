#!/usr/bin/env bash
# resolve-vault.sh — preamble for every vault-touching skill (/query, /ingest,
# /audit, /qa, /ingest-queue, ...).
#
# Behavior:
#   - Resolves $VAULT_PATH and $VAULT_NAME via config.sh (which already handles
#     all the resolution rules: explicit env, .claude/state/active-vault, single
#     bundle, or loud-error on 2+ bundle ambiguity).
#   - On success: prints `[wikiforge] Using vault: <name> (<path>)` to stdout
#     so the user sees which vault is about to be touched BEFORE any operation.
#   - On failure: exits non-zero. The user-facing error already came from
#     config.sh (it lists available vaults and how to disambiguate).
#
# Usage from a skill:
#   bash .claude/scripts/resolve-vault.sh || exit 1
#
# Or sourced (so the calling shell inherits VAULT_PATH/VAULT_NAME):
#   source .claude/scripts/resolve-vault.sh || return 1
#
# Why this exists: skills are markdown instructions read by Claude. Without an
# explicit, loud preamble it's easy for the LLM to silently pick the wrong
# vault when 2+ exist. This script makes the choice visible and refuses to
# proceed when ambiguous.

set -euo pipefail

_RV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_RV_REPO_DIR="$(cd "$_RV_SCRIPT_DIR/.." && pwd)"

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
