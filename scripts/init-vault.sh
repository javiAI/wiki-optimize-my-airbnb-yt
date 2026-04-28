#!/bin/bash
# init-vault.sh — Interactive WikiForge vault setup wizard
#
# Usage (non-interactive, all args provided):
#   scripts/init-vault.sh <vault-name> <vault-path>
#
# Usage (interactive wizard):
#   scripts/init-vault.sh
#
# After setup, optionally launches Claude with an initial prompt.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

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

ask_list() {
    local prompt="$1"
    local example="$2"
    echo "$prompt"
    echo "  (comma-separated, e.g. $example)"
    read -r -p "  > " answer
    echo "$answer"
}

confirm() {
    local prompt="$1"
    local default="${2:-y}"
    read -r -p "$prompt [${default}]: " answer
    answer="${answer:-$default}"
    [[ "${answer,,}" == "y" ]]
}

# ── Interactive wizard ────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        WikiForge — New Vault Setup       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Vault name and path
VAULT_NAME="${1:-}"
VAULT_PATH="${2:-}"

if [[ -z "$VAULT_NAME" ]]; then
    VAULT_NAME=$(ask "Vault name (slug, no spaces)" "my-vault")
fi

if [[ -z "$VAULT_PATH" ]]; then
    VAULT_PATH=$(ask "Vault path" "$HOME/Dev/vaults/$VAULT_NAME")
fi

VAULT_PATH="${VAULT_PATH/#\~/$HOME}"
VAULT_PATH="$(realpath -m "$VAULT_PATH" 2>/dev/null || echo "$VAULT_PATH")"

echo ""
echo "── Source configuration ──────────────────────────────────────────────────"

# 2. Source type
echo "Source type:"
echo "  1) youtube  — YouTube videos (yt-dlp + transcripts)"
echo "  2) pdf      — PDF documents (pdftotext)"
echo "  3) web      — Web pages (html2text)"
echo "  4) file     — Local files (direct read)"
SOURCE_TYPE_NUM=$(ask "Choose [1-4]" "1")
case "$SOURCE_TYPE_NUM" in
    1|youtube) SOURCE_TYPE="youtube" ;;
    2|pdf)     SOURCE_TYPE="pdf" ;;
    3|web)     SOURCE_TYPE="web" ;;
    4|file)    SOURCE_TYPE="file" ;;
    *)         SOURCE_TYPE="youtube" ;;
esac

# 3. Source language (original language of the source material)
SOURCE_LANG=$(ask "Source/original language (ISO code)" "en")
echo "  → Atoms will be created in '$SOURCE_LANG' first (the source language)"

# 4. Additional output languages
echo ""
echo "── Language configuration ────────────────────────────────────────────────"
echo "Additional output languages (translations beyond the source language)."
echo "Leave empty if you only want atoms in the source language."
EXTRA_LANGS_RAW=$(ask_list "Extra languages (comma-separated ISO codes)" "es,fr")
EXTRA_LANGS=""
if [[ -n "$EXTRA_LANGS_RAW" ]]; then
    # Normalize: remove spaces, lowercase
    EXTRA_LANGS=$(echo "$EXTRA_LANGS_RAW" | tr ',' '\n' | tr -d ' ' | tr '[:upper:]' '[:lower:]' | grep -v "^${SOURCE_LANG}$" | tr '\n' ',' | sed 's/,$//')
fi

# Build enabled languages list (source_lang first)
if [[ -n "$EXTRA_LANGS" ]]; then
    ALL_LANGS="${SOURCE_LANG},${EXTRA_LANGS}"
    AUTO_TRANSLATE="true"
else
    ALL_LANGS="${SOURCE_LANG}"
    AUTO_TRANSLATE="false"
fi

# 5. Topics
echo ""
echo "── Topic configuration ───────────────────────────────────────────────────"
echo "Topics structure the vault. You can leave empty for auto-detection on first ingest."
TOPICS_RAW=$(ask_list "Initial topics (comma-separated slugs)" "pricing,reviews,operations")

