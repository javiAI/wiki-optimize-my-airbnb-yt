#!/usr/bin/env python3
"""
apply-proposed-contradictions.py

Post-test consolidator for O4v2 auto-curation. Reads `proposed_contradictions[]`
emitted by agents in vaults/{name}/tests/raw-responses/<LABEL>/run-<N>/Q*.json,
dedupes against the existing log at $VAULT_PATH/meta/contradictions.md, and
appends new entries.

Default mode is DRY-RUN: prints what would be appended. Pass --apply to write.

Usage:
  python3 scripts/apply-proposed-contradictions.py --label O4v2-post --run 1
  python3 scripts/apply-proposed-contradictions.py --label O4v2-post --run 1 --apply
  python3 scripts/apply-proposed-contradictions.py --label O4v2-post --run 1 --apply --min-severity HIGH

Dedupe key: sorted tuple of normalized atom names. If both atoms of a proposed
entry already appear together in any existing meta section, skip.

Atoms are normalized by stripping the [[notes/...]] / [[...]] wrapper and any
path prefix, so [[notes/pricing--five-percent-adjustments]] and
[[pricing--five-percent-adjustments]] match.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / ".claude" / "scripts"))
from config import VaultConfig  # noqa: E402

_cfg = VaultConfig()
RAW_DIR = REPO_ROOT / "vaults" / _cfg.name / "tests" / "raw-responses"
VAULT_PATH = Path(os.environ.get("VAULT_PATH", str(_cfg.vault_path)))
META_PATH = VAULT_PATH / "meta" / "contradictions.md"


def normalize_atom(s: str) -> str:
    if not s:
        return ""
    m = re.search(r"\[\[([^\]]+)\]\]", s)
    s = m.group(1) if m else s
    s = s.strip().lstrip("notes/").lstrip("/")
    s = s.split("#")[0]
    return s.lower()


def existing_atom_pairs(meta_text: str) -> set:
    pairs = set()
    sections = re.split(r"\n## \[", meta_text)
    for sec in sections[1:]:
        atoms_in_sec = re.findall(r"\[\[([^\]]+)\]\]", sec)
        norm = sorted(set(normalize_atom("[[" + a + "]]") for a in atoms_in_sec))
        for i in range(len(norm)):
            for j in range(i + 1, len(norm)):
                pairs.add((norm[i], norm[j]))
    return pairs


def collect_proposals(label: str, run: int):
    run_dir = RAW_DIR / label / f"run-{run}"
    if not run_dir.exists():
        sys.exit(f"ERROR: run dir not found: {run_dir}")
    proposals = []
    for q_path in sorted(run_dir.glob("Q*.json")):
        try:
            data = json.loads(q_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"WARN: skipping malformed {q_path.name}: {e}", file=sys.stderr)
            continue
        for entry in data.get("proposed_contradictions") or []:
            entry["_source_qid"] = data.get("question_id", q_path.stem)
            proposals.append(entry)
    return proposals


def dedupe(proposals, existing_pairs):
    seen_local = set()
    new_proposals = []
    for p in proposals:
        atoms = p.get("atoms") or []
        if len(atoms) < 2:
            continue
        key = tuple(sorted(normalize_atom(a) for a in atoms[:2]))
        if key in existing_pairs:
            continue
        if key in seen_local:
            continue
        seen_local.add(key)
        new_proposals.append(p)
    return new_proposals


def render_section(p: dict) -> str:
    today = date.today().isoformat()
    title = p.get("title") or f"{p.get('topic', 'unknown')}: auto-flagged"
    atoms = p.get("atoms") or []
    severity = p.get("severity", "MEDIUM")
    relation = p.get("relation", "direct")
    proposed = p.get("proposed_resolution", "(pendiente revisión humana)")
    evidence = p.get("evidence", "(sin evidencia adicional)")
    qid = p.get("_source_qid", "?")
    atom_lines = "\n".join(f"- {a}" for a in atoms)
    return f"""---

## [{today}] {title} (auto-proposed by O4v2)

**Severity**: {severity}
**Relation**: {relation}
**Source**: detected during O4v2 auto-curation in {qid}; pending human review.

**Atoms en conflicto:**
{atom_lines}

**Proposed resolution**: {proposed}

**Evidence**: {evidence}

> Esta entrada se generó automáticamente vía `scripts/apply-proposed-contradictions.py`. Revisar manualmente, ajustar resolución, y cuando esté validada eliminar el sufijo `(auto-proposed by O4v2)` del header.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--apply", action="store_true",
                    help="Write to meta/contradictions.md (default: dry-run)")
    ap.add_argument("--min-severity", choices=["HIGH", "MEDIUM"], default="MEDIUM")
    args = ap.parse_args()

    if not META_PATH.exists():
        sys.exit(f"ERROR: meta file not found: {META_PATH}")

    proposals = collect_proposals(args.label, args.run)
    if args.min_severity == "HIGH":
        proposals = [p for p in proposals if p.get("severity") == "HIGH"]

    meta_text = META_PATH.read_text(encoding="utf-8")
    existing = existing_atom_pairs(meta_text)
    new_props = dedupe(proposals, existing)

    print(f"Total proposals: {len(proposals)}")
    print(f"After dedupe vs meta: {len(new_props)} new")
    for p in new_props:
        print(f"  - {p.get('title', '?')} ({p.get('severity', '?')}) atoms={p.get('atoms', [])} qid={p.get('_source_qid', '?')}")

    if not new_props:
        print("Nothing to apply.")
        return

    if not args.apply:
        print("\n[DRY-RUN] Pass --apply to write.")
        for p in new_props:
            print(render_section(p))
        return

    appended = "\n".join(render_section(p) for p in new_props)
    if not meta_text.endswith("\n"):
        meta_text += "\n"
    META_PATH.write_text(meta_text + appended, encoding="utf-8")
    print(f"\nApplied {len(new_props)} new entries to {META_PATH}")


if __name__ == "__main__":
    main()
