#!/usr/bin/env bash
# Build $VAULT/meta/videos.md (master table) from ingested sources,
# append ingest entry to log.md, and refresh "Fuentes" section in index.md.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${REPO_ROOT}/scripts/config.sh"
VAULT="${VAULT_PATH:?VAULT_PATH not set — see scripts/config.sh.example}"
SOURCES="${VAULT}/raw"
VIDEOS_MD="${VAULT}/meta/videos.md"
LOG_MD="${VAULT}/log.md"
INDEX_MD="${VAULT}/index.md"

TODAY=$(date '+%F')
COUNT=$(find "${SOURCES}" -name "*.md" | wc -l | tr -d ' ')

# 1. videos.md — master table, sorted by published desc
{
  echo "# Videos — Master Table"
  echo
  echo "> Auto-generated from \`raw/*.md\` frontmatter. Do not edit manually."
  echo "> Last updated: ${TODAY} — ${COUNT} videos."
  echo
  echo "| Published | Views | Likes | Dur (s) | Auth | Transcript |"
  echo "|-----------|------:|------:|--------:|:----:|-----------|"
} > "$VIDEOS_MD"

python3 "${REPO_ROOT}/scripts/extract-meta.py" "$SOURCES" >> "$VIDEOS_MD"

# 2. Append to log.md
{
  echo
  echo "## [${TODAY}] ingest | batch Optimize My Airbnb (${COUNT} videos)"
  echo "- Source: YouTube channel @OptimizeMyAirbnb"
  echo "- Subtitle source: en (auto-caption, original language)"
  echo "- Output: \`raw/*.md\` (${COUNT} files)"
  echo "- Meta table: \`meta/videos.md\`"
  echo "- Next: atomic extraction per video (§4.1 step 2) — deferred, manual/guided"
} >> "$LOG_MD"

# 3. Update Fuentes section of index.md
python3 - "$INDEX_MD" "$COUNT" "$TODAY" <<'PY'
import sys, re, pathlib
idx_path = pathlib.Path(sys.argv[1])
count = sys.argv[2]
today = sys.argv[3]
text = idx_path.read_text()
new_section = (
  "## Fuentes\n\n"
  f"**{count} transcripciones** en `raw/` (último batch: {today}).\n"
  "Tabla completa en [[meta/videos]]. Listar por recencia: "
  "`ls -1 raw/ | sort -r`.\n"
)
text = re.sub(r"## (Fuentes|Transcripciones)\n.*", new_section, text, flags=re.DOTALL)
text = re.sub(r"> Última actualización: .*", f"> Última actualización: {today}", text)
idx_path.write_text(text)
PY

echo "OK — videos.md (${COUNT} rows), log.md appended, index.md refreshed"
