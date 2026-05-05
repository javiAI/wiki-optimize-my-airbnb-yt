#!/usr/bin/env python3
"""
auto-link.py — wires a newly written atom into the wiki graph.

For the given atom stem + language it does FOUR things:

  1. atom → MOC: append `- [[wiki/{lang}/stem]] — claim` into every
     `moc/{lang}/{topic}.md` covering one of the atom's topics. Creates the
     MOC stub if it doesn't exist yet.

  2. atom → MOC backref: emit `**Topics**: [[moc/{lang}/topic]], ...` in the
     atom body footer so the atom points to its own MOC(s).

  3. atom → atom: BM25-rank the K most similar atoms in the same language
     (claim+topics weighted) and emit a `## Related` section with
     `[[wiki/{lang}/peer]]` links above a relative score floor.

  4. index: regenerate `index/{lang}/index.md` listing every MOC with its
     atom count, so the navigation root stays current.

All four are idempotent — re-running the script reproduces the same file.

Usage:
  python3 .claude/scripts/auto-link.py pricing--base-price --lang en
  python3 .claude/scripts/auto-link.py pricing--base-price --lang es
  python3 .claude/scripts/auto-link.py --all --lang en
  python3 .claude/scripts/auto-link.py --all          # all atoms in all enabled languages
  python3 .claude/scripts/auto-link.py --dry-run pricing--base-price --lang en
  python3 .claude/scripts/auto-link.py --no-related ...   # skip atom→atom (debug)
"""

import argparse
import re
import sys
from pathlib import Path

TOPICS_RE = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)
CLAIM_RE = re.compile(r"^claim:\s*(.+?)$", re.MULTILINE)

# Inter-atom linking config
RELATED_TOP_K = 5
RELATED_MIN_SCORE_RATIO = 0.3   # peer must score ≥ 30% of the top peer's score
RELATED_HEADER_BY_LANG = {"es": "## Relacionados", "en": "## Related"}
TOPIC_LABEL_BY_LANG = {"es": "**Temas**", "en": "**Topics**"}


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


def ensure_moc_stub(moc_path: Path, topic: str, lang: str, vault_path: Path, dry_run: bool) -> bool:
    """Create a fresh MOC file for {topic}/{lang} if missing.

    Returns True if a stub was created (or would be in dry-run), False if the
    file already existed.
    """
    if moc_path.exists():
        return False
    wiki_dir = vault_path / "wiki" / lang
    count = 0
    if wiki_dir.exists():
        topic_pat = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)
        for atom in wiki_dir.glob("*.md"):
            m = topic_pat.search(atom.read_text(errors="replace"))
            if not m:
                continue
            atom_topics = {t.strip() for t in m.group(1).split(",")}
            if topic in atom_topics:
                count += 1
    stub = f"# MOC — {topic} [{lang}]\n\n{count} atoms.\n\n## Auto-linked\n"
    if dry_run:
        print(f"  [DRY-RUN] Would create MOC stub: {moc_path}")
        return True
    moc_path.parent.mkdir(parents=True, exist_ok=True)
    moc_path.write_text(stub)
    print(f"  [OK] Created MOC stub: moc/{lang}/{moc_path.name} ({count} atoms)")
    return True


def append_to_moc(moc_path: Path, lang: str, stem: str, claim: str, dry_run: bool, section: str = None) -> bool:
    text = moc_path.read_text(errors="replace")
    if already_linked(text, lang, stem):
        return False

    entry = f"- [[wiki/{lang}/{stem}]] — {claim}"

    if section:
        # Insert under specific heading
        heading = f"## {section}"
        if heading in text:
            idx = text.index(heading) + len(heading)
            # Find end of that section's content (next ## or EOF)
            next_section = re.search(r'\n##\s', text[idx:])
            insert_at = idx + next_section.start() if next_section else len(text)
            new_text = text[:insert_at].rstrip("\n") + f"\n{entry}\n" + text[insert_at:]
        else:
            new_text = text.rstrip("\n") + f"\n\n{heading}\n\n{entry}\n"
    elif "## Auto-linked" in text:
        # Preserve a blank line between heading and first entry when section is empty.
        after_heading = text.split("## Auto-linked", 1)[1]
        if not re.search(r"^\s*-\s", after_heading, re.MULTILINE):
            new_text = text.rstrip("\n") + f"\n\n{entry}\n"
        else:
            new_text = text.rstrip("\n") + f"\n{entry}\n"
    else:
        new_text = text.rstrip("\n") + f"\n\n## Auto-linked\n\n{entry}\n"

    if dry_run:
        print(f"  [DRY-RUN] Would add to {moc_path.name}:\n    {entry}")
        return True
    moc_path.write_text(new_text)
    print(f"  [OK] Added to {moc_path.name}: {entry[:80]}")
    return True


