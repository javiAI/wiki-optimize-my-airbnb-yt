#!/bin/bash
# on-atom-refine.sh — Second-pass atom refinement hook
#
# Triggered by on-file-write.sh when pipeline.auto_refine: true in vault.yml.
# Runs a focused claude -p pass on a newly created atom to:
#   1. Remove compound claims (split if needed)
#   2. Ensure body is query-optimized (answers the claim directly, no filler)
#   3. Compress verbose explanations to dense factual prose
#   4. Verify YAML frontmatter is complete
#
# Called as: bash on-atom-refine.sh {stem} {lang} {vault_path}
# Not wired into settings.json directly — called from on-file-write.sh.

set -euo pipefail

STEM="${1:-}"
LANG="${2:-}"
VAULT_PATH="${3:-}"

if [[ -z "$STEM" || -z "$LANG" || -z "$VAULT_PATH" ]]; then
    echo "[refine] Usage: on-atom-refine.sh {stem} {lang} {vault_path}" >&2
    exit 1
fi

ATOM_FILE="$VAULT_PATH/wiki/$LANG/$STEM.md"
if [[ ! -f "$ATOM_FILE" ]]; then
    echo "[refine] WARN: atom not found: $ATOM_FILE" >&2
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="$REPO_DIR/vaults/$(basename "$VAULT_PATH")/state"
LOG="$STATE_DIR/logs/refine.log"
LOCK="$STATE_DIR/logs/refine-locks/${STEM}.${LANG}.lock"
mkdir -p "$(dirname "$LOG")" "$(dirname "$LOCK")"

if [[ -f "$LOCK" ]]; then
    echo "[refine] Already running for $STEM [$LANG]"
    exit 0
fi

touch "$LOCK"
echo "[refine] Starting second-pass refinement: $STEM [$LANG]"

# Determine whether this atom is the canonical (atomization_lang) for its source.
# If so, after refining we re-propagate (--force) so all enabled langs re-derive
# from the refined canonical. If not, we skip re-propagation — propagated atoms
# never become a propagation source.
IS_CANONICAL=$(python3 -c "
import sys, re
sys.path.insert(0, '$REPO_DIR/.claude/scripts')
from pathlib import Path
from config import VaultConfig
cfg = VaultConfig()
atom = Path('$VAULT_PATH/wiki/$LANG/$STEM.md')
if not atom.exists():
    print('false'); sys.exit()
text = atom.read_text(encoding='utf-8', errors='replace')
# A propagated atom carries propagated_from; canonical does not.
if re.search(r'^propagated_from:', text, re.MULTILINE):
    print('false'); sys.exit()
print('true')
" 2>/dev/null || echo "false")

(
    cd "$REPO_DIR"

    claude -p "Refine the atom at wiki/$LANG/$STEM.md in vault $VAULT_PATH.

Rules:
1. The claim must be ONE falsifiable sentence — no compound claims with 'and/y'. If compound, rewrite as the single most important claim.
2. Body must be dense and query-optimized: opens with the direct answer, then supporting detail. No intro fluff, no trailing summaries.
3. Remove sentences that repeat the claim verbatim.
4. Ensure YAML has: lang, claim, topics, confidence, sources (with url if computable), conflicts_with, last_verified.
5. Do NOT change source_id, locator, url, or excerpt fields.
6. Language: body must be entirely in $LANG — zero mixing.

Write the refined version back to the same file. If already optimal, make no changes." \
        --max-turns 2 \
        >> "$LOG" 2>&1

    REFINE_RC=$?
    rm -f "$LOCK"
    echo "[refine] Done: $STEM [$LANG] (rc=$REFINE_RC)" >> "$LOG"

    # Re-propagate canonical → all other enabled langs (--force overwrites the
    # stale propagated atoms with re-derivations from the refined canonical).
    # Guarantees per-lang equivalence after any canonical edit.
    if [[ "$REFINE_RC" -eq 0 && "$IS_CANONICAL" == "true" ]]; then
        ENABLED=$(VAULT_NAME="$(basename "$VAULT_PATH")" python3 -c "
import sys; sys.path.insert(0,'.claude/scripts')
from config import VaultConfig
print(' '.join(VaultConfig().enabled_languages))
" 2>/dev/null || echo "")
        for TLANG in $ENABLED; do
            [[ "$TLANG" == "$LANG" ]] && continue
            echo "[refine] Re-propagating refined canonical: $STEM $LANG → $TLANG" >> "$LOG"
            VAULT_NAME="$(basename "$VAULT_PATH")" python3 .claude/scripts/propagate_atom.py "$STEM" \
                --from "$LANG" --to "$TLANG" --force \
                >> "$LOG" 2>&1 || \
                echo "[refine] WARN: re-propagate failed: $STEM → $TLANG" >> "$LOG"
        done
    fi
) &

exit 0
