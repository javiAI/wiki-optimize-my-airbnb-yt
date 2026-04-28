#!/usr/bin/env python3
"""
vault-agent.py

Vault health audit: orphans, stale claims, index consistency, topic gaps,
unresolved contradictions. Writes meta/agent-report-YYYY-MM-DD.md + appends log.md.

Usage:
  python3 scripts/vault-agent.py
  python3 scripts/vault-agent.py --dry-run   # print report without writing
  python3 scripts/vault-agent.py --stale-days 90
"""

import argparse
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_PATH = Path(os.environ.get(
    "VAULT_PATH",
    "/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt"
))

NOTES_DIR = VAULT_PATH / "notes"
MOC_DIR = VAULT_PATH / "MOC"
INDEX_FILE = VAULT_PATH / "index.md"
INDEX_DIR = VAULT_PATH / "index"
META_DIR = VAULT_PATH / "meta"
CONTRADICTIONS_FILE = META_DIR / "contradictions.md"
LOG_FILE = VAULT_PATH / "log.md"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
TOPICS_RE = re.compile(r"^topics:\s*\[(.+?)\]", re.MULTILINE)
LAST_VERIFIED_RE = re.compile(r"^last_verified:\s*(\S+)", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[notes/([^\]]+?)(?:#[^\]]*)?\]\]")
CONTRADICTIONS_HEADER_RE = re.compile(r"^## \[", re.MULTILINE)


def load_atoms():
    """Return dict of stem -> {topics, last_verified, path}."""
    atoms = {}
    for p in sorted(NOTES_DIR.glob("*.md")):
        text = p.read_text(errors="replace")
        m_topics = TOPICS_RE.search(text)
        m_lv = LAST_VERIFIED_RE.search(text)
        topics = []
        if m_topics:
            topics = [t.strip() for t in m_topics.group(1).split(",")]
        last_verified = None
        if m_lv:
            try:
                last_verified = date.fromisoformat(m_lv.group(1))
            except ValueError:
                pass
        atoms[p.stem] = {"topics": topics, "last_verified": last_verified, "path": p}
    return atoms


def load_moc_citations():
    """Return set of atom stems cited in any MOC file."""
    cited = set()
    for p in sorted(MOC_DIR.glob("*.md")):
        text = p.read_text(errors="replace")
        for m in WIKILINK_RE.finditer(text):
            cited.add(m.group(1))
    return cited


def check_orphans(atoms, moc_citations):
    return [stem for stem in atoms if stem not in moc_citations]


def check_stale(atoms, stale_days):
    cutoff = date.today() - timedelta(days=stale_days)
    return [
        stem for stem, info in atoms.items()
        if info["last_verified"] and info["last_verified"] < cutoff
    ]


def check_index_consistency(atoms):
    """Find [[notes/stem]] links in index files that don't exist in notes/."""
    broken = []
    sources = [INDEX_FILE] + list(INDEX_DIR.glob("*.md")) if INDEX_DIR.is_dir() else [INDEX_FILE]
    for idx in sources:
        if not idx.exists():
            continue
        text = idx.read_text(errors="replace")
        for m in WIKILINK_RE.finditer(text):
            stem = m.group(1)
            if stem not in atoms:
                broken.append(f"{stem} (in {idx.name})")
    return broken


def check_topic_gaps(atoms):
    """Topics with 3+ atoms but no MOC/<topic>.md."""
    from collections import Counter
    freq = Counter()
    for info in atoms.values():
        for t in info["topics"]:
            freq[t] += 1
    gaps = []
    for topic, count in sorted(freq.items(), key=lambda x: -x[1]):
        if count >= 3 and not (MOC_DIR / f"{topic}.md").exists():
            gaps.append((topic, count))
    return gaps


def check_unresolved_contradictions():
    """Count contradiction entries in meta/contradictions.md."""
    if not CONTRADICTIONS_FILE.exists():
        return 0
    text = CONTRADICTIONS_FILE.read_text(errors="replace")
    return len(CONTRADICTIONS_HEADER_RE.findall(text))


def ingest_recommendations(atoms):
    """Topics with the fewest atoms — candidates for new ingests."""
    from collections import Counter
    freq = Counter()
    for info in atoms.values():
        for t in info["topics"]:
            freq[t] += 1
    all_topics = sorted(freq.items(), key=lambda x: x[1])
    return [(t, c) for t, c in all_topics if c <= 5][:5]


def build_report(atoms, stale_days):
    moc_citations = load_moc_citations()
    orphans = check_orphans(atoms, moc_citations)
    stale = check_stale(atoms, stale_days)
    broken_index = check_index_consistency(atoms)
    gaps = check_topic_gaps(atoms)
    contradiction_count = check_unresolved_contradictions()
    ingest_recs = ingest_recommendations(atoms)

    today = date.today().isoformat()
    moc_count = len(list(MOC_DIR.glob("*.md"))) if MOC_DIR.exists() else 0
    source_dirs = VAULT_PATH / "sources"
    source_count = len(list(source_dirs.glob("*.md"))) if source_dirs.exists() else 0

    lines = [
        f"# Vault Health Report — {today}",
        "",
        "## Summary",
        f"- Atoms: {len(atoms)} | MOCs: {moc_count} | Sources: {source_count}",
        f"- Orphans: {len(orphans)} | Stale (>{stale_days}d): {len(stale)} | Topic gaps: {len(gaps)}",
        f"- Broken index links: {len(broken_index)} | Contradiction entries: {contradiction_count}",
        "",
    ]

    if orphans:
        lines += ["## Orphan Atoms (not cited in any MOC)", ""]
        for stem in orphans:
            lines.append(f"- [[notes/{stem}]]")
        lines.append("")

    if stale:
        lines += [f"## Stale Claims (last_verified > {stale_days} days)", ""]
        for stem in stale:
            lv = atoms[stem]["last_verified"]
            lines.append(f"- [[notes/{stem}]] (last verified {lv})")
        lines.append("")

    if broken_index:
        lines += ["## Broken Index Links", ""]
        for entry in broken_index:
            lines.append(f"- [[notes/{entry}]] (missing)")
        lines.append("")

    if gaps:
        lines += ["## Topic Gaps (3+ atoms, no MOC)", ""]
        for topic, count in gaps:
            lines.append(f"- `{topic}` — {count} atoms, no MOC/{topic}.md")
        lines.append("")

    if ingest_recs:
        lines += ["## Ingest Recommendations (underrepresented topics)", ""]
        for topic, count in ingest_recs:
            lines.append(f"- Consider ingesting 2-3 videos about `{topic}` (currently {count} atoms)")
        lines.append("")

    lines += [
        "## Generated by",
        f"`scripts/vault-agent.py` on {datetime.utcnow().isoformat()}Z",
    ]

    return "\n".join(lines), {
        "orphans": len(orphans),
        "stale": len(stale),
        "gaps": len(gaps),
        "contradiction_count": contradiction_count,
        "broken_index": len(broken_index),
    }


def write_report(report_text, dry_run):
    today = date.today().isoformat()
    out_path = META_DIR / f"agent-report-{today}.md"
    if dry_run:
        print(report_text)
        print(f"\n[DRY-RUN] Would write: {out_path}")
    else:
        out_path.write_text(report_text)
        print(f"[OK] Report: {out_path}")
    return out_path


def append_log(stats, report_path, dry_run):
    today = date.today().isoformat()
    entry = (
        f"\n## [{today}] agent-report | Vault health check\n"
        f"- Generated: meta/{report_path.name}\n"
        f"- Findings: {stats['orphans']} orphans, {stats['stale']} stale, "
        f"{stats['gaps']} topic gaps, {stats['broken_index']} broken index links, "
        f"{stats['contradiction_count']} contradiction entries\n"
        f"- User action required: review recommendations in meta/{report_path.name}\n"
    )
    if dry_run:
        print(f"\n[DRY-RUN] Would append to log.md:\n{entry}")
    else:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
        print(f"[OK] Appended to {LOG_FILE}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                   help="Print report without writing files")
    p.add_argument("--stale-days", type=int, default=180,
                   help="Days threshold for stale claims (default: 180)")
    args = p.parse_args()

    if not NOTES_DIR.exists():
        print(f"ERROR: notes/ not found at {NOTES_DIR}", file=sys.stderr)
        sys.exit(1)

    atoms = load_atoms()
    report_text, stats = build_report(atoms, args.stale_days)
    report_path = write_report(report_text, args.dry_run)
    if not args.dry_run:
        append_log(stats, report_path, args.dry_run)
    else:
        print(f"\nStats: {stats}")


if __name__ == "__main__":
    main()
