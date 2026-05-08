#!/bin/bash
# init-vault.sh — WikiForge vault setup (terminal use).
#
# Usage:
#   init-vault.sh                       # interactive wizard (prompts for each field)
#   init-vault.sh --config answers.yml  # non-interactive (reads all answers from YAML)
#   init-vault.sh -c answers.yml -y     # non-interactive + auto-confirm "Create vault?"
#   init-vault.sh <input_dir>           # directory-mode: auto-detect config.yaml + sources.txt
#
# Directory-mode:
#   Pass a directory containing config.yaml (or config.yml) and optionally
#   sources.txt. The script reads answers from config.yaml without prompting,
#   and runs batch-ingest.sh on sources.txt after bundle creation.
#   If <input_dir> sits inside vaults/, its basename is the vault slot
#   (config.yaml's `name` may override it; if it doesn't match, the bundle
#   uses the basename and a warning is printed).
#
# Creates a new vault bundle at vaults/{name}/ in this repo:
#   vaults/{name}/vault.yml      — config (rendered from .claude/templates/vault.yml.template)
#   vaults/{name}/agents.md      — per-vault agents reference (from .claude/templates/agents.md.template)
#   vaults/{name}/state/         — runtime state (created on demand by hooks)
#   vaults/{name}/tests/         — per-vault test bundle (questions, prompts, raw-responses, results, comparisons)
#
# Also creates the vault data directory at the chosen path. The data directory
# contains DATA ONLY ({lang}/{raw,wiki,moc,index,queries}/ + meta/). No hooks,
# no settings.json, no queues — those live in the repo's .claude/ and
# vaults/{name}/state/.
#
# Config-file schema (see .claude/templates/init-answers.yml.example):
#   name: my-vault                 # required
#   data_path: ~/Dev/my-vault      # required
#   description: Short description # optional (default: "Vault for {name}")
#   languages: [en, es]            # required; list or "en,es" string
#   auto_atoms: true               # optional (default: true)
#   auto_propagate: true           # optional (default: true if 2+ langs, else false)
#   auto_refine: false             # optional (default: false)
#   make_active: true              # optional (default: true)
#
# For the guided Claude-integrated flow, use the /init-vault skill.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VAULTS_DIR="$REPO_DIR/vaults"
TEMPLATES_DIR="$REPO_DIR/.claude/templates"

# ── Argument parsing ─────────────────────────────────────────────────────────

CONFIG_FILE=""
AUTO_YES=0
REVIEW_AFTER=0
INPUT_DIR=""
SOURCES_FILE=""
VAULT_NAME_FROM_DIR=""   # set only when INPUT_DIR is a vaults/{name}/ slot
while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--config)
            CONFIG_FILE="${2:?--config requires a path}"
            # `:?` rejects unset but not empty — guard separately.
            if [[ -z "${CONFIG_FILE// }" ]]; then
                echo "ERROR: --config requires a non-empty path." >&2
                exit 2
            fi
            shift 2
            ;;
        -y|--yes)
            AUTO_YES=1
            shift
            ;;
        --review)
            REVIEW_AFTER=1
            shift
            ;;
        -h|--help)
            sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        -*)
            echo "ERROR: unknown flag: $1" >&2
            echo "Usage: $0 [--config <yaml>] [--yes] [--review] | $0 <input_dir>" >&2
            exit 2
            ;;
        *)
            if [[ -z "${1// }" ]]; then
                echo "ERROR: positional argument (input directory) is empty." >&2
                exit 2
            fi
            if [[ -n "$INPUT_DIR" ]]; then
                echo "ERROR: only one positional argument (input directory) is supported." >&2
                exit 2
            fi
            INPUT_DIR="$1"
            shift
            ;;
    esac
done