def link_atom(stem: str, lang: str, vault_path: Path, dry_run: bool,
              section: str = None, vault_index=None, with_related: bool = True,
              vault_name: str = None, with_index: bool = True) -> int:
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
        ensure_moc_stub(moc_path, topic, lang, vault_path, dry_run)
        if dry_run and not moc_path.exists():
            # In dry-run we didn't actually create the stub, so we can't append.
            print(f"  [DRY-RUN] Would link {stem} into moc/{lang}/{topic}.md")
            linked += 1
            continue
        if append_to_moc(moc_path, lang, stem, claim, dry_run, section):
            linked += 1

    if with_related:
        related = compute_related(stem, lang, vault_path, index=vault_index)
        if upsert_related_section(atom_path, topics, related, lang, dry_run):
            linked += 1

    if with_index:
        regenerate_index(vault_path, lang, vault_name or "vault", dry_run)

    if linked == 0:
        print(f"  {stem} [{lang}]: already linked in all relevant MOCs (and Related is current)")
    return linked


# ── Inter-atom linking (atom → atom + atom → MOC backref) ────────────────────

def compute_related(stem: str, lang: str, vault_path: Path, index=None) -> list:
    """Return [(stem, claim, score), ...] of top BM25 peers in the same lang.

    Reuses retrieve.py's VaultIndex. Self is filtered out. Peers below
    `RELATED_MIN_SCORE_RATIO * top_score` are dropped — only genuinely close
    matches survive, so a topical outlier ends up with an empty Related list
    rather than spurious links.
    """
    atom_path = vault_path / "wiki" / lang / f"{stem}.md"
    if not atom_path.exists():
        return []
    text = atom_path.read_text(errors="replace")
    m_claim = CLAIM_RE.search(text)
    if not m_claim:
        return []
    query = m_claim.group(1).strip().strip('"')
    m_topics = TOPICS_RE.search(text)
    if m_topics:
        query += " " + " ".join(t.strip() for t in m_topics.group(1).split(","))

    if index is None:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from retrieve import VaultIndex  # type: ignore
        except ImportError:
            return []
        index = VaultIndex(vault_path, lang)

    ranked = index.score(query, RELATED_TOP_K + 1)
    ranked = [(score, s) for score, s in ranked if s != stem]
    if not ranked:
        return []
    top_score = ranked[0][0]
    threshold = top_score * RELATED_MIN_SCORE_RATIO
    out = []
    for score, peer_stem in ranked[:RELATED_TOP_K]:
        if score < threshold:
            break
        atom = index.atoms.get(peer_stem) or {}
        peer_claim = (atom.get("fm") or {}).get("claim", "")[:90]
        out.append((peer_stem, peer_claim, score))
    return out


def render_related_section(topics: list, related: list, lang: str) -> str:
    """Render the trailing block: topic backrefs + related-atom list."""
    heading = RELATED_HEADER_BY_LANG.get(lang, "## Related")
    label = TOPIC_LABEL_BY_LANG.get(lang, "**Topics**")
    moc_links = ", ".join(f"[[moc/{lang}/{t}]]" for t in topics)
    lines = [heading, "", f"{label}: {moc_links}"]
    if related:
        lines.append("")
        for peer_stem, peer_claim, _score in related:
            claim_clean = peer_claim.strip().rstrip(".").strip('"').strip()
            lines.append(f"- [[wiki/{lang}/{peer_stem}]] — {claim_clean}")
    return "\n".join(lines) + "\n"


