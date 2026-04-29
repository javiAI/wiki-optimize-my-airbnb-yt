#!/bin/bash
# init-vault.sh — WikiForge vault setup (non-interactive, terminal use)
#
# This script is the TERMINAL fallback. For the guided Claude-integrated flow, use:
#   /init-vault  (skill inside a Claude session)
#
# Usage:
#   scripts/init-vault.sh                    # interactive terminal wizard
#   scripts/init-vault.sh --name my-vault    # partial non-interactive
#
# What it does:
#   1. Asks vault name, data path, output languages, sources, pipeline options
#   2. Writes configs/{name}.yaml to this repo
#   3. Creates vault directory structure at the specified data path
#   4. Optionally runs batch-ingest.sh if sources were provided

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CONFIGS_DIR="$REPO_DIR/configs"

# ── Helpers ──────────────────────────────────────────────────────────────────

ask() {
    local prompt="$1"
    local default="${2:-}"
    local answer
    if [[ -n "$default" ]]; then
        read -r -p "$prompt [$default]: " answer
        echo "${answer:-$default}"
    else
        read -r -p "$prompt: " answer
        echo "$answer"
    fi
}

confirm() {
    local prompt="$1"
    local default="${2:-y}"
    local answer
    read -r -p "$prompt [${default}]: " answer
    answer="${answer:-$default}"
    [[ "$(echo "$answer" | tr '[:upper:]' '[:lower:]')" == "y" ]]
}

