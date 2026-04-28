"""
conflict-resolver.py — Source priority scoring and conflict detection.

For each pair of atoms in the same topic that make conflicting claims,
computes which atom is the primary recommendation using a priority hierarchy:

Priority criteria (applied in order — first that decides wins):
  1. temporal_supersession  — newer source overrides older (published date + recency score)
  2. contextual_scope       — both valid under different conditions (no winner, describe both)
  3. confidence_tier        — high > medium > low
  4. authority_tier         — channel_authority high > medium > low
  5. specificity_tier       — more specific claim (has numbers, explicit conditions) wins

Source score formula (for recency + popularity weighting):
  score = 0.40·recency + 0.30·views_norm + 0.20·specificity + 0.10·authority

Usage:
    python3 scripts/conflict-resolver.py --atom pricing--base-price-definition --lang es
    python3 scripts/conflict-resolver.py --scan --lang es         # scan all atoms for conflicts
    python3 scripts/conflict-resolver.py --scan --write-meta      # write to meta/contradictions.md
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional


# ── Source priority weights ───────────────────────────────────────────────────

SCORE_WEIGHTS = {
    "recency":     0.40,
    "views":       0.30,
    "specificity": 0.20,
    "authority":   0.10,
}

AUTHORITY_SCORES = {"high": 1.0, "medium": 0.6, "low": 0.3}
CONFIDENCE_SCORES = {"high": 1.0, "medium": 0.6, "low": 0.3}


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end]
    body = text[end + 3:].strip()

    fm: dict = {}
    sources_list = []
    in_sources = False
    current_source: dict = {}

    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("sources:"):
            in_sources = True
            continue

        if in_sources:
            if stripped.startswith("- source_id:"):
                if current_source:
                    sources_list.append(current_source)
                current_source = {"source_id": stripped.split(":", 1)[1].strip()}
            elif current_source and ":" in stripped:
                k, v = stripped.split(":", 1)
                current_source[k.strip()] = v.strip().strip('"')
            if not line.startswith(" ") and ":" in stripped and not stripped.startswith("-"):
                in_sources = False
                if current_source:
                    sources_list.append(current_source)
                    current_source = {}
                k, v = stripped.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
            continue

        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k, v = k.strip(), v.strip().strip('"')
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
            fm[k] = v

    if current_source:
        sources_list.append(current_source)
    if sources_list:
        fm["sources"] = sources_list
    return fm, body


def source_recency_score(published: Optional[str]) -> float:
    """Score 0-1 based on publication date. Newer = higher."""
    if not published:
        return 0.5
    try:
        pub = date.fromisoformat(published[:10])
        today = date.today()
        age_days = (today - pub).days
        # Sigmoid decay: 2 years old → ~0.5, 5 years → ~0.2
        return max(0.0, 1.0 - age_days / 1825)
    except ValueError:
        return 0.5


def source_views_score(views: Optional[str]) -> float:
    """Normalize views to 0-1. Assume 1M views = top score."""
    try:
        v = int(str(views).replace(",", "").replace(".", ""))
        return min(1.0, v / 1_000_000)
    except (TypeError, ValueError):
        return 0.3


def specificity_score(claim: str) -> float:
    """Higher score for claims with numbers, percentages, explicit conditions."""
    score = 0.3
    if re.search(r'\d+%', claim):
        score += 0.3
    if re.search(r'\d+', claim):
        score += 0.2
    if any(word in claim.lower() for word in ["si ", "cuando ", "if ", "when ", "solo ", "only "]):
        score += 0.2
    return min(1.0, score)


def compute_source_score(source: dict, claim: str = "") -> float:
    """Compute priority score for a source entry."""
    recency = source_recency_score(source.get("published"))
    views = source_views_score(source.get("views"))
    spec = specificity_score(claim)
    authority = AUTHORITY_SCORES.get(source.get("channel_authority", "medium"), 0.6)

    return (
        SCORE_WEIGHTS["recency"] * recency +
        SCORE_WEIGHTS["views"] * views +
        SCORE_WEIGHTS["specificity"] * spec +
        SCORE_WEIGHTS["authority"] * authority
    )


def atom_priority_score(fm: dict) -> float:
    """Compute overall priority score for an atom based on its best source."""
    sources = fm.get("sources", [])
    claim = fm.get("claim", "")
    if not sources:
        return 0.0
    # Best source score (atom may cite multiple sources)
    return max(compute_source_score(s, claim) for s in sources)


def detect_conflict_severity(claim_a: str, claim_b: str, topic: str) -> str:
    """
    Heuristic severity classification.
    HIGH: same topic, explicit numerical contradiction (one overrides other)
    MEDIUM: same topic, different strategy/approach
    LOW: related topic, different context
    """
    a = claim_a.lower()
    b = claim_b.lower()

    # Look for explicit negation or contradiction signals
    contradiction_signals = ["no ", "nunca ", "never ", "evitar ", "avoid ", "no es ", "is not "]
    has_negation = any(s in a or s in b for s in contradiction_signals)

    # Look for numeric conflict (both have numbers but different values)
    nums_a = re.findall(r'\d+(?:\.\d+)?%?', a)
    nums_b = re.findall(r'\d+(?:\.\d+)?%?', b)
    numeric_conflict = bool(nums_a and nums_b and nums_a != nums_b)

    if has_negation or numeric_conflict:
        return "HIGH"
    return "MEDIUM"


def resolve_conflict(atom_a: dict, atom_b: dict, stem_a: str, stem_b: str) -> dict:
    """
    Apply priority hierarchy to determine primary atom.
    Returns resolution dict with criterion, primary, and rationale.
    """
    fm_a, fm_b = atom_a["fm"], atom_b["fm"]
    score_a = atom_priority_score(fm_a)
    score_b = atom_priority_score(fm_b)
    claim_a = fm_a.get("claim", "")
    claim_b = fm_b.get("claim", "")

    # Criterion 1: temporal_supersession (score delta > 0.15 = meaningful recency gap)
    if abs(score_a - score_b) >= 0.15:
        primary = stem_a if score_a > score_b else stem_b
        secondary = stem_b if score_a > score_b else stem_a
        return {
            "resolution_criterion": "temporal_supersession",
            "primary": primary,
            "secondary": secondary,
            "rationale": f"{primary} has higher source score ({max(score_a, score_b):.2f} vs {min(score_a, score_b):.2f})",
            "note": f"Use {primary} as current recommendation; {secondary} provides historical context",
        }

    # Criterion 2: confidence_tier
    conf_a = CONFIDENCE_SCORES.get(fm_a.get("confidence", "medium"), 0.6)
    conf_b = CONFIDENCE_SCORES.get(fm_b.get("confidence", "medium"), 0.6)
    if conf_a != conf_b:
        primary = stem_a if conf_a > conf_b else stem_b
        secondary = stem_b if conf_a > conf_b else stem_a
        return {
            "resolution_criterion": "confidence_tier",
            "primary": primary,
            "secondary": secondary,
            "rationale": f"{primary} has higher confidence ({fm_a.get('confidence')} vs {fm_b.get('confidence')})",
            "note": f"Prefer {primary}; verify {secondary} source",
        }

    # Criterion 3: specificity_tier
    spec_a = specificity_score(claim_a)
    spec_b = specificity_score(claim_b)
    if abs(spec_a - spec_b) >= 0.2:
        primary = stem_a if spec_a > spec_b else stem_b
        secondary = stem_b if spec_a > spec_b else stem_a
        return {
            "resolution_criterion": "specificity_tier",
            "primary": primary,
            "secondary": secondary,
            "rationale": f"{primary} claim is more specific (numbers/conditions)",
            "note": f"Both may apply; {primary} has more actionable prescription",
        }

    # No clear winner → contextual scope
    return {
        "resolution_criterion": "contextual_scope",
        "primary": None,
        "secondary": None,
        "rationale": "Claims apply under different conditions; no universal winner",
        "note": f"Surface both {stem_a} and {stem_b} with their respective conditions",
    }


def load_atom(path: Path) -> Optional[dict]:
    try:
        text = path.read_text(errors="replace")
        fm, body = _parse_frontmatter(text)
        return {"fm": fm, "body": body, "path": str(path)}
    except Exception:
        return None


def scan_topic_conflicts(vault_path: Path, lang: str, topic: str) -> list[dict]:
    """Find conflict pairs within a topic by checking conflicts_with fields."""
    wiki_dir = vault_path / "wiki" / lang
    conflicts = []
    topic_atoms = {}

    for p in wiki_dir.glob(f"{topic}--*.md"):
        atom = load_atom(p)
        if atom:
            topic_atoms[p.stem] = atom

    # Check declared conflicts_with
    for stem, atom in topic_atoms.items():
        conflicts_with = atom["fm"].get("conflicts_with", [])
        if isinstance(conflicts_with, str):
            conflicts_with = [conflicts_with] if conflicts_with else []
        for other_stem in conflicts_with:
            if other_stem in topic_atoms and stem < other_stem:  # avoid duplicates
                severity = detect_conflict_severity(
                    atom["fm"].get("claim", ""),
                    topic_atoms[other_stem]["fm"].get("claim", ""),
                    topic,
                )
                resolution = resolve_conflict(atom, topic_atoms[other_stem], stem, other_stem)
                conflicts.append({
                    "atom_a": stem,
                    "atom_b": other_stem,
                    "topic": topic,
                    "severity": severity,
                    "claim_a": atom["fm"].get("claim", "")[:120],
                    "claim_b": topic_atoms[other_stem]["fm"].get("claim", "")[:120],
                    "score_a": round(atom_priority_score(atom["fm"]), 3),
                    "score_b": round(atom_priority_score(topic_atoms[other_stem]["fm"]), 3),
                    **resolution,
                })

    return conflicts


def write_contradictions_entry(vault_path: Path, conflict: dict) -> None:
    """Append a new undocumented conflict to meta/contradictions.md."""
    f = vault_path / "meta" / "contradictions.md"
    today = date.today().isoformat()
    entry = f"""
