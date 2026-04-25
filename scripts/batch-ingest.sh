#!/usr/bin/env bash
# Batch-ingest all videos from a list file (one "video_id|title|duration" per line).
# Usage: batch-ingest.sh <list_file>

set -uo pipefail

LIST="${1:?usage: batch-ingest.sh <list_file>}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${REPO_ROOT}/scripts/config.sh"
: "${VAULT_PATH:?VAULT_PATH not set — see scripts/config.sh.example}"
LOG="${REPO_ROOT}/scripts/batch-ingest.log"

TOTAL=$(wc -l < "$LIST" | tr -d ' ')
OK=0; SKIP=0; FAIL=0; N=0

: > "$LOG"
echo "[$(date '+%F %T')] START batch: $TOTAL videos" | tee -a "$LOG"

while IFS='|' read -r VID TITLE DURATION; do
  N=$((N+1))
  printf "[%3d/%3d] %s " "$N" "$TOTAL" "$VID" | tee -a "$LOG"

  OUT=$("${REPO_ROOT}/scripts/ingest.sh" "$VID" 2>&1)
  RC=$?
  case $RC in
    0)
      if [[ "$OUT" == SKIP* ]]; then
        SKIP=$((SKIP+1)); echo "SKIP" | tee -a "$LOG"
      else
        OK=$((OK+1)); echo "OK" | tee -a "$LOG"
      fi
      ;;
    2)
      SKIP=$((SKIP+1)); echo "NO_SUBS" | tee -a "$LOG"
      ;;
    *)
      FAIL=$((FAIL+1)); echo "FAIL rc=$RC" | tee -a "$LOG"
      echo "    -> $OUT" | tee -a "$LOG"
      ;;
  esac
done < "$LIST"

echo "[$(date '+%F %T')] END  ok=$OK skip=$SKIP fail=$FAIL total=$N" | tee -a "$LOG"
