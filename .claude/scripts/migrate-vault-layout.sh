#!/usr/bin/env bash
# migrate-vault-layout.sh — In-place migration from v1 (kind-first) to v2 (lang-first).
#
#   v1: $VAULT_PATH/{wiki,moc,raw,index,queries}/{lang}/...
#   v2: $VAULT_PATH/{lang}/{wiki,moc,raw,index,queries}/...
#
# Three phases:
#   1. Move per-kind/per-lang directories from v1 to v2 paths.
#   2. Rewrite wikilinks in every .md body: [[kind/lang/stem]] → [[lang/kind/stem]].
#   3. Remove empty v1 kind directories.
#
# Idempotent: a v2 vault is a no-op. An empty vault is a no-op (new writes go to v2).
# A partially-migrated vault is completed without re-touching what's already done.
#
# Usage:
#   bash .claude/scripts/migrate-vault-layout.sh [--vault NAME] [--dry-run]
#   VAULT_NAME=oma-test-1 bash .claude/scripts/migrate-vault-layout.sh --dry-run

set -euo pipefail

DRY_RUN=0
VAULT_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --vault)
            shift
            [[ $# -lt 1 ]] && { echo "ERROR: --vault requires a name" >&2; exit 2; }
            VAULT_ARG="$1"
            ;;
        --help|-h)
            sed -n '2,20p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "ERROR: unknown arg: $1" >&2; exit 2 ;;
    esac
    shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve vault path + enabled langs via Python (single source of truth: VaultConfig).
VAULT_INFO=$(
    SCRIPT_DIR_VAR="$SCRIPT_DIR" \
    VAULT_ARG_VAR="$VAULT_ARG" \
    python3 - <<'PYEOF'
import os, sys, json
sys.path.insert(0, os.environ['SCRIPT_DIR_VAR'])
from config import VaultConfig
arg = os.environ.get('VAULT_ARG_VAR') or None
cfg = VaultConfig(arg)
print(json.dumps({'vault_path': str(cfg.vault_path), 'langs': cfg.enabled_languages}))
PYEOF
)

VAULT_PATH=$(echo "$VAULT_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['vault_path'])")
LANGS=$(echo "$VAULT_INFO" | python3 -c "import sys,json; print(' '.join(json.load(sys.stdin)['langs']))")

if [[ -z "$VAULT_PATH" || ! -d "$VAULT_PATH" ]]; then
    echo "ERROR: vault path missing or invalid: $VAULT_PATH" >&2
    exit 1
fi
if [[ -z "$LANGS" ]]; then
    echo "ERROR: no enabled languages declared in vault.yml" >&2
    exit 1
fi

KINDS="wiki moc raw index queries"

# Detect layout. v2 wins when both shapes exist (resume case).
CURRENT_LAYOUT="empty"
for L in $LANGS; do
    if [[ -d "$VAULT_PATH/$L/wiki" || -d "$VAULT_PATH/$L/moc" || -d "$VAULT_PATH/$L/raw" ]]; then
        CURRENT_LAYOUT="v2"
        break
    fi
done
if [[ "$CURRENT_LAYOUT" == "empty" ]]; then
    for L in $LANGS; do
        for K in $KINDS; do
            if [[ -d "$VAULT_PATH/$K/$L" ]]; then
                CURRENT_LAYOUT="v1"
                break 2
            fi
        done
    done
fi

# A vault may be partially-migrated (some langs in v2, some still in v1). Detect that.
HAS_V1_LEFT=0
for L in $LANGS; do
    for K in $KINDS; do
        [[ -d "$VAULT_PATH/$K/$L" ]] && { HAS_V1_LEFT=1; break 2; }
    done
done

echo "Vault: $VAULT_PATH"
echo "Layout detected: $CURRENT_LAYOUT"
echo "Enabled langs: $LANGS"
[[ "$DRY_RUN" -eq 1 ]] && echo "DRY-RUN MODE — no changes will be written"
echo

if [[ "$CURRENT_LAYOUT" == "empty" ]]; then
    echo "Vault is empty — nothing to migrate."
    exit 0
fi
if [[ "$CURRENT_LAYOUT" == "v2" && "$HAS_V1_LEFT" -eq 0 ]]; then
    echo "Already v2 — nothing to migrate."
    exit 0
fi

# ── Phase 1: move per-lang/per-kind directories ──────────────────────────────
echo "═══ Phase 1: Move directories ═══"
PHASE1_MOVED=0
PHASE1_SKIPPED=0
for L in $LANGS; do
    for K in $KINDS; do
        SRC="$VAULT_PATH/$K/$L"
        DST="$VAULT_PATH/$L/$K"
        [[ -d "$SRC" ]] || continue

        if [[ -d "$DST" ]]; then
            REMAINING=$(find "$SRC" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')
            echo "  [SKIP] $K/$L → $L/$K (destination exists; $REMAINING items still in source)"
            PHASE1_SKIPPED=$((PHASE1_SKIPPED + 1))
            continue
        fi

        echo "  MOVE  $K/$L → $L/$K"
        if [[ "$DRY_RUN" -eq 0 ]]; then
            mkdir -p "$VAULT_PATH/$L"
            mv "$SRC" "$DST"
        fi
        PHASE1_MOVED=$((PHASE1_MOVED + 1))
    done
done
echo "  ($PHASE1_MOVED moved, $PHASE1_SKIPPED skipped)"

# ── Phase 2: rewrite wikilinks in .md bodies ─────────────────────────────────
echo
echo "═══ Phase 2: Rewrite wikilinks ═══"

VAULT_PATH_VAR="$VAULT_PATH" \
LANGS_VAR="$LANGS" \
DRY_RUN_VAR="$DRY_RUN" \
python3 - <<'PYEOF'
import os, re
from pathlib import Path

vault = Path(os.environ['VAULT_PATH_VAR'])
langs = os.environ['LANGS_VAR'].split()
kinds = ['wiki', 'moc', 'raw', 'index', 'queries']
dry = os.environ['DRY_RUN_VAR'] == '1'

# Match [[kind/lang/...]] only when kind+lang are in our known sets — avoids
# touching wikilinks like [[meta/glossary]] that happen to contain a slash.
pattern = re.compile(
    r'\[\[(?P<kind>' + '|'.join(kinds) + r')/(?P<lang>' + '|'.join(langs) + r')/'
)

scanned = 0
rewritten = 0
for md in vault.rglob('*.md'):
    scanned += 1
    try:
        text = md.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        continue
    new_text = pattern.sub(lambda m: f"[[{m.group('lang')}/{m.group('kind')}/", text)
    if new_text != text:
        rewritten += 1
        rel = md.relative_to(vault)
        print(f"  REWRITE  {rel}")
        if not dry:
            md.write_text(new_text, encoding='utf-8')

print(f"  ({scanned} files scanned, {rewritten} rewritten)")
PYEOF

# ── Phase 3: clean up empty v1 kind dirs ─────────────────────────────────────
echo
echo "═══ Phase 3: Clean up empty v1 directories ═══"
for K in $KINDS; do
    [[ -d "$VAULT_PATH/$K" ]] || continue
    REMAINING=$(find "$VAULT_PATH/$K" -mindepth 1 2>/dev/null | head -1)
    if [[ -z "$REMAINING" ]]; then
        echo "  RMDIR  $K/"
        [[ "$DRY_RUN" -eq 0 ]] && rmdir "$VAULT_PATH/$K"
    else
        echo "  [KEEP] $K/ (non-empty — manual review)"
    fi
done

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN complete. Re-run without --dry-run to apply."
else
    echo "Migration complete: $VAULT_PATH is now v2."
fi