# ── Directory-mode: auto-detect config.yaml + sources.txt ────────────────────
if [[ -n "$INPUT_DIR" ]]; then
    if [[ ! -d "$INPUT_DIR" ]]; then
        echo "ERROR: input directory not found: $INPUT_DIR" >&2
        exit 1
    fi
    INPUT_DIR="$(cd "$INPUT_DIR" && pwd)"

    # Find a config file (config.yaml or config.yml).
    if [[ -f "$INPUT_DIR/config.yaml" ]]; then
        DIR_CONFIG="$INPUT_DIR/config.yaml"
    elif [[ -f "$INPUT_DIR/config.yml" ]]; then
        DIR_CONFIG="$INPUT_DIR/config.yml"
    else
        DIR_CONFIG=""
    fi

    if [[ -n "$DIR_CONFIG" ]]; then
        if [[ -n "$CONFIG_FILE" && "$CONFIG_FILE" != "$DIR_CONFIG" ]]; then
            echo "ERROR: --config and <input_dir>/config.yaml both provided. Pick one." >&2
            exit 2
        fi
        CONFIG_FILE="$DIR_CONFIG"
    fi

    # If the directory is itself a vaults/{name}/ slot, remember the slot name.
    if [[ "$(dirname "$INPUT_DIR")" == "$VAULTS_DIR" ]]; then
        VAULT_NAME_FROM_DIR="$(basename "$INPUT_DIR")"
    fi

    # Detect sources file (auto-ingest after creation).
    if [[ -f "$INPUT_DIR/sources.txt" ]]; then
        SOURCES_FILE="$INPUT_DIR/sources.txt"
    fi
fi

# ── Config-file loader (non-interactive mode) ────────────────────────────────
# Reads the YAML and exports each field as an env var. Missing fields stay
# unset so the interactive defaults apply later. Uses Python (with config.py's
# parser as fallback) so we don't depend on yq/PyYAML being installed.

CFG_NAME=""
CFG_DATA_PATH=""
CFG_DESCRIPTION=""
CFG_LANGS=""
CFG_AUTO_ATOMS=""
CFG_AUTO_PROPAGATE=""
CFG_AUTO_REFINE=""
CFG_MAKE_ACTIVE=""

if [[ -n "$CONFIG_FILE" ]]; then
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "ERROR: config file not found: $CONFIG_FILE" >&2
        exit 1
    fi
    # Load the YAML and emit shell-quoted KEY=value lines we can `eval`.
    # We pass the repo's scripts dir as argv[2] so the Python helper can fall
    # back to config.py's parser if PyYAML isn't installed.
    EVAL_LINES=$(python3 - "$CONFIG_FILE" "$SCRIPT_DIR" <<'PY'
import sys
# Reuse config.py's parser if PyYAML is missing.
try:
    import yaml
    with open(sys.argv[1]) as f:
        d = yaml.safe_load(f) or {}
except ImportError:
    sys.path.insert(0, sys.argv[2])
    from config import _parse_simple_yaml
    from pathlib import Path
    d = _parse_simple_yaml(Path(sys.argv[1]))

def shq(v):
    s = str(v)
    return "'" + s.replace("'", "'\\''") + "'"

mapping = {
    "name": "CFG_NAME",
    "data_path": "CFG_DATA_PATH",
    "description": "CFG_DESCRIPTION",
    "auto_atoms": "CFG_AUTO_ATOMS",
    "auto_propagate": "CFG_AUTO_PROPAGATE",
    "auto_refine": "CFG_AUTO_REFINE",
    "make_active": "CFG_MAKE_ACTIVE",
}
for k, var in mapping.items():
    if k in d and d[k] is not None:
        v = d[k]
        if isinstance(v, bool):
            v = "true" if v else "false"
        print(f"{var}={shq(v)}")

# Languages: accept list or comma-separated string.
langs = d.get("languages")
if isinstance(langs, list):
    langs_csv = ",".join(str(x).strip() for x in langs if str(x).strip())
elif isinstance(langs, str):
    langs_csv = ",".join(s.strip() for s in langs.split(",") if s.strip())
else:
    langs_csv = ""
if langs_csv:
    print(f"CFG_LANGS={shq(langs_csv)}")
PY
    )
    eval "$EVAL_LINES"
fi

# ── Plugin defaults loader ───────────────────────────────────────────────────
# Pulls `defaults:` from .claude/wikiforge/config.yaml so /init-vault can run
# zero-prompt when the plugin is preconfigured. Per-vault answers (from
# CONFIG_FILE above) win — this only fills in fields still empty.

