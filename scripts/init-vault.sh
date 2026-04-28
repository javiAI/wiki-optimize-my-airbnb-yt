#!/bin/bash
# init-vault.sh — Bootstrap a new WikiForge vault
# Usage: scripts/init-vault.sh <vault-name> <vault-path>
# Example: scripts/init-vault.sh my-cooking-vault ~/Dev/vaults/cooking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

VAULT_NAME="${1:-}"
VAULT_PATH="${2:-}"

if [[ -z "$VAULT_NAME" || -z "$VAULT_PATH" ]]; then
    echo "Usage: $0 <vault-name> <vault-path>"
    echo "Example: $0 my-cooking-vault ~/Dev/vaults/cooking"
    exit 1
fi

VAULT_PATH="${VAULT_PATH/#\~/$HOME}"  # Expand ~

echo "=== WikiForge: Initializing vault '$VAULT_NAME' at $VAULT_PATH ==="

# 1. Create standard folder structure
echo "[1/6] Creating folder structure..."
mkdir -p \
    "$VAULT_PATH/raw" \
    "$VAULT_PATH/wiki/en" \
    "$VAULT_PATH/wiki/es" \
    "$VAULT_PATH/moc/en" \
    "$VAULT_PATH/moc/es" \
    "$VAULT_PATH/index/en" \
    "$VAULT_PATH/index/es" \
    "$VAULT_PATH/queries/en" \
    "$VAULT_PATH/queries/es" \
    "$VAULT_PATH/meta"

# 2. Copy vault.yaml template
echo "[2/6] Creating vault.yaml..."
if [[ -f "$REPO_DIR/templates/vault.yaml.template" ]]; then
    sed "s/YOUR-VAULT-NAME/$VAULT_NAME/g" \
        "$REPO_DIR/templates/vault.yaml.template" > "$VAULT_PATH/vault.yaml"
    echo "  → Edit $VAULT_PATH/vault.yaml to configure topics and languages"
else
    echo "  WARNING: templates/vault.yaml.template not found; creating minimal vault.yaml"
    cat > "$VAULT_PATH/vault.yaml" << EOF
name: "$VAULT_NAME"
description: ""
version: "1.0"
source:
  type: youtube
  original_language: en
languages:
  enabled: [en]
  primary: en
  secondary: []
  detect_from_query: true
topics: []
pipeline:
  auto_atoms: true
  auto_translate: false
  auto_link: true
  deep_links: true
  qa_on_create: true
qa:
  completeness: true
  url_validation: true
  anglicism_check: []
  conflict_check: true
EOF
fi

# 3. Create stub index files
echo "[3/6] Creating index stubs..."
cat > "$VAULT_PATH/index/en/index.md" << 'EOF'
# Vault Index

| Topic | Atoms | Top claim |
|-------|-------|-----------|
| — | — | Run `/audit` to populate |

→ Read `moc/en/{topic}.md` for full topic details.
EOF

cat > "$VAULT_PATH/index/es/index.md" << 'EOF'
# Índice del Vault

| Topic | Átomos | Claim principal |
|-------|--------|-----------------|
| — | — | Ejecuta `/audit` para poblar |

→ Lee `moc/es/{topic}.md` para detalles completos por topic.
EOF

# 4. Create stub meta files
echo "[4/6] Creating meta stubs..."
touch "$VAULT_PATH/meta/contradictions.md"
touch "$VAULT_PATH/meta/backlinks.md"
touch "$VAULT_PATH/meta/glossary.md"
[[ ! -f "$VAULT_PATH/meta/contradictions.md" ]] || \
    echo "# Contradictions\n\nNo contradictions registered yet." > "$VAULT_PATH/meta/contradictions.md"

# 5. Copy .claude config (hooks + settings)
echo "[5/6] Setting up .claude config..."
CLAUDE_TARGET="$VAULT_PATH/.claude"
mkdir -p "$CLAUDE_TARGET/hooks" "$CLAUDE_TARGET/queue" "$CLAUDE_TARGET/logs"

# Copy hooks if they exist in the repo
if [[ -d "$REPO_DIR/.claude/hooks" ]]; then
    cp -r "$REPO_DIR/.claude/hooks/." "$CLAUDE_TARGET/hooks/"
    chmod +x "$CLAUDE_TARGET/hooks/"*.sh 2>/dev/null || true
fi

# Create settings.json pointing to hook scripts
cat > "$CLAUDE_TARGET/settings.json" << SETTINGS_EOF
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_TARGET/hooks/on-file-write.sh",
          "timeout": 120
        }]
      },
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "$CLAUDE_TARGET/hooks/on-bash-complete.sh",
          "timeout": 30
        }]
      }
    ],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_TARGET/hooks/on-session-stop.sh",
        "timeout": 60
      }]
    }],
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_TARGET/hooks/on-session-start.sh",
        "timeout": 10
      }]
    }]
  }
}
SETTINGS_EOF

touch "$CLAUDE_TARGET/queue/pending-atoms.txt"

# 6. Initialize git
echo "[6/6] Initializing git..."
if [[ ! -d "$VAULT_PATH/.git" ]]; then
    git -C "$VAULT_PATH" init -q
    cat > "$VAULT_PATH/.gitignore" << 'EOF'
.obsidian/
*.log
.claude/logs/
EOF
    git -C "$VAULT_PATH" add vault.yaml index/ meta/ .gitignore
    git -C "$VAULT_PATH" commit -q -m "init: WikiForge vault $VAULT_NAME"
fi

echo ""
echo "=== WikiForge vault '$VAULT_NAME' initialized! ==="
echo ""
echo "Next steps:"
echo "  1. Edit vault.yaml → set topics, languages, description"
echo "  2. Run: scripts/batch-ingest.sh <sources-list.txt>"
echo "     OR:  /ingest <source-id>  (Claude Code skill)"
echo "  3. When atoms are ready: /ingest-queue"
echo "  4. Periodic health check: /audit"
