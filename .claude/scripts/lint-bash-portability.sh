#!/bin/bash
# lint-bash-portability.sh — scan .claude/scripts/*.sh and .claude/hooks/*.sh
# for bash-4+ idioms that fail silently on macOS bash 3.2.
#
# We've been bitten by `declare -A` (bash 3.2 parses it as `declare -a` and
# silently turns associative-array writes into noops, breaking ingest.sh into
# returning NO_SUBS for every video). This script catches that class of bug
# before it ships.
#
# Usage: bash .claude/scripts/lint-bash-portability.sh
# Exit codes: 0 = clean, 1 = forbidden idioms found.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

TARGETS=(
    "$REPO_DIR/.claude/scripts"
    "$REPO_DIR/.claude/hooks"
)

# Pattern → human-readable reason
PATTERNS=(
    'declare -A|associative arrays — bash 3.2 silently ignores -A and creates an indexed array'
    '\bmapfile\b|mapfile is bash 4+; use a while-read loop instead'
    '\breadarray\b|readarray is bash 4+; use a while-read loop instead'
    '\$\{[a-zA-Z_][a-zA-Z0-9_]*,,\}|lowercase param expansion ${var,,} is bash 4+'
    '\$\{[a-zA-Z_][a-zA-Z0-9_]*\^\^\}|uppercase param expansion ${var^^} is bash 4+'
)

violations=0

SELF="$(basename "${BASH_SOURCE[0]}")"

for dir in "${TARGETS[@]}"; do
    [[ -d "$dir" ]] || continue
    while IFS= read -r -d '' file; do
        # Skip self — pattern strings inside this file are not real usages.
        [[ "$(basename "$file")" == "$SELF" ]] && continue
        for entry in "${PATTERNS[@]}"; do
            pattern="${entry%%|*}"
            reason="${entry#*|}"
            # Strip comment-only lines before grepping (comments mentioning the
            # forbidden idiom are fine — e.g. "avoid declare -A").
            matches=$(grep -nE "$pattern" "$file" 2>/dev/null | grep -vE '^\s*[0-9]+:\s*#' || true)
            if [[ -n "$matches" ]]; then
                while IFS= read -r m; do
                    [[ -z "$m" ]] && continue
                    rel="${file#$REPO_DIR/}"
                    echo "FAIL  $rel:${m%%:*}: $reason"
                    violations=$((violations + 1))
                done <<< "$matches"
            fi
        done
    done < <(find "$dir" -maxdepth 1 -type f -name "*.sh" -print0)
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "$violations bash-portability violation(s). macOS ships bash 3.2; these scripts must run there."
    exit 1
fi

echo "OK  bash 3.2 portability clean."
exit 0
