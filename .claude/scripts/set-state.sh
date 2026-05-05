#!/bin/bash
# set-state.sh — Simple state.yaml writer
# Usage: set-state.sh active_lang es
# OR:    set-state.sh active_vault oma-test-1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_YAML="$REPO_DIR/.claude/state/state.yaml"

KEY="${1:-}"
VALUE="${2:-}"

if [[ -z "$KEY" || -z "$VALUE" ]]; then
    echo "Usage: set-state.sh <key> <value>"
    echo "Example: set-state.sh active_lang es"
    exit 1
fi

mkdir -p "$(dirname "$STATE_YAML")"

# Read current state or start empty
if [[ -f "$STATE_YAML" ]]; then
    current=$(cat "$STATE_YAML")
else
    current="# WikiForge repo state
# Holds cross-cutting selections (vault, lang) shared by scripts and the LLM."
fi

# Update or add the key
temp=$(mktemp)
if [[ -f "$STATE_YAML" ]]; then
    grep -v "^${KEY}:" "$STATE_YAML" >> "$temp" || true
fi
echo "${KEY}: ${VALUE}" >> "$temp"
mv "$temp" "$STATE_YAML"
