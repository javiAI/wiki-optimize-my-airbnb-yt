#!/usr/bin/env python3
"""
auto-link.py

Post-ingest hook: given an atom filename, insert its [[notes/stem]] entry
into every MOC that covers one of its topics, if not already present.

Usage:
  python3 scripts/auto-link.py pricing--bootstrap-initial-price.md
  python3 scripts/auto-link.py pricing--bootstrap-initial-price   # stem also ok
  python3 scripts/auto-link.py --all    # backfill all atoms into MOCs
  python3 scripts/auto-link.py --dry-run pricing--bootstrap-initial-price.md
"""

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_PATH = Path(os.environ.get(
    "VAULT_PATH",
    "/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt"
))

NOTES_DIR = VAULT_PATH / "notes"
MOC_DIR = VAULT_PATH / "MOC"

TOPICS_RE = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)
CLAIM_RE = re.compile(r"^claim:\s*(.+?)$", re.MULTILINE)


def get_atom_meta(atom_path):
    text = atom_path.read_text(errors="replace")
    m_topics = TOPICS_RE.search(text)
    m_claim = CLAIM_RE.search(text)
    topics = [t.strip() for t in m_topics.group(1).split(",")] if m_topics else []
    claim_raw = m_claim.group(1).strip() if m_claim else ""
    claim = re.sub(r"\*\*", "", claim_raw)[:100]
    return topics, claim


def already_linked(moc_text, stem):
    return f"[[notes/{stem}]]" in moc_text or f"[[notes/{stem}#" in moc_text


def append_to_moc(moc_path, stem, claim, dry_run):
    text = moc_path.read_text(errors="replace")
    if already_linked(text, stem):
        return False

    entry = f"- [[notes/{stem}]] — {claim}"
    new_text = text.rstrip("\n") + f"\n\n## Auto-linked\n\n{entry}\n"

    # If there's already an ## Auto-linked section, just append the entry
    if "## Auto-linked" in text:
        new_text = text.rstrip("\n") + f"\n{entry}\n"

    if dry_run:
        print(f"  [DRY-RUN] Would add to {moc_path.name}:\n    {entry}")
        return True
    moc_path.write_text(new_text)
    print(f"  [OK] Added to {moc_path.name}: {entry[:80]}")
    return True


def link_atom(atom_stem, dry_run):
    atom_path = NOTES_DIR / f"{atom_stem}.md"
    if not atom_path.exists():
        print(f"ERROR: atom not found: {atom_path}", file=sys.stderr)
        return 0

    topics, claim = get_atom_meta(atom_path)
    if not topics:
        print(f"  No topics found in {atom_stem} — skipping")
        return 0

    linked = 0
    for topic in topics:
        moc_path = MOC_DIR / f"{topic}.md"
        if not moc_path.exists():
            continue
        if append_to_moc(moc_path, atom_stem, claim, dry_run):
            linked += 1

    if linked == 0:
        print(f"  {atom_stem}: already linked in all relevant MOCs (or MOC missing)")
    return linked


def main():
    p = argparse.ArgumentParser()
    p.add_argument("atom", nargs="?",
                   help="Atom filename or stem (e.g. pricing--bootstrap.md)")
    p.add_argument("--all", action="store_true",
                   help="Backfill all atoms into their MOCs")
    p.add_argument("--dry-run", action="store_true",
                   help="Print changes without writing")
    args = p.parse_args()

    if not args.atom and not args.all:
        p.print_help()
        sys.exit(1)

    if args.all:
        total = 0
        for atom_path in sorted(NOTES_DIR.glob("*.md")):
            stem = atom_path.stem
            n = link_atom(stem, args.dry_run)
            total += n
        print(f"\nTotal new links: {total}")
    else:
        stem = args.atom.removesuffix(".md")
        n = link_atom(stem, args.dry_run)
        print(f"\nNew links added: {n}")


if __name__ == "__main__":
    main()
