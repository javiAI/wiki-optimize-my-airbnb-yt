#!/bin/bash
# on-session-start.sh — SessionStart hook
# Notifies user if pending-atoms queue is non-empty, showing first filenames.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Bash 3.2 portability check — fail loud if forbidden idioms slip into shell
# scripts (we've regressed on `declare -A` once already).
LINTER="$REPO_DIR/.claude/scripts/lint-bash-portability.sh"
if [[ -x "$LINTER" ]]; then
    if ! LINT_OUT=$(bash "$LINTER" 2>&1); then
        echo "[WikiForge] bash portability regression detected:"
        echo "$LINT_OUT" | sed 's/^/  /'
    fi
fi

if [[ -z "${VAULT_PATH:-}" ]]; then
    # Quiet mode: SessionStart fires on every Claude Code launch. If the user
    # has 2+ vaults and hasn't picked one yet, we don't want a loud error at
    # startup — they may not be operating on a vault at all this session.
    # Skills that actually touch the vault (/query, /ingest, etc.) re-source
    # config.sh without WIKIFORGE_CONFIG_QUIET and surface the ambiguity then.
    # shellcheck disable=SC1091
    WIKIFORGE_CONFIG_QUIET=1 source "$REPO_DIR/.claude/scripts/config.sh" 2>/dev/null || true
fi

[[ -z "${VAULT_PATH:-}" ]] && exit 0

STATE_DIR="$REPO_DIR/vaults/$(basename "$VAULT_PATH")/state"
QUEUE="$STATE_DIR/queue/pending-atoms.txt"
FALLBACK_QUEUE="$STATE_DIR/queue/llm-fallback.txt"

if [[ -f "$QUEUE" && -s "$QUEUE" ]]; then
    # Count only lines that still point to existing files
    VALID=0
    PREVIEW=""
    SHOWN=0
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        if [[ -f "$line" ]]; then
            VALID=$((VALID + 1))
            if [[ $SHOWN -lt 3 ]]; then
                PREVIEW="${PREVIEW}  - $(basename "$line")\n"
                SHOWN=$((SHOWN + 1))
            fi
        fi
    done < "$QUEUE"

    if [[ $VALID -gt 0 ]]; then
        echo "[WikiForge] $VALID source(s) pending atom creation. Run /ingest-queue to process."
        echo -e "$PREVIEW" | head -4
        [[ $VALID -gt 3 ]] && echo "  ... and $((VALID - 3)) more"
    fi
fi

if [[ -f "$FALLBACK_QUEUE" && -s "$FALLBACK_QUEUE" ]]; then
    FB_COUNT=$(grep -c . "$FALLBACK_QUEUE" 2>/dev/null || echo 0)
    if [[ "$FB_COUNT" -gt 0 ]]; then
        echo "[WikiForge] $FB_COUNT source(s) have no transcript in any enabled language; atomization will fall back to LLM synthesis from enabled[0] (excerpt_source: llm_fallback). Quality may be lower."
    fi
fi

exit 0
