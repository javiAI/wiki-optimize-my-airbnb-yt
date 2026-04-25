#!/usr/bin/env bash
# Ingest a single YouTube video transcript into vault/02-Transcripts/
# Usage: ingest-video.sh <video_id_or_url>
#
# Pipeline:
#   1. yt-dlp -> metadata JSON + EN auto-caption VTT
#   2. clean_vtt.py: dedupe + strip tags + group into ~20s blocks
#   3. write vault/02-Transcripts/YYYY-MM-DD--<slug>.md with YAML frontmatter
#
# Idempotent: skips if output file already exists (use --force to overwrite).

set -euo pipefail

FORCE=0
if [[ "${1:-}" == "--force" ]]; then FORCE=1; shift; fi

INPUT="${1:?usage: ingest-video.sh [--force] <video_id_or_url>}"
VID="${INPUT##*v=}"; VID="${VID##*/}"; VID="${VID%%&*}"
URL="https://youtube.com/watch?v=${VID}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${REPO_ROOT}/scripts/config.sh"
VAULT="${VAULT_PATH:?VAULT_PATH not set — see scripts/config.sh.example}"
OUT_DIR="${VAULT}/sources"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. Metadata
yt-dlp --skip-download --write-auto-sub --sub-lang en --sub-format vtt \
       --print-json -o "${TMP}/%(id)s.%(ext)s" "$URL" > "${TMP}/meta.json" 2>"${TMP}/ytdl.err" \
  || { echo "yt-dlp failed for $VID" >&2; tail -20 "${TMP}/ytdl.err" >&2; exit 1; }

VTT_FILE=$(ls "${TMP}"/*.en.vtt 2>/dev/null | head -1 || true)
if [[ -z "$VTT_FILE" ]]; then
  echo "No EN auto-captions for $VID — skipping" >&2
  exit 2
fi

# 2. Extract fields with jq
read -r UPLOAD_DATE TITLE DURATION VIEWS LIKES COMMENTS LANG < <(
  jq -r '[
    .upload_date // "00000000",
    (.title // "untitled" | gsub("[|\t\n]"; " ")),
    (.duration // 0 | tostring),
    (.view_count // 0 | tostring),
    (.like_count // 0 | tostring),
    (.comment_count // 0 | tostring),
    (.language // "en")
  ] | @tsv' "${TMP}/meta.json" | tr '\t' '\n' | paste -sd' ' -
)
# Reparse with tabs (title may contain spaces) — use a safer read
IFS=$'\t' read -r UPLOAD_DATE TITLE DURATION VIEWS LIKES COMMENTS LANG < <(
  jq -r '[
    .upload_date // "00000000",
    (.title // "untitled" | gsub("[|\t\n]"; " ")),
    (.duration // 0 | tostring),
    (.view_count // 0 | tostring),
    (.like_count // 0 | tostring),
    (.comment_count // 0 | tostring),
    (.language // "en")
  ] | @tsv' "${TMP}/meta.json"
)

DATE_ISO="${UPLOAD_DATE:0:4}-${UPLOAD_DATE:4:2}-${UPLOAD_DATE:6:2}"

# 3. Slug from title
SLUG=$(printf '%s' "$TITLE" \
  | tr '[:upper:]' '[:lower:]' \
  | LC_ALL=C sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g' \
  | cut -c1-60 \
  | sed -E 's/-+$//')
[[ -z "$SLUG" ]] && SLUG="untitled"

OUT_FILE="${OUT_DIR}/${DATE_ISO}--${SLUG}.md"

if [[ -f "$OUT_FILE" && "$FORCE" -eq 0 ]]; then
  echo "SKIP (exists): $OUT_FILE"
  exit 0
fi

# 4. Clean VTT into ~20s blocks via python helper
BODY=$(python3 "${REPO_ROOT}/scripts/clean_vtt.py" "$VTT_FILE")

# 5. Escape YAML string (title may contain quotes)
TITLE_YAML=$(printf '%s' "$TITLE" | sed 's/"/\\"/g')

# 6. Write markdown
{
  echo "---"
  echo "video_id: ${VID}"
  echo "title: \"${TITLE_YAML}\""
  echo "url: ${URL}"
  echo "published: ${DATE_ISO}"
  echo "duration_sec: ${DURATION%.*}"
  echo "views: ${VIEWS}"
  echo "likes: ${LIKES}"
  echo "comments: ${COMMENTS}"
  echo "channel_authority: high"
  echo "language: ${LANG}"
  echo "topics: []"
  echo "superseded_by: []"
  echo "---"
  echo
  echo "$BODY"
} > "$OUT_FILE"

echo "OK  ${OUT_FILE}"