## [{conflict['atom_a']} vs {conflict['atom_b']}] {today}
- **Topic**: {conflict['topic']}
- **Severity**: {conflict['severity']}
- **Claim A**: {conflict['claim_a']}
- **Claim B**: {conflict['claim_b']}
- **Score A**: {conflict['score_a']} | **Score B**: {conflict['score_b']}
- **Resolution criterion**: {conflict['resolution_criterion']}
- **Primary**: {conflict.get('primary') or 'contextual (no universal winner)'}
- **Note**: {conflict.get('note', '')}
"""
    with open(f, "a") as fp:
        fp.write(entry)


def main():
    p = argparse.ArgumentParser(description="WikiForge conflict resolver")
    p.add_argument("--atom", default=None, help="Check conflicts for one atom stem")
    p.add_argument("--lang", default=None)
    p.add_argument("--scan", action="store_true", help="Scan all topics for conflicts")
    p.add_argument("--write-meta", action="store_true", help="Write new conflicts to meta/contradictions.md")
    p.add_argument("--vault", default=None)
    p.add_argument("--output", default="text", choices=["text", "json"])
    args = p.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig
    cfg = VaultConfig(args.vault)
    vault_path = cfg.vault_path
    lang = args.lang or cfg.primary_language

    all_conflicts = []

    if args.scan:
        wiki_dir = vault_path / "wiki" / lang
        topics = set()
        for p_file in wiki_dir.glob("*.md"):
            parts = p_file.stem.split("--", 1)
            if len(parts) == 2:
                topics.add(parts[0])
        for topic in sorted(topics):
            conflicts = scan_topic_conflicts(vault_path, lang, topic)
            all_conflicts.extend(conflicts)

    elif args.atom:
        # Load the atom and check its conflicts_with list
        stem = args.atom.removesuffix(".md")
        atom_path = vault_path / "wiki" / lang / f"{stem}.md"
        if not atom_path.exists():
            print(f"ERROR: atom not found: {atom_path}", file=sys.stderr)
            sys.exit(1)
        atom = load_atom(atom_path)
        if atom:
            topic = stem.split("--", 1)[0]
            all_conflicts = scan_topic_conflicts(vault_path, lang, topic)
            all_conflicts = [c for c in all_conflicts if stem in (c["atom_a"], c["atom_b"])]
    else:
        p.print_help()
        sys.exit(1)

    if args.output == "json":
        print(json.dumps(all_conflicts, ensure_ascii=False, indent=2))
    else:
        if not all_conflicts:
            print(f"No conflicts found [{lang}]")
        else:
            print(f"\nConflicts found: {len(all_conflicts)} [{lang}]\n")
            for c in all_conflicts:
                print(f"  [{c['severity']}] {c['atom_a']} vs {c['atom_b']}")
                print(f"    Criterion: {c['resolution_criterion']}")
                print(f"    Primary: {c.get('primary') or 'contextual'}")
                print(f"    {c.get('note', '')}")
                print()

    if args.write_meta and all_conflicts:
        # Load existing contradictions to avoid duplicates
        existing = (vault_path / "meta" / "contradictions.md").read_text(errors="replace")
        new_count = 0
        for c in all_conflicts:
            key = f"{c['atom_a']} vs {c['atom_b']}"
            if key not in existing:
                write_contradictions_entry(vault_path, c)
                new_count += 1
        print(f"\nWrote {new_count} new conflict(s) to meta/contradictions.md")


if __name__ == "__main__":
    main()