# ── Interactive wizard ────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        WikiForge — New Vault Setup       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Vault name
VAULT_NAME=$(ask "Vault name (slug, no spaces)" "my-vault")
VAULT_NAME=$(echo "$VAULT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

CONFIG_FILE="$CONFIGS_DIR/${VAULT_NAME}.yaml"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "  ⚠  Config already exists: $CONFIG_FILE"
    if ! confirm "  Overwrite?" "n"; then
        echo "Aborted — edit $CONFIG_FILE directly if needed."
        exit 0
    fi
fi

# 2. Vault data path (where Obsidian/raw data lives)
VAULT_DATA_PATH=$(ask "Vault data path (where atoms and sources are stored)" "$HOME/Dev/obsidian_vaults/$VAULT_NAME")
VAULT_DATA_PATH="${VAULT_DATA_PATH/#\~/$HOME}"
VAULT_DATA_PATH="$(realpath -m "$VAULT_DATA_PATH" 2>/dev/null || echo "$VAULT_DATA_PATH")"

# 3. Output languages
echo ""
echo "── Languages ────────────────────────────────────────────────────────────"
echo "Which languages should atoms be written in?"
echo "  Primary language is always auto-detected from source content."
echo "  Examples: en  |  en,es  |  en,es,fr"
read -r -p "  Languages (comma-separated ISO codes) [en]: " LANGS_RAW
LANGS_RAW="${LANGS_RAW:-en}"
PRIMARY_LANG=$(echo "$LANGS_RAW" | cut -d',' -f1 | tr -d ' ' | tr '[:upper:]' '[:lower:]')
ALL_LANGS=$(echo "$LANGS_RAW" | tr ',' '\n' | tr -d ' ' | tr '[:upper:]' '[:lower:]' | tr '\n' ',' | sed 's/,$//')
EXTRA_LANGS=$(echo "$LANGS_RAW" | tr ',' '\n' | tr -d ' ' | tr '[:upper:]' '[:lower:]' | grep -v "^${PRIMARY_LANG}$" | tr '\n' ',' | sed 's/,$//')
AUTO_TRANSLATE="false"
[[ -n "$EXTRA_LANGS" ]] && AUTO_TRANSLATE="true"

# 4. Sources to ingest
echo ""
echo "── Sources ──────────────────────────────────────────────────────────────"
echo "Paste sources to ingest (optional — you can always add more later)."
echo "  Supported formats (one per line, or comma-separated):"
echo "    • YouTube video ID:       Ek8m0ZAhMgA"
echo "    • Full YouTube URL:       https://youtube.com/watch?v=Ek8m0ZAhMgA"
echo "    • YouTube channel URL:    https://www.youtube.com/@ChannelName"
echo "    • Path to a .txt file:    ./oma-videos.txt"
echo "  Leave empty to skip initial ingest."
read -r -p "  > " SOURCES_RAW
SOURCES_INPUT="$(echo "$SOURCES_RAW" | tr -d ' ')"

# 5. Pipeline options
echo ""
echo "── Pipeline ─────────────────────────────────────────────────────────────"
AUTO_ATOMS="false"
AUTO_REFINE="false"
confirm "Auto-create atoms after ingest? (recommended)" "y" && AUTO_ATOMS="true"
confirm "Auto-refine atoms (second quality pass, uses more tokens)?" "n" && AUTO_REFINE="true"

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║              Setup Summary               ║"
echo "╚══════════════════════════════════════════╝"
echo "  Vault name    : $VAULT_NAME"
echo "  Data path     : $VAULT_DATA_PATH"
echo "  Config file   : $CONFIG_FILE"
echo "  Languages     : $ALL_LANGS"
echo "  Auto-translate: $AUTO_TRANSLATE"
echo "  Sources       : ${SOURCES_INPUT:-none (add later)}"
echo "  Auto-atoms    : $AUTO_ATOMS"
echo "  Auto-refine   : $AUTO_REFINE"
echo ""

if ! confirm "Create vault?" "y"; then
    echo "Aborted."
    exit 0
fi

# ── Create folder structure ───────────────────────────────────────────────────
echo ""
echo "=== WikiForge: Creating vault '$VAULT_NAME' ==="
echo "[1/4] Creating vault directory structure..."

IFS=',' read -ra LANG_ARRAY <<< "$ALL_LANGS"
LANG_DIRS=""
for lang in "${LANG_ARRAY[@]}"; do
    lang=$(echo "$lang" | tr -d ' ')
    LANG_DIRS="$LANG_DIRS $VAULT_DATA_PATH/wiki/$lang $VAULT_DATA_PATH/moc/$lang $VAULT_DATA_PATH/index/$lang $VAULT_DATA_PATH/queries/$lang"
done

mkdir -p $VAULT_DATA_PATH/raw $VAULT_DATA_PATH/meta $LANG_DIRS
mkdir -p "$CONFIGS_DIR"

# ── Write configs/{name}.yaml ─────────────────────────────────────────────────
echo "[2/4] Writing $CONFIG_FILE..."

ENABLED_YAML=$(echo "$ALL_LANGS" | tr ',' '\n' | tr -d ' ' | awk '{printf "\"%s\", ", $0}' | sed 's/, $//')
SECONDARY_YAML=""
if [[ -n "$EXTRA_LANGS" ]]; then
    SECONDARY_YAML=$(echo "$EXTRA_LANGS" | tr ',' '\n' | tr -d ' ' | awk '{printf "\"%s\", ", $0}' | sed 's/, $//')
fi

cat > "$CONFIG_FILE" << YAML_EOF
name: "$VAULT_NAME"
vault_path: "$VAULT_DATA_PATH"
version: "1.0"

languages:
  enabled: [$ENABLED_YAML]
  primary: "$PRIMARY_LANG"
  secondary: [${SECONDARY_YAML}]
  detect_from_query: true

topics: []

pipeline:
  auto_atoms: $AUTO_ATOMS
  auto_translate: $AUTO_TRANSLATE
  auto_link: true
  deep_links: true
  qa_on_create: true
  auto_refine: $AUTO_REFINE

qa:
  completeness: true
  url_validation: true
  anglicism_check: [${SECONDARY_YAML}]
  conflict_check: true
YAML_EOF

# ── Create meta + index stubs ─────────────────────────────────────────────────
echo "[3/4] Creating stubs..."

for lang in "${LANG_ARRAY[@]}"; do
    lang=$(echo "$lang" | tr -d ' ')
    cat > "$VAULT_DATA_PATH/index/$lang/index.md" << EOF
# Vault Index — $VAULT_NAME ($lang)

| Topic | Atoms | Summary |
|-------|-------|---------|
| — | — | Run /audit to populate |

→ Read \`moc/$lang/{topic}.md\` for full topic details.
EOF
done

cat > "$VAULT_DATA_PATH/meta/contradictions.md" << 'EOF'
# Contradictions

No contradictions documented yet.

## Format
## [topic--atom-A vs topic--atom-B] YYYY-MM-DD
- **Conflict**: ...
- **Resolution**: primary=atom-A (reason: ...)
- **Criterion**: temporal_supersession | contextual_scope | confidence_tier
EOF

touch "$VAULT_DATA_PATH/meta/backlinks.md" "$VAULT_DATA_PATH/meta/glossary.md"

cat > "$VAULT_DATA_PATH/agents.md" << EOF
# agents.md — Vault Reference Schema

Vault: $VAULT_NAME | Languages: $ALL_LANGS

## Atom YAML Schema

\`\`\`yaml
lang: $PRIMARY_LANG
claim: "Single falsifiable sentence."
topics: [topic-id]
confidence: high | medium | low
source_lang: $PRIMARY_LANG
sources:
  - source_id: ID
    locator: "HH:MM-HH:MM"
    url: "https://youtube.com/watch?v=ID&t=N"
    excerpt: "Direct quote."
conflicts_with: []
last_verified: YYYY-MM-DD
\`\`\`

## Structure
wiki/{lang}/ — atoms | moc/{lang}/ — maps of content | index/{lang}/ — tier-0 nav
raw/         — immutable source files | meta/ — contradictions, backlinks, glossary
EOF

# ── Git init ──────────────────────────────────────────────────────────────────
if [[ ! -d "$VAULT_DATA_PATH/.git" ]]; then
    git -C "$VAULT_DATA_PATH" init -q
    cat > "$VAULT_DATA_PATH/.gitignore" << 'EOF'
.obsidian/
*.log
.claude/logs/
EOF
    git -C "$VAULT_DATA_PATH" add .
    git -C "$VAULT_DATA_PATH" commit -q -m "init: WikiForge vault $VAULT_NAME"
fi

# ── Setup .claude in vault ────────────────────────────────────────────────────
CLAUDE_TARGET="$VAULT_DATA_PATH/.claude"
mkdir -p "$CLAUDE_TARGET/hooks" "$CLAUDE_TARGET/queue" "$CLAUDE_TARGET/logs" "$CLAUDE_TARGET/logs/translate-locks"
touch "$CLAUDE_TARGET/queue/pending-atoms.txt"

# Copy hooks from repo
if [[ -d "$REPO_DIR/.claude/hooks" ]]; then
    cp -r "$REPO_DIR/.claude/hooks/." "$CLAUDE_TARGET/hooks/"
    chmod +x "$CLAUDE_TARGET/hooks/"*.sh 2>/dev/null || true
fi

cat > "$CLAUDE_TARGET/settings.json" << SETTINGS_EOF
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": "bash $CLAUDE_TARGET/hooks/on-file-write.sh", "timeout": 120}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "bash $CLAUDE_TARGET/hooks/on-bash-complete.sh", "timeout": 30}]
      }
    ],
    "Stop": [{"hooks": [{"type": "command", "command": "bash $CLAUDE_TARGET/hooks/on-session-stop.sh", "timeout": 60}]}],
    "SessionStart": [{"hooks": [{"type": "command", "command": "bash $CLAUDE_TARGET/hooks/on-session-start.sh", "timeout": 10}]}]
  }
}
SETTINGS_EOF

echo "[4/4] Done."

# ── Optional: run ingest ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Vault '$VAULT_NAME' created!         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Config : $CONFIG_FILE"
echo "  Data   : $VAULT_DATA_PATH"
echo ""

if [[ -n "$SOURCES_INPUT" ]]; then
    echo "Sources provided: $SOURCES_INPUT"
    if confirm "Run ingest now?" "y"; then
        # Write sources to a temp list file and call batch-ingest.sh
        TMPLIST=$(mktemp)
        echo "$SOURCES_INPUT" | tr ',' '\n' | tr -d ' ' | grep -v '^$' > "$TMPLIST"
        VAULT_NAME="$VAULT_NAME" bash "$SCRIPT_DIR/batch-ingest.sh" "$TMPLIST"
        rm -f "$TMPLIST"
    fi
else
    echo "Next steps:"
    echo "  1. Add sources:  bash scripts/batch-ingest.sh <list-file>"
    echo "  2. Or open Claude and run /init-vault for the guided flow"
    echo ""
fi
