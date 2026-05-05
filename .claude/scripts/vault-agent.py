#!/usr/bin/env python3
"""
vault-agent.py

Vault health audit: orphans, stale claims, index consistency, topic gaps,
missing translations, unresolved contradictions.

Writes meta/agent-report-YYYY-MM-DD.md.

Usage:
  python3 .claude/scripts/vault-agent.py
  python3 .claude/scripts/vault-agent.py --dry-run
  python3 .claude/scripts/vault-agent.py --incremental   # only check recently-changed files
  python3 .claude/scripts/vault-agent.py --stale-days 90
  python3 .claude/scripts/vault-agent.py --lang es            # audit only ES
  python3 .claude/scripts/vault-agent.py --lang es,en         # audit ES and EN only
  python3 .claude/scripts/vault-agent.py --since 2026-04-01   # only atoms modified since date
  python3 .claude/scripts/vault-agent.py --output json        # machine-readable stats
  python3 .claude/scripts/vault-agent.py --vault /path/to/vault
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


def load_atom_citations(vault_path: Path, lang: str) -> dict:
    """Map stem → set of stems that link TO it from atom bodies (inbound atom-links).

    Counts any `[[wiki/{lang}/peer]]` reference inside any other atom's file as
    an inbound link, including Related sections written by auto-link.py.
    """
    inbound: dict = {}
    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        return inbound
    for p in sorted(wiki_dir.glob("*.md")):
        text = p.read_text(errors="replace")
        for m in WIKILINK_RE.finditer(text):
            if m.group(1) == lang and m.group(2) != p.stem:
                inbound.setdefault(m.group(2), set()).add(p.stem)
    return inbound


def check_atom_orphans(atoms: dict, atom_inbound: dict) -> list:
    """Atoms that no other atom links to. With auto-link.py emitting Related
    sections, an orphan here means the atom is genuinely isolated in BM25 space —
    or auto-link hasn't run yet."""
    return [stem for stem in atoms if not atom_inbound.get(stem)]


# Keep these in sync with auto-link.py's RELATED_TOP_K / RELATED_MIN_SCORE_RATIO
# so the cross-ref check measures coverage of the same recommendations.
_CROSSREF_TOP_K = 5
_CROSSREF_MIN_RATIO = 0.3


def check_missing_cross_refs(vault_path: Path, lang: str, atoms: dict) -> list:
    """Pairs (atom, peer, score) where BM25 ranks `peer` in the top-K for `atom`
    but `atom` does not currently link to `peer`. Coverage gap for auto-link.py.
    """
    if not atoms:
        return []
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from retrieve import VaultIndex  # type: ignore
    except ImportError:
        return []
    index = VaultIndex(vault_path, lang)

    outbound: dict = {}
    for stem, info in atoms.items():
        text = info["path"].read_text(errors="replace")
        outs = set()
        for m in WIKILINK_RE.finditer(text):
            if m.group(1) == lang:
                outs.add(m.group(2))
        outbound[stem] = outs

    missing: list = []
    for stem in atoms:
        atom_obj = index.atoms.get(stem) or {}
        claim = (atom_obj.get("fm") or {}).get("claim", "")
        topics_q = " ".join(atom_obj.get("topics", []))
        if not (claim or topics_q):
            continue
        ranked = index.score(f"{claim} {topics_q}", _CROSSREF_TOP_K + 1)
        ranked = [(score, s) for score, s in ranked if s != stem]
        if not ranked:
            continue
        top_score = ranked[0][0]
        threshold = top_score * _CROSSREF_MIN_RATIO
        for score, peer in ranked[:_CROSSREF_TOP_K]:
            if score < threshold:
                break
            if peer not in outbound.get(stem, set()):
                missing.append((stem, peer, round(score, 2)))
    return missing


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