DEFAULT_LINES=$(python3 - "$REPO_DIR" "$SCRIPT_DIR" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from config import read_config

cfg = read_config(Path(sys.argv[1]))
defaults = cfg.get("defaults") or {}

def shq(v):
    return "'" + str(v).replace("'", "'\\''") + "'"

def emit(var, val):
    if val is None:
        return
    if isinstance(val, bool):
        val = "true" if val else "false"
    print(f"{var}={shq(val)}")

emit("DEF_DATA_PATH_PATTERN", defaults.get("data_path_pattern"))

langs = defaults.get("languages")
if isinstance(langs, list):
    langs_csv = ",".join(str(x).strip() for x in langs if str(x).strip())
elif isinstance(langs, str):
    langs_csv = ",".join(s.strip() for s in langs.split(",") if s.strip())
else:
    langs_csv = ""
if langs_csv:
    emit("DEF_LANGS", langs_csv)

pipeline = defaults.get("pipeline") or {}
emit("DEF_AUTO_ATOMS", pipeline.get("auto_atoms"))
emit("DEF_AUTO_PROPAGATE", pipeline.get("auto_propagate"))
emit("DEF_AUTO_REFINE", pipeline.get("auto_refine"))
PY
)
DEF_DATA_PATH_PATTERN=""
DEF_LANGS=""
DEF_AUTO_ATOMS=""
DEF_AUTO_PROPAGATE=""
DEF_AUTO_REFINE=""
eval "$DEFAULT_LINES"

[[ -z "$CFG_LANGS" && -n "$DEF_LANGS" ]] && CFG_LANGS="$DEF_LANGS"
[[ -z "$CFG_AUTO_ATOMS" && -n "$DEF_AUTO_ATOMS" ]] && CFG_AUTO_ATOMS="$DEF_AUTO_ATOMS"
[[ -z "$CFG_AUTO_PROPAGATE" && -n "$DEF_AUTO_PROPAGATE" ]] && CFG_AUTO_PROPAGATE="$DEF_AUTO_PROPAGATE"
[[ -z "$CFG_AUTO_REFINE" && -n "$DEF_AUTO_REFINE" ]] && CFG_AUTO_REFINE="$DEF_AUTO_REFINE"

# ── Helpers ──────────────────────────────────────────────────────────────────

