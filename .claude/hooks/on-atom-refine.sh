#!/bin/bash
# on-atom-refine.sh — Second-pass atom refinement hook
#
# Triggered by on-file-write.sh when pipeline.auto_refine: true in vault.yaml.
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

LOG="$VAULT_PATH/.claude/logs/refine.log"
LOCK="$VAULT_PATH/.claude/logs/refine-locks/${STEM}.${LANG}.lock"
mkdir -p "$(dirname "$LOG")" "$(dirname "$LOCK")"

if [[ -f "$LOCK" ]]; then
    echo "[refine] Already running for $STEM [$LANG]"
    exit 0
fi

touch "$LOCK"
echo "[refine] Starting second-pass refinement: $STEM [$LANG]"

(
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
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

    rm -f "$LOCK"
    echo "[refine] Done: $STEM [$LANG]" >> "$LOG"
) &

exit 0