def upsert_related_section(atom_path: Path, topics: list, related: list,
                           lang: str, dry_run: bool) -> bool:
    """Insert or replace the trailing Related/Topics block. Idempotent."""
    text = atom_path.read_text(errors="replace")
    heading = RELATED_HEADER_BY_LANG.get(lang, "## Related")
    new_section = render_related_section(topics, related, lang)

    # Strip any existing block headed by `heading` up to next `##` heading or EOF.
    pat = re.compile(
        rf"^{re.escape(heading)}.*?(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    stripped = pat.sub("", text).rstrip() + "\n"
    new_text = stripped + "\n" + new_section

    if new_text == text:
        return False
    if dry_run:
        print(f"  [DRY-RUN] Would update Related block on {atom_path.name}")
        return True
    atom_path.write_text(new_text)
    print(f"  [OK] Updated Related block: {atom_path.name} ({len(related)} peers)")
    return True


# ── Index regeneration (navigation root) ─────────────────────────────────────

_INDEX_LINK_RE = re.compile(r"\[\[wiki/[a-z]{2,3}/([^\]\s|#]+)")


def regenerate_index(vault_path: Path, lang: str, vault_name: str, dry_run: bool) -> bool:
    """Rebuild `index/{lang}/index.md` listing every MOC + its atom count.

    The index is the entry point of the three-level navigation (index → MOC →
    atom). Re-running is cheap (~ms per lang) and idempotent — content only
    changes when the underlying MOCs change.
    """
    moc_dir = vault_path / "moc" / lang
    index_path = vault_path / "index" / lang / "index.md"

    rows = []
    if moc_dir.exists():
        for moc_path in sorted(moc_dir.glob("*.md")):
            topic = moc_path.stem
            text = moc_path.read_text(errors="replace")
            stems = set(_INDEX_LINK_RE.findall(text))
            rows.append((topic, len(stems)))

    lines = [f"# Vault Index — {vault_name} ({lang})", ""]
    if not rows:
        lines.append("_No MOCs yet. Run `/ingest` then `/ingest-queue` to populate._")
        lines.append("")
    else:
        lines.append("| Topic | Atoms |")
        lines.append("|-------|-------|")
        for topic, count in rows:
            lines.append(f"| [[moc/{lang}/{topic}]] | {count} |")
        lines.append("")
        lines.append(f"→ Read `moc/{lang}/{{topic}}.md` for the constituent atoms; "
                     "atoms cross-link via `## Related` blocks.")
        lines.append("")

    new_text = "\n".join(lines)
    old_text = index_path.read_text(errors="replace") if index_path.exists() else ""
    if new_text == old_text:
        return False
    if dry_run:
        print(f"  [DRY-RUN] Would regenerate index/{lang}/index.md ({len(rows)} MOCs)")
        return True
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(new_text)
    print(f"  [OK] Regenerated index/{lang}/index.md ({len(rows)} MOCs)")
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("atom", nargs="?", help="Atom stem (e.g. pricing--base-price)")
    p.add_argument("--lang", default=None, help="Language code (en, es, ...)")
    p.add_argument("--all", action="store_true", help="Backfill all atoms")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--vault", default=None, help="Vault path (default: $VAULT_PATH)")
    p.add_argument("--section", default=None, help="Insert under this MOC heading (e.g. 'Básicos')")
    p.add_argument("--no-related", action="store_true",
                   help="Skip atom→atom Related-block update (debug / fast mode)")
    p.add_argument("--no-index", action="store_true",
                   help="Skip index/{lang}/index.md regeneration")
    p.add_argument("--index-only", action="store_true",
                   help="Only regenerate index/{lang}/index.md (no atom/MOC writes)")
    args = p.parse_args()

    if not args.atom and not args.all and not args.index_only:
        p.print_help()
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig
    cfg = VaultConfig(args.vault)

    langs = [args.lang] if args.lang else cfg.languages

    if args.index_only:
        for lang in langs:
            regenerate_index(cfg.vault_path, lang, cfg.name, args.dry_run)
        return

    # Build BM25 index once per lang to avoid O(N²) cost in --all mode.
    vault_indexes: dict = {}
    if not args.no_related:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from retrieve import VaultIndex  # type: ignore
            for lang in langs:
                if (cfg.vault_path / "wiki" / lang).exists():
                    vault_indexes[lang] = VaultIndex(cfg.vault_path, lang)
        except ImportError:
            print("WARN: retrieve.py not importable — skipping atom→atom linking", file=sys.stderr)

    with_related = not args.no_related
    with_index = not args.no_index

    if args.all:
        total = 0
        for lang in langs:
            wiki_dir = cfg.vault_path / "wiki" / lang
            if not wiki_dir.exists():
                print(f"  wiki/{lang}/ not found — skipping")
                continue
            print(f"\nLinking [{lang}]...")
            # In --all mode, skip per-atom index regen — do it once at the end.
            for atom_path in sorted(wiki_dir.glob("*.md")):
                n = link_atom(atom_path.stem, lang, cfg.vault_path, args.dry_run,
                              args.section, vault_index=vault_indexes.get(lang),
                              with_related=with_related,
                              vault_name=cfg.name, with_index=False)
                total += n
            if with_index:
                regenerate_index(cfg.vault_path, lang, cfg.name, args.dry_run)
        print(f"\nTotal new links: {total}")
    else:
        stem = args.atom.removesuffix(".md")
        total = 0
        for lang in langs:
            n = link_atom(stem, lang, cfg.vault_path, args.dry_run, args.section,
                          vault_index=vault_indexes.get(lang),
                          with_related=with_related,
                          vault_name=cfg.name, with_index=with_index)
            total += n
        print(f"\nNew links added: {total}")


if __name__ == "__main__":
    main()
