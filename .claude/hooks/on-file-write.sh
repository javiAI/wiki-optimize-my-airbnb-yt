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

    # Optional second-pass refinement
    AUTO_REFINE=$(python3 -c "
import sys; sys.path.insert(0,'.claude/scripts')
from config import VaultConfig
c = VaultConfig()
print(str(c.get('pipeline.auto_refine', False)).lower())
" 2>/dev/null || echo "false")

    if [[ "$AUTO_REFINE" == "true" ]]; then
        bash "$SCRIPT_DIR/on-atom-refine.sh" "$STEM" "$LANG" "$VAULT_PATH" &
    fi

    # Auto-propagate canonical atom → other enabled langs (re-atomize at locator
    # using target-lang transcript). Reads pipeline.auto_propagate (new) with
    # legacy fallback to pipeline.auto_translate.
    AUTO_PROPAGATE=$(python3 -c "
import sys; sys.path.insert(0,'.claude/scripts')
from config import VaultConfig
c = VaultConfig()
v = c.get('pipeline.auto_propagate')
if v is None:
    v = c.get('pipeline.auto_translate', False)
print(str(v).lower())
" 2>/dev/null || echo "false")

    if [[ "$AUTO_PROPAGATE" == "true" ]]; then
        # Determine atomization_lang for this atom from its source (raw frontmatter
        # via video_id lookup). Fallback: assume the lang of the file just written
        # IS the atomization_lang.
        ATOMIZATION_LANG=$(FILE="$FILE" LANG="$LANG" python3 -c "
import sys, os
sys.path.insert(0,'.claude/scripts')
from pathlib import Path
import re
from config import VaultConfig
cfg = VaultConfig()
atom = Path(os.environ['FILE'])
text = atom.read_text(encoding='utf-8', errors='replace')
m = re.search(r'^\s*-\s*source_id:\s*(\S+)', text, re.MULTILINE)
if not m:
    print(os.environ['LANG'])
    sys.exit()
sid = m.group(1)
# Try to find this video in raw/{any-lang}/ to read native_lang
found = None
for lang_dir in (cfg.vault_path / 'raw').iterdir() if (cfg.vault_path / 'raw').exists() else []:
    if not lang_dir.is_dir():
        continue
    for raw in lang_dir.glob('*.md'):
        rt = raw.read_text(encoding='utf-8', errors='replace')
        if re.search(rf'^video_id:\s*{re.escape(sid)}\s*$', rt, re.MULTILINE):
            n = re.search(r'^native_lang:\s*(\S+)', rt, re.MULTILINE)
            if n:
                found = n.group(1).strip()
                break
    if found: break
if found:
    print(cfg.atomization_lang_for(found))
else:
    print(os.environ['LANG'])
" 2>/dev/null || echo "$LANG")

        if [[ "$LANG" == "$ATOMIZATION_LANG" ]]; then
            LOG="$STATE_DIR/logs/propagate.log"
            LOCK_DIR="$STATE_DIR/logs/propagate-locks"
            mkdir -p "$(dirname "$LOG")" "$LOCK_DIR"

            ENABLED=$(python3 -c "
import sys; sys.path.insert(0,'.claude/scripts')
from config import VaultConfig
print(' '.join(VaultConfig().enabled_languages))
" 2>/dev/null || echo "")

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
