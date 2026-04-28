#!/bin/bash
# on-file-write.sh — PostToolUse(Write|Edit) hook
# Reads JSON from stdin: .tool_input.file_path
# Triggers: atom pipeline (auto-link + qa + translate) on wiki/ writes,
#            queue pending-atoms.txt on raw/ writes

set -euo pipefail

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

[[ -z "$FILE" ]] && exit 0

# Resolve vault dir — prefer env var, fall back to config.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${VAULT_PATH:-}" ]]; then
    CONFIG_SH="$REPO_DIR/scripts/config.sh"
    if [[ -f "$CONFIG_SH" ]]; then
        VAULT_PATH=$(grep 'VAULT_PATH=' "$CONFIG_SH" | head -1 | cut -d= -f2- | tr -d '"' | sed "s|\$HOME|$HOME|g")
    fi
fi

[[ -z "${VAULT_PATH:-}" ]] && { echo "[hook] VAULT_PATH not set — skipping"; exit 0; }

# ── raw/ write → queue for atom creation ────────────────────────────────────
if [[ "$FILE" == */raw/* ]]; then
    QUEUE="$VAULT_PATH/.claude/queue/pending-atoms.txt"
    mkdir -p "$(dirname "$QUEUE")"
    echo "$FILE" >> "$QUEUE"
    echo "[hook] Queued for atom creation: $(basename "$FILE")"
    exit 0
fi

# ── wiki/{lang}/*.md write → auto-link + qa + optional translate ─────────────
if [[ "$FILE" == */wiki/*/*.md ]]; then
    STEM=$(basename "$FILE" .md)
    LANG=$(echo "$FILE" | sed 's|.*wiki/\([^/]*\)/.*|\1|')

    echo "[hook] Atom written: $STEM [$LANG]"

    cd "$REPO_DIR"
    python3 scripts/auto-link.py "$STEM" --lang "$LANG" --vault "$VAULT_PATH" 2>&1 || true
    python3 scripts/atom-qa.py "$STEM" --lang "$LANG" --vault "$VAULT_PATH" 2>&1 || true

    # Auto-translate primary → secondary if enabled
    PRIMARY_LANG=$(python3 scripts/config.py 2>/dev/null | grep 'primary:' | head -1 | awk '{print $2}' || echo "en")
    AUTO_TRANSLATE=$(python3 -c "
import sys; sys.path.insert(0,'scripts')
from config import VaultConfig
c = VaultConfig('$VAULT_PATH')
print(str(c.get('pipeline.auto_translate', False)).lower())
" 2>/dev/null || echo "false")

    if [[ "$LANG" == "$PRIMARY_LANG" && "$AUTO_TRANSLATE" == "true" ]]; then
        LOG="$VAULT_PATH/.claude/logs/translate.log"
        mkdir -p "$(dirname "$LOG")"
        SECONDARY_LANGS=$(python3 -c "
import sys; sys.path.insert(0,'scripts')
from config import VaultConfig
c = VaultConfig('$VAULT_PATH')
print(' '.join(c.secondary_languages))
" 2>/dev/null || echo "")
        for SLANG in $SECONDARY_LANGS; do
            if [[ ! -f "$VAULT_PATH/wiki/$SLANG/$STEM.md" ]]; then
                echo "[hook] Triggering translation: $STEM → $SLANG"
                claude -p "Translate wiki/$LANG/$STEM.md to wiki/$SLANG/$STEM.md. Follow the atom schema in CLAUDE.md: monolingual $SLANG body, same source_id/locator/url, no anglicisms. Write the file directly." \
                    --max-turns 3 \
                    >> "$LOG" 2>&1 &
            fi
        done
    fi
    exit 0
fi

exit 0
