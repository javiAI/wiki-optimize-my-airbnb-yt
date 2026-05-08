#!/usr/bin/env bash
# Ingest a single YouTube video transcript per enabled language.
# Usage: ingest.sh [--force] <video_id_or_url>
#
# Pipeline:
#   1. yt-dlp metadata + per-lang VTT (manual subs preferred, auto fallback)
#      for every lang in vault.yml `languages.enabled`. If the video's native
#      lang is not enabled, also fetch the native VTT for atomization input.
#   2. clean_vtt.py: dedupe + strip tags + group into ~20s blocks (per lang)
#   3. write {VAULT}/raw/{LANG}/YYYY-MM-DD--<slug>.md per available LANG
#      with frontmatter: native_lang, subtitle_source (manual|auto), language.
#
# Idempotent: skips a per-lang file if it already exists (use --force to rewrite).

set -euo pipefail

FORCE=0
if [[ "${1:-}" == "--force" ]]; then FORCE=1; shift; fi

INPUT="${1:?usage: ingest.sh [--force] <video_id_or_url>}"
VID="${INPUT##*v=}"; VID="${VID##*/}"; VID="${VID%%&*}"
URL="https://youtube.com/watch?v=${VID}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "${REPO_ROOT}/.claude/scripts/config.sh"
VAULT="${VAULT_PATH:?VAULT_PATH not set — see .claude/scripts/config.sh}"