# Build topics YAML
TOPICS_YAML="[]"
if [[ -n "$TOPICS_RAW" ]]; then
    TOPICS_YAML="["
    IFS=',' read -ra TOPIC_ARRAY <<< "$TOPICS_RAW"
    for topic in "${TOPIC_ARRAY[@]}"; do
        topic=$(echo "$topic" | tr -d ' ')
        if [[ -n "$topic" ]]; then
            NAME=$(echo "$topic" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')
            TOPICS_YAML="${TOPICS_YAML}{id: ${topic}, name: \"${NAME}\", description: \"\"}, "
        fi
    done
    TOPICS_YAML="${TOPICS_YAML%, }]"
fi

# 6. Pipeline options
echo ""
echo "── Pipeline options ──────────────────────────────────────────────────────"
AUTO_ATOMS=$(confirm "Auto-create atoms after ingest?" "y" && echo "true" || echo "false")
AUTO_REFINE=$(confirm "Auto-refine atoms (second-pass quality pass, costs tokens)?" "n" && echo "true" || echo "false")

# ── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║              Setup Summary               ║"
echo "╚══════════════════════════════════════════╝"
echo "  Vault name    : $VAULT_NAME"
echo "  Path          : $VAULT_PATH"
echo "  Source type   : $SOURCE_TYPE"
echo "  Source lang   : $SOURCE_LANG"
echo "  All languages : $ALL_LANGS"
echo "  Auto-translate: $AUTO_TRANSLATE"
echo "  Topics        : ${TOPICS_RAW:-auto-detect}"
echo "  Auto-atoms    : $AUTO_ATOMS"
echo "  Auto-refine   : $AUTO_REFINE"
echo ""

if ! confirm "Create vault?" "y"; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "=== WikiForge: Initializing vault '$VAULT_NAME' ==="

# ── Create folder structure ───────────────────────────────────────────────────
echo "[1/6] Creating folder structure..."

# Build lang dirs from ALL_LANGS
IFS=',' read -ra LANG_ARRAY <<< "$ALL_LANGS"
LANG_DIRS=""
for lang in "${LANG_ARRAY[@]}"; do
    lang=$(echo "$lang" | tr -d ' ')
    LANG_DIRS="$LANG_DIRS $VAULT_PATH/wiki/$lang $VAULT_PATH/moc/$lang $VAULT_PATH/index/$lang $VAULT_PATH/queries/$lang"
done

mkdir -p $VAULT_PATH/raw $VAULT_PATH/meta $LANG_DIRS

# ── Write vault.yaml ──────────────────────────────────────────────────────────
echo "[2/6] Writing vault.yaml..."

ENABLED_LIST=$(echo "$ALL_LANGS" | tr ',' '\n' | tr -d ' ' | awk '{printf "\"%s\", ", $0}' | sed 's/, $//')
SECONDARY_LIST=$(echo "${EXTRA_LANGS:-}" | tr ',' '\n' | tr -d ' ' | grep -v '^$' | awk '{printf "\"%s\", ", $0}' | sed 's/, $//' || echo "")

cat > "$VAULT_PATH/vault.yaml" << YAML_EOF
name: "$VAULT_NAME"
description: ""
version: "1.0"

source:
  type: $SOURCE_TYPE
  original_language: $SOURCE_LANG

languages:
  enabled: [$ENABLED_LIST]
  primary: "$SOURCE_LANG"
  secondary: [${SECONDARY_LIST}]
  detect_from_query: true

topics: $TOPICS_YAML

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
  anglicism_check: [${SECONDARY_LIST}]
  conflict_check: true
YAML_EOF

# ── Create index stubs ────────────────────────────────────────────────────────
echo "[3/6] Creating index stubs..."
for lang in "${LANG_ARRAY[@]}"; do
    lang=$(echo "$lang" | tr -d ' ')
    cat > "$VAULT_PATH/index/$lang/index.md" << EOF
# Vault Index — $VAULT_NAME ($lang)

| Topic | Atoms | Summary |
|-------|-------|---------|
| — | — | Run /audit to populate |

→ Read \`moc/$lang/{topic}.md\` for full topic details.
EOF
done

# ── Create meta stubs ─────────────────────────────────────────────────────────
echo "[4/6] Creating meta stubs..."
cat > "$VAULT_PATH/meta/contradictions.md" << 'EOF'
# Contradictions

No contradictions documented yet. Format:

## [topic--atom-A vs topic--atom-B] YYYY-MM-DD
- **Conflict**: atom-A claims X; atom-B claims Y
- **Resolution**: primary=atom-A (reason: higher recency score)
- **Criterion**: temporal_supersession | contextual_scope | confidence_tier
EOF

touch "$VAULT_PATH/meta/backlinks.md" "$VAULT_PATH/meta/glossary.md"

# ── Write agents.md ───────────────────────────────────────────────────────────
cat > "$VAULT_PATH/agents.md" << EOF
# agents.md — Vault Reference Schema

Vault: $VAULT_NAME | Source: $SOURCE_TYPE ($SOURCE_LANG) | Languages: $ALL_LANGS

## Atom YAML Schema

\`\`\`yaml
lang: $SOURCE_LANG
claim: "Single falsifiable sentence."
topics: [topic-id]
confidence: high | medium | low
source_lang: $SOURCE_LANG
sources:
  - source_id: ID
    locator: "HH:MM-HH:MM"
    url: "deep-link-url"
    excerpt: "Direct quote."
conflicts_with: []
last_verified: YYYY-MM-DD
\`\`\`

## Structure
wiki/{lang}/ — atoms | moc/{lang}/ — maps | index/{lang}/ — tier-0 nav | raw/ — sources | meta/ — shared
EOF

# ── Setup .claude ─────────────────────────────────────────────────────────────
echo "[5/6] Setting up .claude config..."
CLAUDE_TARGET="$VAULT_PATH/.claude"
mkdir -p "$CLAUDE_TARGET/hooks" "$CLAUDE_TARGET/queue" "$CLAUDE_TARGET/logs" "$CLAUDE_TARGET/logs/translate-locks" "$CLAUDE_TARGET/logs/refine-locks"

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
        "hooks": [
          {"type": "command", "command": "bash $CLAUDE_TARGET/hooks/on-file-write.sh", "timeout": 120},
          {"type": "command", "command": "bash $CLAUDE_TARGET/hooks/on-config-change.sh", "timeout": 10}
        ]
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

touch "$CLAUDE_TARGET/queue/pending-atoms.txt"

# ── Git init ──────────────────────────────────────────────────────────────────
echo "[6/6] Initializing git..."
if [[ ! -d "$VAULT_PATH/.git" ]]; then
    git -C "$VAULT_PATH" init -q
    cat > "$VAULT_PATH/.gitignore" << 'EOF'
.obsidian/
*.log
.claude/logs/
EOF
    git -C "$VAULT_PATH" add vault.yaml index/ meta/ agents.md .gitignore .claude/settings.json
    git -C "$VAULT_PATH" commit -q -m "init: WikiForge vault $VAULT_NAME"
fi

# ── Success ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Vault '$VAULT_NAME' ready!           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Path: $VAULT_PATH"
echo ""
echo "Next steps:"
echo "  1. Edit $VAULT_PATH/vault.yaml to adjust topics if needed"
echo "  2. Add sources and run: bash scripts/batch-ingest.sh <list>"
echo "  3. Run /ingest-queue when ready to create atoms"
echo "  4. Run /audit for vault health checks"
echo ""

# ── Optional: launch Claude with initial prompt ───────────────────────────────
if confirm "Launch Claude to start working with this vault now?" "y"; then
    FIRST_TASK="source_lang=${SOURCE_LANG}, vault_path=${VAULT_PATH}, source_type=${SOURCE_TYPE}"
    if [[ -n "${TOPICS_RAW:-}" ]]; then
        FIRST_TASK="${FIRST_TASK}, topics=${TOPICS_RAW}"
    fi

    INITIAL_PROMPT="Vault initialized. Configuration: $FIRST_TASK.

What would you like to do?
- If you have source files ready: /ingest <source_id>
- If you want to batch ingest: run scripts/batch-ingest.sh first, then /ingest-queue
- If you want to import existing notes: python3 scripts/migrate-atoms.py --lang $SOURCE_LANG --vault $VAULT_PATH
- If you just want to explore: /audit"

    export VAULT_PATH
    cd "$VAULT_PATH"
    exec claude --print "$INITIAL_PROMPT"
fi
