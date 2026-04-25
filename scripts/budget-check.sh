#!/usr/bin/env bash
# budget-check.sh — estima tokens de una query y verifica contra el ceiling del regime §4.2.
#
# Uso:
#   scripts/budget-check.sh [--regime A|B|C] <file1> [<file2> ...]
#   cat files.txt | scripts/budget-check.sh --regime B
#
# Notas:
# - Rutas se resuelven: primero absolutas, luego relativas a $VAULT_PATH.
# - Heurística: TOK_PER_LINE=11.5 (empírica para notas markdown del vault).
# - Sin --regime: auto-clasifica por tokens totales contra los ceilings A/B/C.
# - Exit codes: 0 = within budget, 2 = over budget, 1 = usage error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/config.sh"

REGIME=""
FILES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --regime)
      REGIME="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

# stdin support (one path per line)
if [[ ${#FILES[@]} -eq 0 ]] && [[ ! -t 0 ]]; then
  while IFS= read -r line; do
    [[ -n "$line" ]] && FILES+=("$line")
  done
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "usage: $0 [--regime A|B|C] <file>..." >&2
  exit 1
fi

TOK_PER_LINE=11.5

# Ceilings from §4.2.a (bash 3.2 compatible — no associative arrays).
# Valores provisionales 2026-04-24: +~4k vs diseño original para absorber index.md (~4k tokens baseline).
# Tras optimización #4 (split index.md), revertir a A=4000 / B=6000 / C=8500.
ceil_for() {
  case "$1" in
    A|a) echo 8000 ;;
    B|b) echo 10000 ;;
    C|c) echo 13000 ;;
    *)   echo 0 ;;
  esac
}

total_lines=0
total_tokens=0

printf "%-64s %8s %8s\n" "FILE" "LINES" "TOKENS"
printf "%-64s %8s %8s\n" "----" "-----" "------"

for f in "${FILES[@]}"; do
  resolved="$f"
  if [[ ! -f "$resolved" ]] && [[ -f "$VAULT_PATH/$f" ]]; then
    resolved="$VAULT_PATH/$f"
  fi
  if [[ ! -f "$resolved" ]]; then
    printf "%-64s %8s %8s\n" "${f:0:64}" "?" "MISSING"
    continue
  fi
  lines=$(wc -l < "$resolved" | tr -d ' ')
  tokens=$(awk -v l="$lines" -v t="$TOK_PER_LINE" 'BEGIN { printf "%d", l*t }')
  total_lines=$((total_lines + lines))
  total_tokens=$((total_tokens + tokens))
  display="${resolved#"$VAULT_PATH"/}"
  printf "%-64s %8d %8d\n" "${display:0:64}" "$lines" "$tokens"
done

echo ""
printf "TOTAL: %d lines, ~%d tokens\n" "$total_lines" "$total_tokens"

if [[ -z "$REGIME" ]]; then
  ceil_a=$(ceil_for A); ceil_b=$(ceil_for B); ceil_c=$(ceil_for C)
  if   (( total_tokens <= ceil_a )); then REGIME="A"; ceil=$ceil_a
  elif (( total_tokens <= ceil_b )); then REGIME="B"; ceil=$ceil_b
  elif (( total_tokens <= ceil_c )); then REGIME="C"; ceil=$ceil_c
  else REGIME="EXCEEDED"
  fi
  echo ""
  if [[ "$REGIME" == "EXCEEDED" ]]; then
    echo "Auto-classify: OVER all ceilings (A=8k, B=10k, C=13k). Replantear (§4.2.a)."
    exit 2
  else
    echo "Auto-classify: regime $REGIME (within its ceiling: $ceil tokens)."
    exit 0
  fi
fi

REGIME=$(echo "$REGIME" | tr '[:lower:]' '[:upper:]')
ceil=$(ceil_for "$REGIME")
if (( ceil == 0 )); then
  echo "ERROR: unknown regime '$REGIME' (expected A, B, or C)" >&2
  exit 1
fi

pct=$(awk -v t="$total_tokens" -v c="$ceil" 'BEGIN { printf "%.0f", (t/c)*100 }')
echo ""
if (( total_tokens <= ceil )); then
  echo "Regime $REGIME: within budget ($total_tokens / $ceil tokens, ${pct}%)."
  exit 0
else
  echo "Regime $REGIME: OVER BUDGET ($total_tokens / $ceil tokens, ${pct}%). Replantear (§4.2.a)."
  exit 2
fi
