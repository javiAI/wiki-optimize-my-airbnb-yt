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

if [[ -z "${VAULT_PATH:-}" ]]; then
    CONFIG_SH="$REPO_DIR/scripts/config.sh"
    if [[ -f "$CONFIG_SH" ]]; then
        VAULT_PATH=$(grep 'VAULT_PATH=' "$CONFIG_SH" | head -1 | cut -d= -f2- | tr -d '"' | sed "s|\$HOME|$HOME|g" | sed "s|~|$HOME|g")
    fi
fi

if [[ -z "${VAULT_PATH:-}" ]]; then
    echo "[hook] WARN: VAULT_PATH not set — skipping on-file-write" >&2
    exit 0
fi

# ── raw/ write → queue for atom creation ────────────────────────────────────
if [[ "$FILE" == */raw/* && "$FILE" == *.md ]]; then
    QUEUE="$VAULT_PATH/.claude/queue/pending-atoms.txt"
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
    python3 scripts/auto-link.py "$STEM" --lang "$LANG" --vault "$VAULT_PATH" 2>&1 || \
        echo "[hook] WARN: auto-link failed for $STEM [$LANG]" >&2
    python3 scripts/atom-qa.py "$STEM" --lang "$LANG" --vault "$VAULT_PATH" 2>&1 || \
        echo "[hook] WARN: atom-qa failed for $STEM [$LANG]" >&2

    # Optional second-pass refinement
    AUTO_REFINE=$(python3 -c "
import sys; sys.path.insert(0,'scripts')
from config import VaultConfig
c = VaultConfig('$VAULT_PATH')
print(str(c.get('pipeline.auto_refine', False)).lower())
" 2>/dev/null || echo "false")

    if [[ "$AUTO_REFINE" == "true" ]]; then
        bash "$SCRIPT_DIR/on-atom-refine.sh" "$STEM" "$LANG" "$VAULT_PATH" &
    fi

    # Auto-translate primary → secondary if enabled
    AUTO_TRANSLATE=$(python3 -c "
import sys; sys.path.insert(0,'scripts')
from config import VaultConfig
c = VaultConfig('$VAULT_PATH')
print(str(c.get('pipeline.auto_translate', False)).lower())
" 2>/dev/null || echo "false")

    SOURCE_LANG=$(python3 -c "
import sys; sys.path.insert(0,'scripts')
from config import VaultConfig
c = VaultConfig('$VAULT_PATH')
print(c.get('source.original_language', c.primary_language))
" 2>/dev/null || echo "")

    if [[ "$LANG" == "$SOURCE_LANG" && "$AUTO_TRANSLATE" == "true" ]]; then
        LOG="$VAULT_PATH/.claude/logs/translate.log"
        LOCK_DIR="$VAULT_PATH/.claude/logs/translate-locks"
        mkdir -p "$(dirname "$LOG")" "$LOCK_DIR"

        SECONDARY_LANGS=$(python3 -c "
import sys; sys.path.insert(0,'scripts')
from config import VaultConfig
c = VaultConfig('$VAULT_PATH')
print(' '.join(c.secondary_languages))
" 2>/dev/null || echo "")

        for SLANG in $SECONDARY_LANGS; do
            LOCK="$LOCK_DIR/${STEM}.${SLANG}.lock"
            TARGET="$VAULT_PATH/wiki/$SLANG/$STEM.md"

            # Skip if already exists or translation already running
            if [[ -f "$TARGET" ]]; then
                continue
            fi
            if [[ -f "$LOCK" ]]; then
                echo "[hook] Translation already running: $STEM → $SLANG"
                continue
            fi

            touch "$LOCK"
            echo "[hook] Triggering translation: $STEM → $SLANG"
            (
                claude -p "You are translating a vault atom. Read wiki/$SOURCE_LANG/$STEM.md from $VAULT_PATH. Create wiki/$SLANG/$STEM.md: same frontmatter structure (lang: $SLANG, same source_id/locator/url), body written naturally in $SLANG by a fluent bilingual — not a translation, a native rewrite. Apply anglicism table from vault's agents.md." \
                    --max-turns 3 \
                    >> "$LOG" 2>&1
                rm -f "$LOCK"
            ) &
        done
    fi
    exit 0
fi

exit 0
