#!/usr/bin/env python3
"""
auto-link.py

Post-write hook: given an atom stem + language, insert [[wiki/{lang}/stem]] entry
into every moc/{lang}/{topic}.md that covers one of its topics, if not already present.

Usage:
  python3 scripts/auto-link.py pricing--base-price --lang en
  python3 scripts/auto-link.py pricing--base-price --lang es
  python3 scripts/auto-link.py --all --lang en
  python3 scripts/auto-link.py --all          # all atoms in all enabled languages
  python3 scripts/auto-link.py --dry-run pricing--base-price --lang en
"""

import argparse
import re
import sys
from pathlib import Path

TOPICS_RE = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)
CLAIM_RE = re.compile(r"^claim:\s*(.+?)$", re.MULTILINE)


def get_atom_meta(atom_path: Path):
    text = atom_path.read_text(errors="replace")
    m_topics = TOPICS_RE.search(text)
    m_claim = CLAIM_RE.search(text)
    topics = [t.strip() for t in m_topics.group(1).split(",")] if m_topics else []
    claim_raw = m_claim.group(1).strip() if m_claim else ""
    claim = re.sub(r"\*\*", "", claim_raw)[:100]
    return topics, claim


def already_linked(moc_text: str, lang: str, stem: str) -> bool:
    return f"[[wiki/{lang}/{stem}]]" in moc_text or f"[[wiki/{lang}/{stem}#" in moc_text


def append_to_moc(moc_path: Path, lang: str, stem: str, claim: str, dry_run: bool) -> bool:
    text = moc_path.read_text(errors="replace")
    if already_linked(text, lang, stem):
        return False

    entry = f"- [[wiki/{lang}/{stem}]] — {claim}"

    if "## Auto-linked" in text:
        new_text = text.rstrip("\n") + f"\n{entry}\n"
    else:
        new_text = text.rstrip("\n") + f"\n\n## Auto-linked\n\n{entry}\n"

    if dry_run:
        print(f"  [DRY-RUN] Would add to {moc_path.name}:\n    {entry}")
        return True
    moc_path.write_text(new_text)
    print(f"  [OK] Added to {moc_path.name}: {entry[:80]}")
    return True


def link_atom(stem: str, lang: str, vault_path: Path, dry_run: bool) -> int:
    wiki_dir = vault_path / "wiki" / lang
    atom_path = wiki_dir / f"{stem}.md"
    if not atom_path.exists():
        print(f"ERROR: atom not found: {atom_path}", file=sys.stderr)
        return 0

    topics, claim = get_atom_meta(atom_path)
    if not topics:
        print(f"  No topics found in {stem} — skipping")
        return 0

    moc_dir = vault_path / "moc" / lang
    linked = 0
    for topic in topics:
        moc_path = moc_dir / f"{topic}.md"
        if not moc_path.exists():
            continue
        if append_to_moc(moc_path, lang, stem, claim, dry_run):
            linked += 1

    if linked == 0:
        print(f"  {stem} [{lang}]: already linked in all relevant MOCs (or MOC missing)")
    return linked


def main():
    p = argparse.ArgumentParser()
    p.add_argument("atom", nargs="?", help="Atom stem (e.g. pricing--base-price)")
    p.add_argument("--lang", default=None, help="Language code (en, es, ...)")
    p.add_argument("--all", action="store_true", help="Backfill all atoms")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--vault", default=None, help="Vault path (default: $VAULT_PATH)")
    args = p.parse_args()

    if not args.atom and not args.all:
        p.print_help()
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig
    cfg = VaultConfig(args.vault)

    langs = [args.lang] if args.lang else cfg.languages

    if args.all:
        total = 0
        for lang in langs:
            wiki_dir = cfg.vault_path / "wiki" / lang
            if not wiki_dir.exists():
                print(f"  wiki/{lang}/ not found — skipping")
                continue
            print(f"\nLinking [{lang}]...")
            for atom_path in sorted(wiki_dir.glob("*.md")):
                n = link_atom(atom_path.stem, lang, cfg.vault_path, args.dry_run)
                total += n
        print(f"\nTotal new links: {total}")
    else:
        stem = args.atom.removesuffix(".md")
        total = 0
        for lang in langs:
            n = link_atom(stem, lang, cfg.vault_path, args.dry_run)
            total += n
        print(f"\nNew links added: {total}")


if __name__ == "__main__":
    main()
