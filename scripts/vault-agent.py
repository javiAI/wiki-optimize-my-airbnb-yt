#!/usr/bin/env python3
"""
vault-agent.py

Vault health audit: orphans, stale claims, index consistency, topic gaps,
missing translations, unresolved contradictions.

Writes meta/agent-report-YYYY-MM-DD.md.

Usage:
  python3 scripts/vault-agent.py
  python3 scripts/vault-agent.py --dry-run
  python3 scripts/vault-agent.py --incremental   # only check recently-changed files
  python3 scripts/vault-agent.py --stale-days 90
  python3 scripts/vault-agent.py --lang es            # audit only ES
  python3 scripts/vault-agent.py --lang es,en         # audit ES and EN only
  python3 scripts/vault-agent.py --since 2026-04-01   # only atoms modified since date
  python3 scripts/vault-agent.py --output json        # machine-readable stats
  python3 scripts/vault-agent.py --vault /path/to/vault
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

TOPICS_RE = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)
LAST_VERIFIED_RE = re.compile(r"^last_verified:\s*(\S+)", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[wiki/([^/\]]+)/([^\]#]+?)(?:#[^\]]*)?\]\]")
CONTRADICTIONS_HEADER_RE = re.compile(r"^## \[", re.MULTILINE)


def load_atoms(vault_path: Path, lang: str) -> dict:
    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        return {}
    atoms = {}
    for p in sorted(wiki_dir.glob("*.md")):
        text = p.read_text(errors="replace")
        m_topics = TOPICS_RE.search(text)
        m_lv = LAST_VERIFIED_RE.search(text)
        topics = [t.strip() for t in m_topics.group(1).split(",")] if m_topics else []
        last_verified = None
        if m_lv:
            try:
                last_verified = date.fromisoformat(m_lv.group(1))
            except ValueError:
                pass
        atoms[p.stem] = {"topics": topics, "last_verified": last_verified, "path": p}
    return atoms


def load_moc_citations(vault_path: Path, lang: str) -> set:
    cited = set()
    moc_dir = vault_path / "moc" / lang
    if not moc_dir.exists():
        return cited
    for p in sorted(moc_dir.glob("*.md")):
        text = p.read_text(errors="replace")
        for m in WIKILINK_RE.finditer(text):
            if m.group(1) == lang:
                cited.add(m.group(2))
    return cited


def check_orphans(atoms: dict, moc_citations: set) -> list:
    return [stem for stem in atoms if stem not in moc_citations]


def check_stale(atoms: dict, stale_days: int) -> list:
    cutoff = date.today() - timedelta(days=stale_days)
    return [
        stem for stem, info in atoms.items()
        if info["last_verified"] and info["last_verified"] < cutoff
    ]


def check_index_consistency(vault_path: Path, lang: str, atoms: dict) -> list:
    broken = []
    index_file = vault_path / "index" / lang / "index.md"
    if not index_file.exists():
        return broken
    text = index_file.read_text(errors="replace")
    for m in WIKILINK_RE.finditer(text):
        if m.group(1) == lang and m.group(2) not in atoms:
            broken.append(f"{m.group(2)} (in index/{lang}/index.md)")
    return broken


def check_topic_gaps(vault_path: Path, lang: str, atoms: dict) -> list:
    freq = Counter()
    for info in atoms.values():
        for t in info["topics"]:
            freq[t] += 1
    gaps = []
    moc_dir = vault_path / "moc" / lang
    for topic, count in sorted(freq.items(), key=lambda x: -x[1]):
        if count >= 3 and not (moc_dir / f"{topic}.md").exists():
            gaps.append((topic, count))
    return gaps


def check_missing_translations(vault_path: Path, primary: str, secondary: list) -> dict:
    """Find atoms in primary lang that are missing in any secondary lang."""
    primary_dir = vault_path / "wiki" / primary
    if not primary_dir.exists():
        return {}
    primary_stems = {p.stem for p in primary_dir.glob("*.md")}
    missing = {}
    for lang in secondary:
        lang_dir = vault_path / "wiki" / lang
        if not lang_dir.exists():
            missing[lang] = list(primary_stems)
            continue
        lang_stems = {p.stem for p in lang_dir.glob("*.md")}
        not_translated = sorted(primary_stems - lang_stems)
        if not_translated:
            missing[lang] = not_translated
    return missing


def check_unresolved_contradictions(vault_path: Path) -> int:
    f = vault_path / "meta" / "contradictions.md"
    if not f.exists():
        return 0
    return len(CONTRADICTIONS_HEADER_RE.findall(f.read_text(errors="replace")))


def ingest_recommendations(atoms: dict) -> list:
    freq = Counter()
    for info in atoms.values():
        for t in info["topics"]:
            freq[t] += 1
    return [(t, c) for t, c in sorted(freq.items(), key=lambda x: x[1]) if c <= 5][:5]


def build_report(vault_path: Path, cfg, stale_days: int, lang_filter: list = None, since: date = None) -> tuple[str, dict]:
    today = date.today().isoformat()
    primary = cfg.primary_language
    all_langs = cfg.languages
    secondary = cfg.secondary_languages

    # Apply language filter
    if lang_filter:
        all_langs = [l for l in all_langs if l in lang_filter]
        secondary = [l for l in secondary if l in lang_filter]

    # Per-language stats
    lang_data = {}
    for lang in all_langs:
        atoms = load_atoms(vault_path, lang)
        # Apply --since filter: only atoms modified after date
        if since:
            atoms = {
                stem: info for stem, info in atoms.items()
                if info["path"].stat().st_mtime >= since.toordinal() * 86400
            }
        moc_citations = load_moc_citations(vault_path, lang)
        orphans = check_orphans(atoms, moc_citations)
        stale = check_stale(atoms, stale_days)
        broken = check_index_consistency(vault_path, lang, atoms)
        gaps = check_topic_gaps(vault_path, lang, atoms)
        lang_data[lang] = {
            "atoms": atoms,
            "orphans": orphans,
            "stale": stale,
            "broken_index": broken,
            "gaps": gaps,
        }

    missing_translations = check_missing_translations(vault_path, primary, secondary)
    contradiction_count = check_unresolved_contradictions(vault_path)

    total_atoms = sum(len(d["atoms"]) for d in lang_data.values())
    total_orphans = sum(len(d["orphans"]) for d in lang_data.values())
    total_stale = sum(len(d["stale"]) for d in lang_data.values())
    total_gaps = sum(len(d["gaps"]) for d in lang_data.values())
    total_broken = sum(len(d["broken_index"]) for d in lang_data.values())
    total_missing = sum(len(v) for v in missing_translations.values())

    lines = [
        f"# Vault Health Report — {today}",
        "",
        "## Summary",
        f"- Languages: {', '.join(all_langs)} | Total atoms: {total_atoms}",
        f"- Orphans: {total_orphans} | Stale (>{stale_days}d): {total_stale} | Topic gaps: {total_gaps}",
        f"- Broken index links: {total_broken} | Missing translations: {total_missing} | Contradictions: {contradiction_count}",
        "",
    ]

    for lang in all_langs:
        d = lang_data[lang]
        atom_count = len(d["atoms"])
        moc_count = len(list((vault_path / "moc" / lang).glob("*.md"))) if (vault_path / "moc" / lang).exists() else 0
        lines += [f"### [{lang}] {atom_count} atoms | {moc_count} MOCs", ""]

        if d["orphans"]:
            lines.append(f"**Orphans** ({len(d['orphans'])}):")
            for stem in d["orphans"][:20]:
                lines.append(f"- [[wiki/{lang}/{stem}]]")
            if len(d["orphans"]) > 20:
                lines.append(f"- ... and {len(d['orphans']) - 20} more")
            lines.append("")

        if d["stale"]:
            lines.append(f"**Stale claims** ({len(d['stale'])}):")
            for stem in d["stale"][:10]:
                lv = d["atoms"][stem]["last_verified"]
                lines.append(f"- [[wiki/{lang}/{stem}]] (last verified {lv})")
            if len(d["stale"]) > 10:
                lines.append(f"- ... and {len(d['stale']) - 10} more")
            lines.append("")

        if d["broken_index"]:
            lines.append(f"**Broken index links** ({len(d['broken_index'])}):")
            for entry in d["broken_index"]:
                lines.append(f"- {entry}")
            lines.append("")

        if d["gaps"]:
            lines.append(f"**Topic gaps** (3+ atoms, no MOC):")
            for topic, count in d["gaps"]:
                lines.append(f"- `{topic}` — {count} atoms, no moc/{lang}/{topic}.md")
            lines.append("")

    if missing_translations:
        lines += ["## Missing Translations", ""]
        for lang, stems in sorted(missing_translations.items()):
            lines.append(f"**{primary} → {lang}**: {len(stems)} atoms missing")
            for stem in stems[:15]:
                lines.append(f"  - {stem}")
            if len(stems) > 15:
                lines.append(f"  - ... and {len(stems) - 15} more")
            lines.append("")

    # Ingest recommendations (primary lang only)
    recs = ingest_recommendations(lang_data.get(primary, {}).get("atoms", {}))
    if recs:
        lines += ["## Ingest Recommendations (underrepresented topics)", ""]
        for topic, count in recs:
            lines.append(f"- Consider ingesting 2-3 sources about `{topic}` (currently {count} atoms)")
        lines.append("")

    lines += [
        "## Generated by",
        f"`scripts/vault-agent.py` on {datetime.utcnow().isoformat()}Z",
    ]

    stats = {
        "orphans": total_orphans,
        "stale": total_stale,
        "gaps": total_gaps,
        "broken_index": total_broken,
        "missing_translations": total_missing,
        "contradiction_count": contradiction_count,
    }
    return "\n".join(lines), stats


def main():
    p = argparse.ArgumentParser(description="WikiForge vault health audit")
    p.add_argument("--dry-run", action="store_true", help="Print report without writing")
    p.add_argument("--incremental", action="store_true",
                   help="Only check atoms changed in git since last commit")
    p.add_argument("--stale-days", type=int, default=180)
    p.add_argument("--vault", default=None, help="Vault path (default: $VAULT_PATH)")
    p.add_argument("--lang", default=None, help="Comma-separated language codes to audit (e.g. es or es,en)")
    p.add_argument("--since", default=None, help="Only audit atoms modified since this date (YYYY-MM-DD)")
    p.add_argument("--output", default="text", choices=["text", "json"], help="Output format")
    args = p.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig
    cfg = VaultConfig(args.vault)
    vault_path = cfg.vault_path

    lang_filter = [l.strip() for l in args.lang.split(",")] if args.lang else None
    since_date = date.fromisoformat(args.since) if args.since else None

    report_text, stats = build_report(vault_path, cfg, args.stale_days, lang_filter, since_date)

    if args.output == "json":
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    today = date.today().isoformat()
    out_path = vault_path / "meta" / f"agent-report-{today}.md"

    if args.dry_run:
        print(report_text)
        print(f"\n[DRY-RUN] Would write: {out_path}")
    else:
        out_path.write_text(report_text)
        print(f"[OK] Report: {out_path}")
        print(f"Stats: orphans={stats['orphans']}, stale={stats['stale']}, "
              f"missing_translations={stats['missing_translations']}, "
              f"contradictions={stats['contradiction_count']}")


if __name__ == "__main__":
    main()
