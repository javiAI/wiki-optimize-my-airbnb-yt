# config.sh — bash-side vault path resolution
#
# Resolves VAULT_PATH (and VAULT_NAME) for any caller that operates on a vault.
# Source this from scripts that need $VAULT_PATH in shell context.
#
# Resolution order (first match wins):
#   1. $VAULT_PATH already exported → use as-is (caller knows best)
#   2. $VAULT_NAME exported         → vaults/{name}/vault.yml → vault_path field
#   3. .claude/state/active-vault   → name written by last successful operation
#   4. Single vaults/* bundle       → auto-select (zero ambiguity)
#   5. 2+ bundles, no signal        → AMBIGUOUS: print loud error, leave unset
#
# Why loud-error instead of silent pick: when 2+ vaults exist, picking one
# arbitrarily means a /query or /ingest may operate on the wrong vault — the
# failure mode that motivated this guard. Every caller already does
# `${VAULT_PATH:?...}` so leaving it unset is safe; the loud message gives the
# user the exact one-liner to fix it.
#
# Quiet mode: export WIKIFORGE_CONFIG_QUIET=1 before sourcing to suppress the
# ambiguity message (used by SessionStart hook — noise at startup is bad UX).

# config.sh lives at .claude/scripts/ — repo root is two levels up
_CFG_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_CFG_VAULTS_DIR="${_CFG_REPO_DIR}/vaults"
_CFG_CONFIG_YAML="${_CFG_REPO_DIR}/.claude/config/config.yaml"
_CFG_STATE_YAML="${_CFG_REPO_DIR}/.claude/state/state.yaml"  # legacy fallback
_CFG_STATE_FILE="${_CFG_REPO_DIR}/.claude/state/active-vault"  # legacy fallback

_read_state_field() {
    # Extract a flat top-level field from a config file. Format is intentionally
    # minimal: `key: value` lines, no nesting. Returns empty string if missing.
    local field="$1"
    local config_file="$2"
    [[ -f "$config_file" ]] || return 0
    grep -E "^${field}:" "$config_file" | head -1 \
        | sed -E "s/^${field}:[[:space:]]*\"?([^\"#]+)\"?.*$/\\1/" \
        | tr -d '[:space:]'
}

_resolve_vault_path_from_yml() {
    local yml="$1"
    [[ -f "$yml" ]] || return 1
    # Default $HOME so this still works under `set -u` when HOME is unset
    # (e.g. invoked via `env -i bash`); the substitution becomes a no-op then.
    local h="${HOME:-}"
    grep -E '^vault_path:' "$yml" | head -1 \
        | sed -E 's/^vault_path:[[:space:]]*"?([^"]+)"?.*$/\1/' \
        | sed "s|\$HOME|$h|g" \
        | sed "s|^~|$h|"
}

# Track whether VAULT_NAME was explicitly set but unresolvable. When that
# happens we want to STOP — falling through to active-vault or single-bundle
# would silently route to a different vault than the user named.
_CFG_VAULT_NAME_BAD=0

# 1. $VAULT_PATH already set → nothing to do.
# 2. $VAULT_NAME → resolve via vault.yml.
if [[ -z "${VAULT_PATH:-}" && -n "${VAULT_NAME:-}" ]]; then
    _CFG_VP=$(_resolve_vault_path_from_yml "${_CFG_VAULTS_DIR}/${VAULT_NAME}/vault.yml" || true)
    if [[ -n "${_CFG_VP:-}" ]]; then
        export VAULT_PATH="$_CFG_VP"
    else
        # VAULT_NAME was set but the bundle doesn't exist — loud error, no
        # fallback: caller asked for a specific vault and got it wrong.
        _CFG_VAULT_NAME_BAD=1
        if [[ -z "${WIKIFORGE_CONFIG_QUIET:-}" ]]; then
            echo "[wikiforge] ERROR: VAULT_NAME=$VAULT_NAME but vaults/$VAULT_NAME/vault.yml does not exist." >&2
            if [[ -d "$_CFG_VAULTS_DIR" ]]; then
                echo "[wikiforge] Available vaults:" >&2
                for d in "$_CFG_VAULTS_DIR"/*/; do
                    [[ -f "${d}vault.yml" ]] && echo "  - $(basename "${d%/}")" >&2
                done
            fi
        fi
    fi
fi

# 3. config.yaml.active_vault → last operated vault.
if [[ -z "${VAULT_PATH:-}" && "$_CFG_VAULT_NAME_BAD" -eq 0 ]]; then
    _CFG_ACTIVE=""
    if [[ -f "$_CFG_CONFIG_YAML" ]]; then
        _CFG_ACTIVE=$(_read_state_field "active_vault" "$_CFG_CONFIG_YAML")
    fi
    if [[ -n "$_CFG_ACTIVE" && -f "${_CFG_VAULTS_DIR}/${_CFG_ACTIVE}/vault.yml" ]]; then
        _CFG_VP=$(_resolve_vault_path_from_yml "${_CFG_VAULTS_DIR}/${_CFG_ACTIVE}/vault.yml" || true)
        if [[ -n "${_CFG_VP:-}" ]]; then
            export VAULT_PATH="$_CFG_VP"
            export VAULT_NAME="$_CFG_ACTIVE"
        fi
    fi
    unset _CFG_ACTIVE
fi

# 4-5. Bundle-count fallback.
if [[ -z "${VAULT_PATH:-}" && "$_CFG_VAULT_NAME_BAD" -eq 0 ]]; then
    _CFG_BUNDLES=()
    if [[ -d "$_CFG_VAULTS_DIR" ]]; then
        for d in "$_CFG_VAULTS_DIR"/*/; do
            [[ -f "${d}vault.yml" ]] && _CFG_BUNDLES+=("${d%/}")
        done
    fi
    if [[ "${#_CFG_BUNDLES[@]}" -eq 1 ]]; then
        # Single bundle → safe to auto-select.
        _CFG_VP=$(_resolve_vault_path_from_yml "${_CFG_BUNDLES[0]}/vault.yml" || true)
        [[ -n "${_CFG_VP:-}" ]] && export VAULT_PATH="$_CFG_VP"
        [[ -z "${VAULT_NAME:-}" ]] && export VAULT_NAME=$(basename "${_CFG_BUNDLES[0]}")
    elif [[ "${#_CFG_BUNDLES[@]}" -gt 1 ]]; then
        # Ambiguous → refuse to pick. Print the bundle list and exit hint.
        if [[ -z "${WIKIFORGE_CONFIG_QUIET:-}" ]]; then
            {
                echo "[wikiforge] ERROR: vault is ambiguous — ${#_CFG_BUNDLES[@]} bundles exist and none is selected."
                echo "[wikiforge] Available vaults:"
                for d in "${_CFG_BUNDLES[@]}"; do
                    echo "  - $(basename "$d")"
                done
                echo "[wikiforge] Pick one with:  export VAULT_NAME=<name>"
                echo "[wikiforge] Or set the active default:  bash .claude/scripts/set-config.sh active_vault <name>"
            } >&2
        fi
    fi
    unset _CFG_BUNDLES
fi

unset _CFG_REPO_DIR _CFG_VAULTS_DIR _CFG_CONFIG_YAML _CFG_STATE_YAML _CFG_STATE_FILE _CFG_VP _CFG_VAULT_NAME_BAD
unset -f _resolve_vault_path_from_yml _read_state_field