def check_missing_propagations(vault_path: Path, enabled_langs: list) -> dict:
    """Find atoms that exist in some enabled lang but are missing in others.

    With per-source atomization (no global primary), the canonical atom for a
    stem may live in any enabled lang. The expectation is: if a stem exists in
    *any* `wiki/{lang}/`, it should exist in *every* enabled lang. Returns
    {target_lang: [missing_stems_for_that_lang]}, sorted, and only including
    langs that actually have gaps.
    """
    if not enabled_langs:
        return {}
    stems_by_lang = {}
    union_stems = set()
    for lang in enabled_langs:
        lang_dir = vault_path / "wiki" / lang
        stems = {p.stem for p in lang_dir.glob("*.md")} if lang_dir.exists() else set()
        stems_by_lang[lang] = stems
        union_stems |= stems
    missing = {}
    for lang in enabled_langs:
        gap = sorted(union_stems - stems_by_lang[lang])
        if gap:
            missing[lang] = gap
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


def query_topic_demand(vault_path: Path, langs: list) -> Counter:
    """Count topic mentions in cached queries/. Signals what users are asking about.

    A topic that appears in many queries but has few atoms is a high-priority
    candidate for new source ingestion (high demand, low coverage).
    """
    demand = Counter()
    for lang in langs:
        qdir = vault_path / "queries" / lang
        if not qdir.exists():
            continue
        for q in qdir.glob("*.md"):
            try:
                text = q.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not text.startswith("---"):
                continue
            end = text.find("---", 3)
            if end == -1:
                continue
            for line in text[3:end].splitlines():
                s = line.strip()
                if s.startswith("topics:"):
                    raw = s.split(":", 1)[1].strip()
                    for t in raw.strip("[]").split(","):
                        t = t.strip().strip('"\'')
                        if t:
                            demand[t] += 1
                    break
    return demand


def suggest_sources(atoms_by_lang: dict, query_demand: Counter) -> list:
    """Combine atom coverage + query demand → ranked source suggestions.

    Returns [(topic, atom_count, query_mentions, demand_ratio), ...] sorted by
    demand_ratio descending. demand_ratio = (query_mentions + 1) / (atom_count + 1)
    — high ratio means people ask about this more than the corpus covers it.
    """
    coverage = Counter()
    for lang_atoms in atoms_by_lang.values():
        for info in lang_atoms.values():
            for t in info["topics"]:
                coverage[t] += 1
    all_topics = set(coverage) | set(query_demand)
    rows = []
    for t in all_topics:
        atoms_n = coverage.get(t, 0)
        queries_n = query_demand.get(t, 0)
        ratio = (queries_n + 1) / (atoms_n + 1)
        rows.append((t, atoms_n, queries_n, round(ratio, 2)))
    # Filter: only topics where demand ratio > 1.0 (queries exceed atoms) OR
    # coverage is dangerously thin (<=2 atoms with at least 1 query mention).
    filtered = [
        r for r in rows
        if r[3] > 1.0 or (r[1] <= 2 and r[2] >= 1)
    ]
    filtered.sort(key=lambda x: -x[3])
    return filtered[:10]