ask() {
    local prompt="$1"
    local default="${2:-}"
    local answer
    if [[ -n "$default" ]]; then
        read -r -p "$prompt [$default]: " answer >&2
        echo "${answer:-$default}"
    else
        read -r -p "$prompt: " answer >&2
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

# Render a template by substituting {{TOKEN}} placeholders.
# Args: <template_path> <output_path> [TOKEN=value ...]
render_template() {
    local tpl="$1"; shift
    local out="$1"; shift
    if [[ ! -f "$tpl" ]]; then
        echo "ERROR: template not found: $tpl" >&2
        return 1
    fi
    local content
    content=$(cat "$tpl")
    local pair key value
    for pair in "$@"; do
        key="${pair%%=*}"
        value="${pair#*=}"
        # Use awk to do safe literal replacement (no regex interpretation of value)
        content=$(awk -v k="{{$key}}" -v v="$value" \
            '{ idx = index($0, k); while (idx > 0) { $0 = substr($0,1,idx-1) v substr($0, idx+length(k)); idx = index($0, k) } print }' \
            <<< "$content")
    done
    printf '%s\n' "$content" > "$out"
}

# ── Wizard ───────────────────────────────────────────────────────────────────
# Each field uses the value from the YAML config if provided, else prompts the
# user interactively. Validation (slug normalization, path expansion, lang
# splitting) runs on both code paths so the YAML doesn't bypass safety checks.

echo ""
echo "WikiForge — New Vault Setup"
[[ -n "$CONFIG_FILE" ]] && echo "  (using answers from $CONFIG_FILE)"
echo ""

# Vault name precedence: VAULT_NAME_FROM_DIR (when input dir is a vaults/ slot)
# wins over CFG_NAME — the directory you put your config in IS the bundle slot.
# If they disagree, prefer the directory and warn.
if [[ -n "$VAULT_NAME_FROM_DIR" ]]; then
    if [[ -n "$CFG_NAME" && "$CFG_NAME" != "$VAULT_NAME_FROM_DIR" ]]; then
        echo "  ⚠  config.yaml name='$CFG_NAME' does not match directory '$VAULT_NAME_FROM_DIR'."
        echo "     Using '$VAULT_NAME_FROM_DIR' (directory wins)."
    fi
    VAULT_NAME="$VAULT_NAME_FROM_DIR"
elif [[ -n "$CFG_NAME" ]]; then
    VAULT_NAME="$CFG_NAME"
else
    VAULT_NAME=$(ask "Vault name (slug, no spaces)" "my-vault")
fi
VAULT_NAME=$(echo "$VAULT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

BUNDLE_DIR="$VAULTS_DIR/$VAULT_NAME"
# An existing dir with vault.yml is a real bundle (refuse). An empty dir or one
# holding only config.yaml/sources.txt is a bundle slot the user pre-created
# for directory-mode — that's expected and we proceed without prompting.
if [[ -f "$BUNDLE_DIR/vault.yml" ]]; then
    echo "  ⚠  Bundle already exists: $BUNDLE_DIR"
    if [[ -n "$CONFIG_FILE" ]]; then
        echo "  ERROR: refusing to overwrite an existing bundle in non-interactive mode." >&2
        echo "  Remove it first:  rm -rf $BUNDLE_DIR" >&2
        exit 1
    fi
    if ! confirm "  Overwrite?" "n"; then
        echo "Aborted — edit $BUNDLE_DIR/vault.yml directly if needed."
        exit 0
    fi
fi

if [[ -n "$CFG_DATA_PATH" ]]; then
    VAULT_DATA_PATH="$CFG_DATA_PATH"
elif [[ -n "$DEF_DATA_PATH_PATTERN" ]]; then
    # Plugin defaults provide the path pattern — apply silently. Users who
    # want to override per-vault can pass --config with a data_path field.
    VAULT_DATA_PATH="${DEF_DATA_PATH_PATTERN//\{name\}/$VAULT_NAME}"
elif [[ -n "$CONFIG_FILE" ]]; then
    VAULT_DATA_PATH="$HOME/Dev/obsidian_vaults/$VAULT_NAME"
else
    VAULT_DATA_PATH=$(ask "Vault data path" "$HOME/Dev/obsidian_vaults/$VAULT_NAME")
fi
VAULT_DATA_PATH="${VAULT_DATA_PATH/#\~/$HOME}"
VAULT_DATA_PATH="$(realpath -m "$VAULT_DATA_PATH" 2>/dev/null || echo "$VAULT_DATA_PATH")"

if [[ -n "$CFG_DESCRIPTION" ]]; then
    DESCRIPTION="$CFG_DESCRIPTION"
elif [[ -n "$CONFIG_FILE" ]]; then
    DESCRIPTION="Vault for $VAULT_NAME"
else
    DESCRIPTION=$(ask "Short description" "Vault for $VAULT_NAME")
fi

if [[ -n "$CFG_LANGS" ]]; then
    LANGS_RAW="$CFG_LANGS"
else
    echo ""
    echo "Languages — every language you want atoms in. Order doesn't matter;"
    echo "  no primary/secondary distinction. Each video's native language is auto-"
    echo "  detected per-source. If a video's native lang isn't in this list, it"
    echo "  will be atomized in the first language listed."
    echo "  Examples: en  |  en,es  |  en,es,fr"
    LANGS_RAW=$(ask "Enabled languages (comma-separated ISO codes)" "en")
fi
ALL_LANGS=$(echo "$LANGS_RAW" | tr ',' '\n' | tr -d ' ' | tr '[:upper:]' '[:lower:]' | tr '\n' ',' | sed 's/,$//')
NUM_LANGS=$(echo "$ALL_LANGS" | tr ',' '\n' | wc -l | tr -d ' ')

# Pipeline toggles. Defaults match the interactive recommendations:
# auto_atoms=true, auto_propagate=true (only if 2+ langs), auto_refine=false.
echo ""
AUTO_ATOMS="false"
AUTO_PROPAGATE="false"
AUTO_REFINE="false"

if [[ -n "$CFG_AUTO_ATOMS" ]]; then
    [[ "$CFG_AUTO_ATOMS" == "true" ]] && AUTO_ATOMS="true"
elif [[ -n "$CONFIG_FILE" ]]; then
    AUTO_ATOMS="true"  # default when YAML omits it
else
    confirm "Auto-create atoms after ingest? (recommended)" "y" && AUTO_ATOMS="true"
fi

# Auto-propagate replaces auto-translate: when an atom is created, propagate
# it to every other enabled lang by re-atomizing at the same locator using
# the target-lang transcript (or LLM fallback if target-lang subtitle missing).
if [[ "$NUM_LANGS" -gt 1 ]]; then
    if [[ -n "$CFG_AUTO_PROPAGATE" ]]; then
        [[ "$CFG_AUTO_PROPAGATE" == "true" ]] && AUTO_PROPAGATE="true"
    elif [[ -n "$CONFIG_FILE" ]]; then
        AUTO_PROPAGATE="true"  # default when YAML omits it and 2+ langs
    else
        confirm "Auto-propagate atoms to other enabled languages? (recommended)" "y" && AUTO_PROPAGATE="true"
    fi
fi

if [[ -n "$CFG_AUTO_REFINE" ]]; then
    [[ "$CFG_AUTO_REFINE" == "true" ]] && AUTO_REFINE="true"
elif [[ -z "$CONFIG_FILE" ]]; then
    confirm "Auto-refine atoms (second quality pass, uses more tokens)?" "n" && AUTO_REFINE="true"
fi

# ── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "Setup summary"
echo "  Name           : $VAULT_NAME"
echo "  Bundle         : $BUNDLE_DIR"
echo "  Data path      : $VAULT_DATA_PATH"
echo "  Languages      : $ALL_LANGS"
echo "  Auto-atoms     : $AUTO_ATOMS"
echo "  Auto-propagate : $AUTO_PROPAGATE"
echo "  Auto-refine    : $AUTO_REFINE"
echo ""

if [[ "$AUTO_YES" -eq 1 || -n "$CONFIG_FILE" ]]; then
    : # non-interactive: skip the final confirm
elif ! confirm "Create vault?" "y"; then
    echo "Aborted."
    exit 0
fi

# ── Create vault bundle (repo) + data structure (vault path) ─────────────────

echo ""
echo "[1/4] Creating vault bundle: $BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/state/queue" "$BUNDLE_DIR/state/logs"
# /test-vault populates tests/ on demand (questions.{lang}.yaml, raw-responses/,
# results/, reports/, history.md). Keep the parent dir only.
mkdir -p "$BUNDLE_DIR/tests"

# Hub enrichment queues (drained by on-ingest-batch-close.sh → /refresh-hubs).
# pending-atoms.txt is created on-demand by the ingest pipeline.
: > "$BUNDLE_DIR/state/queue/entity-enrichment.txt"
: > "$BUNDLE_DIR/state/queue/comparison-enrichment.txt"

# Ingest counter — incremented per source by on-ingest-batch-close.sh, used to
# auto-fire /audit (or /audit --deep) every `maintenance.audit_every_n_ingests`.
echo 0 > "$BUNDLE_DIR/state/.ingest-counter"

echo "[2/4] Creating vault data structure at $VAULT_DATA_PATH (v2 layout)"
IFS=',' read -ra LANG_ARRAY <<< "$ALL_LANGS"
LANG_DIRS=""
for lang in "${LANG_ARRAY[@]}"; do
    lang=$(echo "$lang" | tr -d ' ')
    # v2 layout: {VAULT_PATH}/{lang}/{kind}/. Each lang holds its own raw/wiki/moc/index/queries/.
    LANG_DIRS="$LANG_DIRS $VAULT_DATA_PATH/$lang/raw $VAULT_DATA_PATH/$lang/wiki $VAULT_DATA_PATH/$lang/moc $VAULT_DATA_PATH/$lang/index $VAULT_DATA_PATH/$lang/queries"
done
mkdir -p "$VAULT_DATA_PATH/meta" $LANG_DIRS

# ── Render vault.yml + agents.md from templates ──────────────────────────────

echo "[3/4] Rendering vault.yml + agents.md from templates"

ENABLED_YAML=$(echo "$ALL_LANGS" | tr ',' '\n' | tr -d ' ' | awk '{printf "\"%s\", ", $0}' | sed 's/, $//')

# Reuse AUTO_TRANSLATE name for template var so older agents.md templates still
# render; the rendered key in vault.yml is now `auto_propagate`.
render_template \
    "$TEMPLATES_DIR/vault.yml.template" \
    "$BUNDLE_DIR/vault.yml" \
    "VAULT_NAME=$VAULT_NAME" \
    "DESCRIPTION=$DESCRIPTION" \
    "VAULT_PATH=$VAULT_DATA_PATH" \
    "ENABLED_LANGS=$ENABLED_YAML" \
    "AUTO_ATOMS=$AUTO_ATOMS" \
    "AUTO_TRANSLATE=$AUTO_PROPAGATE" \
    "AUTO_REFINE=$AUTO_REFINE"

render_template \
    "$TEMPLATES_DIR/agents.md.template" \
    "$BUNDLE_DIR/agents.md" \
    "VAULT_NAME=$VAULT_NAME" \
    "VAULT_PATH=$VAULT_DATA_PATH" \
    "ENABLED_LANGS=$ALL_LANGS"

# ── Create stubs (vault data only) ───────────────────────────────────────────

echo "[4/4] Creating data stubs"

# Generate empty per-lang index.md via auto-link.py — same code path that
# regenerates the index on every atom write, so initial state is consistent
# with the live state. At init there are no MOCs so this writes the empty stub.
VAULT_NAME="$VAULT_NAME" python3 "$REPO_DIR/.claude/scripts/auto-link.py" --index-only \
    --vault "$VAULT_NAME" 2>/dev/null || \
    for lang in "${LANG_ARRAY[@]}"; do
        lang=$(echo "$lang" | tr -d ' ')
        cat > "$VAULT_DATA_PATH/$lang/index/index.md" << EOF
# Vault Index — $VAULT_NAME ($lang)

_No MOCs yet. Run \`/ingest\` then \`/ingest-queue\` to populate._
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

# Entities registry — seed file for entity-detect.py. Populate `entities:` with
# the whitelist of slugs + aliases the vault should always treat as entities.
# entity-detect.py also appends slugs it observes during ingest (after passing
# capitalisation / multi-word noun-phrase filters), so this file grows with the
# corpus. Leaving the seed empty is fine — detection still works on
# capitalised noun phrases, just with more false-positive risk on the first
# few ingests.
cat > "$VAULT_DATA_PATH/meta/entities-registry.yaml" << 'EOF'
# Entities registry — pattern-match seed for entity-detect.py.
#
# Each entry:
#   slug:        # kebab-case, used as the file name (entity--<slug>.md)
#     kind: tool | company | person | product | service | book | channel
#     aliases: [<alias>, ...]   # case-insensitive surface forms

entities: {}
EOF

# ── Active-vault pointer (config.yaml) ────────────────────────────────────────
# When 2+ bundles exist, VaultConfig refuses to guess. Writing the new vault as
# active here means the user can immediately /ingest, /query etc. without
# needing to set $VAULT_NAME in every shell. If other bundles already exist we
# ask first — silently overwriting could surprise the user.
#
# config.yaml replaces the older single-line .claude/state/active-vault file.
# We write active_vault + active_lang (= enabled[0]) so query routing has a
# deterministic fallback when auto-detection is undecidable.

# First lang in ENABLED_LANGS is the deterministic fallback for routing —
# auto-detect overrides this per-query when confident.
DEFAULT_LANG=$(echo "$ALL_LANGS" | tr ',' '\n' | head -1 | tr -d ' ')

set_active_vault() {
    python3 - "$REPO_DIR" "$VAULT_NAME" "$DEFAULT_LANG" << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / ".claude" / "scripts"))
from config import write_state
write_state(Path(sys.argv[1]), active_vault=sys.argv[2], active_lang=sys.argv[3])
# Remove the legacy active-vault file if present — state/wikiforge.yaml supersedes it.
legacy = Path(sys.argv[1]) / ".claude" / "state" / "active-vault"
if legacy.exists():
    legacy.unlink()
PYEOF
}

OTHER_BUNDLE_COUNT=0
for d in "$VAULTS_DIR"/*/; do
    [[ -f "${d}vault.yml" && "${d%/}" != "$BUNDLE_DIR" ]] && OTHER_BUNDLE_COUNT=$((OTHER_BUNDLE_COUNT + 1))
done

ACTIVE_SET=0
if [[ "$OTHER_BUNDLE_COUNT" -eq 0 ]]; then
    # Only bundle in repo → make it active without prompting.
    set_active_vault
    ACTIVE_SET=1
elif [[ -n "$CFG_MAKE_ACTIVE" ]]; then
    # YAML decided: only set active if explicitly true.
    if [[ "$CFG_MAKE_ACTIVE" == "true" ]]; then
        set_active_vault
        ACTIVE_SET=1
    fi
elif [[ -n "$CONFIG_FILE" || "$AUTO_YES" -eq 1 ]]; then
    # Non-interactive default: set active (matches the interactive default).
    set_active_vault
    ACTIVE_SET=1
elif confirm "Make '$VAULT_NAME' the active vault for this repo?" "y"; then
    set_active_vault
    ACTIVE_SET=1
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "Vault '$VAULT_NAME' created."
echo "  Bundle      : $BUNDLE_DIR"
echo "  Vault data  : $VAULT_DATA_PATH"
if [[ "$ACTIVE_SET" -eq 1 ]]; then
    echo "  Active      : yes (.claude/state/wikiforge.yaml — vault=$VAULT_NAME, lang=$DEFAULT_LANG)"
else
    echo "  Active      : no — set with: bash .claude/scripts/set-config.sh active_vault $VAULT_NAME"
fi
echo ""
echo "  Review your vault config:  $BUNDLE_DIR/vault.yml"

# ── Auto-ingest sources.txt (directory-mode only) ────────────────────────────
if [[ -n "$SOURCES_FILE" ]]; then
    echo ""
    echo "Found sources file: $SOURCES_FILE"
    echo "Running batch-ingest..."
    echo ""
    VAULT_NAME="$VAULT_NAME" bash "$REPO_DIR/.claude/scripts/batch-ingest.sh" "$SOURCES_FILE" || {
        echo ""
        echo "  ⚠  batch-ingest exited with errors. Vault was created; re-run ingest manually:" >&2
        echo "     VAULT_NAME=$VAULT_NAME bash .claude/scripts/batch-ingest.sh $SOURCES_FILE" >&2
    }
fi

echo ""
echo "Next steps:"
if [[ -z "$SOURCES_FILE" ]]; then
    echo "  - Ingest sources:  VAULT_NAME=$VAULT_NAME bash .claude/scripts/batch-ingest.sh <list-file>"
fi
echo "  - Open Claude in this repo and run /init-vault for the guided flow."
echo ""
echo "To delete this vault from the repo: rm -rf $BUNDLE_DIR"
echo "To delete the data:                 rm -rf $VAULT_DATA_PATH"

# ── Optional: open vault.yml for review ──────────────────────────────────────
if [[ "$REVIEW_AFTER" -eq 1 ]]; then
    if [[ -n "${EDITOR:-}" ]]; then
        "$EDITOR" "$BUNDLE_DIR/vault.yml"
    elif [[ "$(uname)" == "Darwin" ]] && command -v code >/dev/null 2>&1; then
        code -r "$BUNDLE_DIR/vault.yml"
    elif command -v vi >/dev/null 2>&1; then
        vi "$BUNDLE_DIR/vault.yml"
    else
        echo "  ⚠  No editor available — set \$EDITOR or open $BUNDLE_DIR/vault.yml manually." >&2
    fi
fi