# Resolve enabled_languages + original_language hint via VaultConfig.
read -r ENABLED_LANGS_CSV ORIG_LANG_HINT < <(python3 - <<'PY'
import os, sys
sys.path.insert(0, ".claude/scripts")
from config import VaultConfig
c = VaultConfig()
print(",".join(c.enabled_languages), c.get("source.original_language") or "")
PY
)
IFS=',' read -ra ENABLED_LANGS <<< "$ENABLED_LANGS_CSV"
[[ ${#ENABLED_LANGS[@]} -eq 0 ]] && { echo "ERROR: no enabled languages in vault.yml" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. Fetch metadata once (no subs yet — sub langs come in step 2).
yt-dlp --skip-download --print-json -o "${TMP}/%(id)s" "$URL" \
    > "${TMP}/meta.json" 2>"${TMP}/ytdl.err" \
  || { echo "yt-dlp metadata failed for $VID" >&2; tail -20 "${TMP}/ytdl.err" >&2; exit 1; }

# Detect native language from yt-dlp; fall back to vault hint, then enabled[0].
# Normalize region tags: yt-dlp may return `en-US`, `en-GB`, `pt-BR`, etc.
# We bucket by the base ISO code so atomization_lang_for() matches `en` in
# enabled_languages instead of creating a parallel `raw/en-US/` directory.
DETECTED_LANG=$(jq -r '.language // empty' "${TMP}/meta.json" 2>/dev/null || true)
DETECTED_LANG="${DETECTED_LANG%%-*}"
NATIVE_LANG="${DETECTED_LANG:-}"
[[ -z "$NATIVE_LANG" && -n "$ORIG_LANG_HINT" ]] && NATIVE_LANG="$ORIG_LANG_HINT"
[[ -z "$NATIVE_LANG" ]] && {
    NATIVE_LANG="${ENABLED_LANGS[0]}"
    echo "[ingest] WARN: native_lang missing from yt-dlp; defaulting to $NATIVE_LANG" >&2
}

# Build the list of langs to fetch: enabled ∪ {native_lang} (so atomization
# always has a transcript in the lang it will be written in). Bash 3.2-compat:
# avoid associative arrays — dedup native_lang against enabled list manually.
WANT_LANGS=("${ENABLED_LANGS[@]}")
NATIVE_IN_LIST=0
for _l in "${WANT_LANGS[@]}"; do
    [[ "$_l" == "$NATIVE_LANG" ]] && { NATIVE_IN_LIST=1; break; }
done
[[ $NATIVE_IN_LIST -eq 0 ]] && WANT_LANGS+=("$NATIVE_LANG")

# 2. Per-lang subtitle fetch: manual first, then auto. Returns whichever wins.
fetch_subs_for_lang() {
    local lang="$1"
    local outdir="$2"
    # Try manual creator subs first
    if yt-dlp --skip-download --write-sub --sub-lang "$lang" --sub-format vtt \
              -o "${outdir}/%(id)s" "$URL" > /dev/null 2>"${TMP}/ytdl.err.${lang}.man"; then
        local f
        f=$(ls "${outdir}"/*."${lang}".vtt 2>/dev/null | head -1 || true)
        if [[ -n "$f" ]]; then
            printf '%s\tmanual\n' "$f"
            return 0
        fi
    fi
    # Fallback: auto-translated / auto-generated captions
    if yt-dlp --skip-download --write-auto-sub --sub-lang "$lang" --sub-format vtt \
              -o "${outdir}/%(id)s" "$URL" > /dev/null 2>"${TMP}/ytdl.err.${lang}.auto"; then
        local f
        f=$(ls "${outdir}"/*."${lang}".vtt 2>/dev/null | head -1 || true)
        if [[ -n "$f" ]]; then
            printf '%s\tauto\n' "$f"
            return 0
        fi
    fi
    return 1
}

# 3. Extract metadata fields for the markdown frontmatter.
IFS=$'\t' read -r UPLOAD_DATE TITLE DURATION VIEWS LIKES COMMENTS < <(
  jq -r '[
    .upload_date // "00000000",
    (.title // "untitled" | gsub("[|\t\n]"; " ")),
    (.duration // 0 | tostring),
    (.view_count // 0 | tostring),
    (.like_count // 0 | tostring),
    (.comment_count // 0 | tostring)
  ] | @tsv' "${TMP}/meta.json"
)

DATE_ISO="${UPLOAD_DATE:0:4}-${UPLOAD_DATE:4:2}-${UPLOAD_DATE:6:2}"

SLUG=$(printf '%s' "$TITLE" \
  | tr '[:upper:]' '[:lower:]' \
  | LC_ALL=C sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g' \
  | cut -c1-60 \
  | sed -E 's/-+$//')
[[ -z "$SLUG" ]] && SLUG="untitled"

TITLE_YAML=$(printf '%s' "$TITLE" | sed 's/"/\\"/g')

# 4. Per-lang processing.
ANY_OK=0
for lang in "${WANT_LANGS[@]}"; do
    SUBDIR="${TMP}/${lang}"
    mkdir -p "$SUBDIR"
    OUT_DIR="${VAULT}/raw/${lang}"
    mkdir -p "$OUT_DIR"
    OUT_FILE="${OUT_DIR}/${DATE_ISO}--${SLUG}.md"

    if [[ -f "$OUT_FILE" && "$FORCE" -eq 0 ]]; then
        echo "SKIP (exists): $OUT_FILE"
        ANY_OK=1
        continue
    fi

    if ! result=$(fetch_subs_for_lang "$lang" "$SUBDIR"); then
        echo "MISS  ${lang}: no subtitles for $VID"
        continue
    fi

    VTT_FILE="${result%%$'\t'*}"
    SUB_SOURCE="${result##*$'\t'}"

    BODY=$(python3 "${REPO_ROOT}/.claude/scripts/clean_vtt.py" "$VTT_FILE")

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
      echo "language: ${lang}"
      echo "native_lang: ${NATIVE_LANG}"
      echo "subtitle_source: ${SUB_SOURCE}"
      echo "topics: []"
      echo "superseded_by: []"
      echo "---"
      echo
      echo "$BODY"
    } > "$OUT_FILE"

    echo "OK    ${lang} (${SUB_SOURCE}): ${OUT_FILE}"
    ANY_OK=1
done

if [[ "$ANY_OK" -eq 0 ]]; then
    echo "ERROR: no subtitles available in any requested lang for $VID" >&2
    exit 2
fi

# 5. If native_lang is outside enabled[], record an llm-fallback advisory.
# Atomization will fall back to enabled[0] without a verbatim transcript in the
# atomization lang, so excerpt_source: llm_fallback gets stamped on the atom.
# Surface this at /ingest-queue and session-start so the user sees it.
if [[ $NATIVE_IN_LIST -eq 0 ]]; then
    BUNDLE="${VAULT_NAME:-$(basename "$VAULT")}"
    FALLBACK_QUEUE="${REPO_ROOT}/vaults/${BUNDLE}/state/queue/llm-fallback.txt"
    mkdir -p "$(dirname "$FALLBACK_QUEUE")"
    touch "$FALLBACK_QUEUE"
    if ! grep -qF "$VID" "$FALLBACK_QUEUE"; then
        printf '%s\t%s\t%s\n' "$VID" "$NATIVE_LANG" "${ENABLED_LANGS[0]}" >> "$FALLBACK_QUEUE"
        echo "[ingest] ADVISORY: native_lang=$NATIVE_LANG ∉ enabled[]; atomization → ${ENABLED_LANGS[0]} (llm_fallback)" >&2
    fi
fi