def collect_qa_findings(vault_path: Path) -> dict:
    """Aggregate qa-reports/*.json into totals by violation type and top noisy atoms."""
    qa_dir = vault_path / "meta" / "qa-reports"
    if not qa_dir.exists():
        return {}
    by_type = Counter()
    by_atom = Counter()
    report_count = 0
    for report_file in sorted(qa_dir.glob("*.json")):
        try:
            data = json.loads(report_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        report_count += 1
        atom_key = f"{data.get('atom', report_file.stem)} [{data.get('lang', '?')}]"
        for v in data.get("violations", []):
            by_type[v.get("type", "unknown")] += 1
            by_atom[atom_key] += 1
    if report_count == 0:
        return {}
    return {
        "report_count": report_count,
        "by_type": dict(by_type.most_common()),
        "top_atoms": by_atom.most_common(5),
        "total_violations": sum(by_type.values()),
    }


def build_report(vault_path: Path, cfg, stale_days: int, lang_filter: list = None, since: date = None) -> tuple[str, dict]:
    today = date.today().isoformat()
    all_langs = list(cfg.enabled_languages)

    # Apply language filter
    if lang_filter:
        all_langs = [l for l in all_langs if l in lang_filter]

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
        atom_inbound = load_atom_citations(vault_path, lang)
        orphans = check_orphans(atoms, moc_citations)
        atom_orphans = check_atom_orphans(atoms, atom_inbound)
        stale = check_stale(atoms, stale_days)
        broken = check_index_consistency(vault_path, lang, atoms)
        gaps = check_topic_gaps(vault_path, lang, atoms)
        missing_xrefs = check_missing_cross_refs(vault_path, lang, atoms)
        lang_data[lang] = {
            "atoms": atoms,
            "orphans": orphans,
            "atom_orphans": atom_orphans,
            "stale": stale,
            "broken_index": broken,
            "gaps": gaps,
            "missing_xrefs": missing_xrefs,
        }

    missing_propagations = check_missing_propagations(vault_path, all_langs)
    contradiction_count = check_unresolved_contradictions(vault_path)

    total_atoms = sum(len(d["atoms"]) for d in lang_data.values())
    total_orphans = sum(len(d["orphans"]) for d in lang_data.values())
    total_atom_orphans = sum(len(d["atom_orphans"]) for d in lang_data.values())
    total_stale = sum(len(d["stale"]) for d in lang_data.values())
    total_gaps = sum(len(d["gaps"]) for d in lang_data.values())
    total_broken = sum(len(d["broken_index"]) for d in lang_data.values())
    total_missing = sum(len(v) for v in missing_propagations.values())
    total_missing_xrefs = sum(len(d["missing_xrefs"]) for d in lang_data.values())

    lines = [
        f"# Vault Health Report — {today}",
        "",
        "## Summary",
        f"- Languages: {', '.join(all_langs)} | Total atoms: {total_atoms}",
        f"- MOC orphans: {total_orphans} | Atom orphans: {total_atom_orphans} | Stale (>{stale_days}d): {total_stale} | Topic gaps: {total_gaps}",
        f"- Broken index links: {total_broken} | Missing propagations: {total_missing} | Missing cross-refs: {total_missing_xrefs} | Contradictions: {contradiction_count}",
        "",
    ]

    for lang in all_langs:
        d = lang_data[lang]
        atom_count = len(d["atoms"])
        moc_count = len(list((vault_path / "moc" / lang).glob("*.md"))) if (vault_path / "moc" / lang).exists() else 0
        lines += [f"### [{lang}] {atom_count} atoms | {moc_count} MOCs", ""]

        if d["orphans"]:
            lines.append(f"**MOC orphans** ({len(d['orphans'])}) — atom not listed in any moc/{lang}/:")
            for stem in d["orphans"][:20]:
                lines.append(f"- [[wiki/{lang}/{stem}]]")
            if len(d["orphans"]) > 20:
                lines.append(f"- ... and {len(d['orphans']) - 20} more")
            lines.append("")

        if d["atom_orphans"]:
            lines.append(f"**Atom orphans** ({len(d['atom_orphans'])}) — no inbound links from other atoms:")
            for stem in d["atom_orphans"][:20]:
                lines.append(f"- [[wiki/{lang}/{stem}]]")
            if len(d["atom_orphans"]) > 20:
                lines.append(f"- ... and {len(d['atom_orphans']) - 20} more")
            lines.append("")

        if d["missing_xrefs"]:
            lines.append(f"**Missing cross-refs** ({len(d['missing_xrefs'])}) — high-similarity peers not linked. Run `auto-link.py --all` to fix:")
            for atom_stem, peer, score in d["missing_xrefs"][:15]:
                lines.append(f"- {atom_stem} → {peer} (score {score})")
            if len(d["missing_xrefs"]) > 15:
                lines.append(f"- ... and {len(d['missing_xrefs']) - 15} more")
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

    if missing_propagations:
        lines += ["## Missing Propagations", ""]
        lines.append("Atoms that exist in some enabled lang but not in others. "
                     "Each gap should be filled by `propagate_atom.py` (re-atomize at locator using "
                     "target-lang transcript).")
        lines.append("")
        for lang, stems in sorted(missing_propagations.items()):
            lines.append(f"**Missing in `{lang}`** ({len(stems)}):")
            for stem in stems[:15]:
                lines.append(f"  - {stem}")
            if len(stems) > 15:
                lines.append(f"  - ... and {len(stems) - 15} more")
            lines.append("")

    qa_findings = collect_qa_findings(vault_path)
    if qa_findings:
        lines += [
            "## QA Findings",
            "",
            f"- Atoms with open reports: {qa_findings['report_count']}",
            f"- Total violations: {qa_findings['total_violations']}",
            "",
            "**By type:**",
        ]
        for vtype, count in qa_findings["by_type"].items():
            lines.append(f"- `{vtype}`: {count}")
        lines.append("")
        if qa_findings["top_atoms"]:
            lines.append("**Top atoms by violation count:**")
            for atom_key, count in qa_findings["top_atoms"]:
                lines.append(f"- {atom_key}: {count}")
            lines.append("")

    # Ingest recommendations: aggregate topic frequencies across all enabled langs
    # so the rec is independent of any "primary" notion.
    aggregated = {}
    for d in lang_data.values():
        for stem, info in d["atoms"].items():
            aggregated.setdefault(stem, info)
    recs = ingest_recommendations(aggregated)
    if recs:
        lines += ["## Ingest Recommendations (underrepresented topics)", ""]
        for topic, count in recs:
            lines.append(f"- Consider ingesting 2-3 sources about `{topic}` (currently {count} atoms)")
        lines.append("")

    # Demand-driven source suggestions: where do user queries outpace coverage?
    # Cross-references atom topics × cached query topics. Independent of /qa
    # findings — answers "what should we ingest next?" rather than "what's broken?"
    atoms_by_lang = {lang: d["atoms"] for lang, d in lang_data.items()}
    query_demand = query_topic_demand(vault_path, all_langs)
    suggestions = suggest_sources(atoms_by_lang, query_demand) if query_demand else []
    if suggestions:
        lines += [
            "## Suggested New Sources (demand vs coverage)",
            "",
            "Topics where cached queries mention them more than the atom corpus covers. "
            "High `demand_ratio` = ingest more sources here. Use the `/suggest-sources` "
            "skill to turn these into concrete YouTube/web search queries.",
            "",
            "| topic | atoms | queries | demand_ratio |",
            "|---|---|---|---|",
        ]
        for topic, atoms_n, queries_n, ratio in suggestions:
            lines.append(f"| `{topic}` | {atoms_n} | {queries_n} | {ratio} |")
        lines.append("")

    lines += [
        "## Generated by",
        f"`.claude/scripts/vault-agent.py` on {datetime.utcnow().isoformat()}Z",
    ]

    stats = {
        "orphans": total_orphans,
        "atom_orphans": total_atom_orphans,
        "stale": total_stale,
        "gaps": total_gaps,
        "broken_index": total_broken,
        "missing_propagations": total_missing,
        "missing_cross_refs": total_missing_xrefs,
        "contradiction_count": contradiction_count,
        "qa_reports": qa_findings.get("report_count", 0),
        "qa_violations": qa_findings.get("total_violations", 0),
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
    reports_dir = vault_path / "meta" / "agent-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / f"agent-report-{today}.md"

    if args.dry_run:
        print(report_text)
        print(f"\n[DRY-RUN] Would write: {out_path}")
    else:
        out_path.write_text(report_text)
        print(f"[OK] Report: {out_path}")
        print(f"Stats: orphans={stats['orphans']}, stale={stats['stale']}, "
              f"missing_propagations={stats['missing_propagations']}, "
              f"contradictions={stats['contradiction_count']}")


if __name__ == "__main__":
    main()
