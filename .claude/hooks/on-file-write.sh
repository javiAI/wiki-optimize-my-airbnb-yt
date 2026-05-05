#!/bin/bash
# on-file-write.sh — PostToolUse(Write|Edit) hook
# Reads JSON from stdin: .tool_input.file_path
# Triggers atom pipeline on wiki/ writes; queues raw/ writes for atom creation.

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

[[ -z "$FILE" ]] && exit 0

# Resolve VAULT_PATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 1. Prefer deriving from the FILE path itself: {VAULT_PATH}/{wiki|raw}/...
if [[ "$FILE" == */wiki/*/*.md ]]; then
    VAULT_PATH="${FILE%/wiki/*}"
elif [[ "$FILE" == */raw/* ]]; then
    VAULT_PATH="${FILE%/raw/*}"
fi

# 2. Fallback to .claude/scripts/config.sh (resolves via VAULT_NAME or single bundle).
# Quiet mode: this hook fires on ANY Write/Edit, including ones unrelated to a
# vault. We don't want a loud ambiguity error every time the user edits source
# code in a 2+ vault repo. Skills that operate on a vault surface the error.
if [[ -z "${VAULT_PATH:-}" ]]; then
    # shellcheck disable=SC1091
    WIKIFORGE_CONFIG_QUIET=1 source "$REPO_DIR/.claude/scripts/config.sh" 2>/dev/null || true
fi

if [[ -z "${VAULT_PATH:-}" ]]; then
    echo "[hook] WARN: VAULT_PATH not set — skipping on-file-write" >&2
    exit 0
fi

# Per-vault state dir lives in the vault's bundle: vaults/{name}/state/.
# Vault data dir is data-only.
VAULT_NAME_BASENAME="$(basename "$VAULT_PATH")"
STATE_DIR="$REPO_DIR/vaults/$VAULT_NAME_BASENAME/state"

# ── raw/ write → queue for atom creation ────────────────────────────────────
if [[ "$FILE" == */raw/* && "$FILE" == *.md ]]; then
    QUEUE="$STATE_DIR/queue/pending-atoms.txt"
    mkdir -p "$(dirname "$QUEUE")"
    touch "$QUEUE"
    echo "$FILE" >> "$QUEUE"
    echo "[hook] Queued for atom creation: $(basename "$FILE")"
    exit 0
fi

# ── wiki/{lang}/*.md write → auto-link + qa + optional translate ─────────────
if [[ "$FILE" == */wiki/*/*.md ]]; then
    STEM=$(basename "$FILE" .md)
    # Extract lang safely: path must be .../wiki/{lang}/{stem}.md
    LANG=$(echo "$FILE" | sed -n 's|.*/wiki/\([^/][^/]*\)/[^/]*\.md$|\1|p')

    if [[ -z "$LANG" ]]; then
        echo "[hook] WARN: could not extract lang from path: $FILE" >&2
        exit 0
    fi

    echo "[hook] Atom written: $STEM [$LANG]"

    cd "$REPO_DIR"
    export VAULT_NAME="$VAULT_NAME_BASENAME"
    python3 .claude/scripts/auto-link.py "$STEM" --lang "$LANG" --vault "$VAULT_PATH" 2>&1 || \
        echo "[hook] WARN: auto-link failed for $STEM [$LANG]" >&2
    python3 .claude/scripts/atom-qa.py "$STEM" --lang "$LANG" --vault "$VAULT_PATH" 2>&1 || \
        echo "[hook] WARN: atom-qa failed for $STEM [$LANG]" >&2

    # Single-pass config read: auto_refine, auto_propagate, atomization_lang, enabled.
    # Replaces 4 separate `python3 -c` invocations.
    AUTO_REFINE=false
    AUTO_PROPAGATE=false
    ATOMIZATION_LANG="$LANG"
    ENABLED=""
    while IFS='=' read -r KEY VAL; do
        case "$KEY" in
            auto_refine) AUTO_REFINE="$VAL" ;;
            auto_propagate) AUTO_PROPAGATE="$VAL" ;;
            atomization_lang) ATOMIZATION_LANG="$VAL" ;;
            enabled) ENABLED="$VAL" ;;
        esac
    done < <(FILE="$FILE" LANG="$LANG" python3 .claude/scripts/hook_propagate.py 2>/dev/null || true)

    if [[ "$AUTO_REFINE" == "true" ]]; then
        bash "$SCRIPT_DIR/on-atom-refine.sh" "$STEM" "$LANG" "$VAULT_PATH" &
    fi

    if [[ "$AUTO_PROPAGATE" == "true" ]]; then
        if [[ "$LANG" == "$ATOMIZATION_LANG" ]]; then
            LOG="$STATE_DIR/logs/propagate.log"
            LOCK_DIR="$STATE_DIR/logs/propagate-locks"
            mkdir -p "$(dirname "$LOG")" "$LOCK_DIR"

            for TLANG in $ENABLED; do
                [[ "$TLANG" == "$LANG" ]] && continue
                LOCK="$LOCK_DIR/${STEM}.${TLANG}.lock"
                TARGET="$VAULT_PATH/wiki/$TLANG/$STEM.md"

                if [[ -f "$TARGET" ]]; then
                    continue
                fi
                if [[ -f "$LOCK" ]]; then
                    echo "[hook] Propagation already running: $STEM → $TLANG"
                    continue
                fi

                touch "$LOCK"
                echo "[hook] Triggering propagation: $STEM → $TLANG"
                (
                    python3 .claude/scripts/propagate_atom.py "$STEM" \
                        --from "$LANG" --to "$TLANG" \
                        >> "$LOG" 2>&1 || true
                    rm -f "$LOCK"
                ) &
            done
        fi
    fi
    exit 0
fi

exit 0
