#!/usr/bin/env python3
"""
mine-anglicismos.py

Extract candidate Spanish substitutions from evaluator violations[] across all
test runs. Cross-references CLAUDE.md §10.7 table to surface only NEW terms.

Output:
  - stdout: ranked candidate list (term | freq | runs_seen)
  - meta/proposed-substitutions.md (in vault): same list, ready for human review

Usage:
  python3 scripts/mine-anglicismos.py
  python3 scripts/mine-anglicismos.py --min-freq 2
  python3 scripts/mine-anglicismos.py --output-md   # also write to vault meta/

Design: counts per (term, run-dir) pair so a term repeated in 5 Qs of one run
counts as 5 mentions, but cross-run reproducibility is also tracked separately.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_PATH = Path(os.environ.get(
    "VAULT_PATH",
    "/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt"
))
RAW_DIR = REPO_ROOT / "tests" / "raw-responses"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

# Acentos/eñes → casi siempre español; excluir
SPANISH_CHARS = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")

# Markers de contexto positivo en el entorno de la cita → no es anglicismo
POSITIVE_CTX = re.compile(r"\b(bien|correcto|correcta|usado bien|adecuad[ao])\b", re.IGNORECASE)

# Markers que preceden a una *sugerencia* en español, no a un anglicismo.
# Si una cita aparece justo después de estos markers, es la propuesta, no el problema.
SUGGESTION_MARKERS = re.compile(
    r"(en lugar de|→|->|debería\s+(ser\s+)?|como\s+|sustituir por|reemplazar por|alternativa:?\s*|/\s*)\s*$",
    re.IGNORECASE,
)

QUOTED = re.compile(r"'([^']{1,60})'")

# Términos estructurales del vault que no son vocabulario
PATH_LIKE = re.compile(r"^(notes|moc|sources|index|meta|queries)/?$", re.IGNORECASE)


def load_table_terms():
    """Read CLAUDE.md §10.7 table left column → set of normalized terms."""
    text = CLAUDE_MD.read_text()
    # Tabla está entre el header de Lenguaje y la línea **Allow proper nouns**
    m = re.search(
        r"\*\*Lenguaje \(Spanish purity\)\*\*.*?\*\*Allow proper",
        text, re.DOTALL,
    )
    if not m:
        return set()
    block = m.group(0)
    terms = set()
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ❌"):
            continue
        # | host / hosts | anfitrión / anfitriones |
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        left = cells[0]
        # split por '/' y por '(' para capturar variantes
        for variant in re.split(r"[/(]", left):
            v = variant.strip().strip(")").lower()
            if v and not v.startswith("---"):
                terms.add(v)
    return terms


def load_whitelist():
    """Proper nouns / tech estandarizada."""
    return {
        "pricelabs", "wheelhouse", "beyond", "hostfully", "hospitable",
        "guesty", "ownerrez", "airbnb", "booking", "vrbo", "alltherooms",
        "airdna", "noiseaware", "minut", "google", "youtube", "superhost",
        "aircover", "instant book", "stays", "co-host", "cohost",
        "wifi", "pms", "api", "url", "os", "json", "yaml", "seo", "adr",
        "blt", "fpg", "tos", "gmb", "stayfi",
    }


def is_spanish(term):
    """Heurística: contiene acento/eñe → español, no anglicismo."""
    return bool(SPANISH_CHARS.search(term))


def should_skip(term, table_terms, whitelist):
    t = term.lower().strip()
    if not t or len(t) < 2 or len(t) > 50:
        return True
    if not re.search(r"[a-zA-Z]", t):
        return True
    if is_spanish(t):
        return True
    if PATH_LIKE.match(t):
        return True
    if t in table_terms:
        return True
    # Match parcial con table (e.g. 'listings' vs 'listing', 'fee' vs 'fee (genérico)')
    for tt in table_terms:
        if t == tt or t.rstrip("s") == tt.rstrip("s"):
            return True
    if t in whitelist:
        return True
    # Si la mayoría del string es número/símbolo, skip
    letters = sum(c.isalpha() for c in t)
    if letters < max(2, len(t) // 2):
        return True
    return False


def extract_terms(violation_str):
    """De una cadena de violation extrae candidatos.

    Para cada cita 'X', mira el texto que la precede: si termina en un
    suggestion-marker (`en lugar de`, `→`, `debería ser`...), es la propuesta
    en español, no el anglicismo — descartar.
    """
    if POSITIVE_CTX.search(violation_str):
        # Mezcla "X bien, Y mal" → ambiguo, skip todo el mensaje
        return []
    out = []
    for m in QUOTED.finditer(violation_str):
        before = violation_str[:m.start()]
        if SUGGESTION_MARKERS.search(before):
            continue
        term = m.group(1).lower().strip()
        # Si contiene '/' y NO es path-like, split y extender
        if "/" in term and not PATH_LIKE.match(term):
            for part in term.split("/"):
                p = part.strip()
                if p:
                    out.append(p)
        else:
            out.append(term)
    return out


def mine():
    table_terms = load_table_terms()
    whitelist = load_whitelist()

    # term -> {"total": N, "runs": set, "qs": set, "examples": [...]}
    candidates = defaultdict(
        lambda: {"total": 0, "runs": set(), "qs": set(), "examples": []}
    )

    eval_files = sorted(RAW_DIR.rglob("evaluation.json"))
    if not eval_files:
        print("No evaluation.json files found", file=sys.stderr)
        return {}, table_terms

    for ev_path in eval_files:
        run_id = f"{ev_path.parent.parent.name}/{ev_path.parent.name}"
        try:
            ev = json.loads(ev_path.read_text())
        except json.JSONDecodeError:
            continue
        for qid, qeval in ev.get("evaluations", {}).items():
            for v in qeval.get("violations", []):
                for term in extract_terms(v):
                    if should_skip(term, table_terms, whitelist):
                        continue
                    candidates[term]["total"] += 1
                    candidates[term]["runs"].add(run_id)
                    candidates[term]["qs"].add(f"{run_id}:{qid}")
                    if len(candidates[term]["examples"]) < 3:
                        candidates[term]["examples"].append(f"{run_id}:{qid}")

    return candidates, table_terms


def render(candidates, min_freq, table_terms):
    rows = sorted(
        candidates.items(),
        key=lambda kv: (-len(kv[1]["runs"]), -kv[1]["total"], kv[0]),
    )
    rows = [(t, d) for t, d in rows if d["total"] >= min_freq]

    print(f"\n=== Anglicismo candidates (min_freq={min_freq}) ===\n")
    print(f"Existing table: {len(table_terms)} terms")
    print(f"Eval files scanned: {len(list(RAW_DIR.rglob('evaluation.json')))}")
    print(f"Candidates above threshold: {len(rows)}\n")

    print(f"{'TERM':<32} {'FREQ':>5} {'RUNS':>5} {'EXAMPLES'}")
    print("-" * 100)
    for term, d in rows:
        examples = ", ".join(sorted(d["qs"])[:3])
        print(f"{term:<32} {d['total']:>5} {len(d['runs']):>5}  {examples}")
    return rows


def write_md(rows, out_path):
    lines = [
        "# Proposed Substitutions (auto-mined from evaluator violations)",
        "",
        "Source: `scripts/mine-anglicismos.py` over all `tests/raw-responses/*/run-*/evaluation.json`.",
        "Cross-checked against CLAUDE.md §10.7 table; only NEW terms shown.",
        "",
        "| Term | Freq | Runs | Suggested ES | Examples |",
        "|---|---|---|---|---|",
    ]
    for term, d in rows:
        examples = "; ".join(sorted(d["qs"])[:3])
        lines.append(f"| `{term}` | {d['total']} | {len(d['runs'])} | _(propón ES)_ | {examples} |")
    lines.append("")
    out_path.write_text("\n".join(lines))
    print(f"\n[OK] Wrote {out_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--min-freq", type=int, default=2,
                   help="Min total mentions to surface candidate (default: 2)")
    p.add_argument("--output-md", action="store_true",
                   help="Also write meta/proposed-substitutions.md to vault")
    args = p.parse_args()

    candidates, table_terms = mine()
    rows = render(candidates, args.min_freq, table_terms)

    if args.output_md:
        out = VAULT_PATH / "meta" / "proposed-substitutions.md"
        write_md(rows, out)


if __name__ == "__main__":
    main()
