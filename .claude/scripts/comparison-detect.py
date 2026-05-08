#!/usr/bin/env python3
"""
comparison-detect.py — register + queue comparison hubs from atom mentions.

Triggers a comparison hub when either:
  - 2+ entities of the same `kind` co-occur in the atom (registry hits), or
  - explicit comparison cues ("vs", "versus", "compared to", "alternative to",
    "frente a", "en lugar de", "comparado con") AND 2+ registry entities
    are mentioned in the atom (any kind).

For each unique pair (alpha-sorted on slug), writes the stub
wiki/{lang}/comparison--{a-slug}-vs-{b-slug}.md if absent, or appends the
atom stem to its `cited_atoms[]` if it already exists. Slug is queued in
state/queue/comparison-enrichment.txt (drained by /refresh-hubs).

Idempotent: re-running on the same atom does not duplicate citations or
queue entries. Hub files (`type: entity|comparison`) are skipped.

Usage:
    python3 .claude/scripts/comparison-detect.py <atom-stem> --lang <lang> --vault <vault_path>
"""

import argparse
import datetime
import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import kind_dir  # noqa: E402
from frontmatter import ATOM_FM_RE, CLAIM_RE, TYPE_RE  # noqa: E402

CUE_RE = re.compile(
    r"\b(vs\.?|versus|compared to|alternative to|frente a|en lugar de|comparado con)\b",
    re.IGNORECASE,
)


def load_registry(vault_path: Path) -> dict:
    """Returns {slug: {kind, title, aliases}} from meta/entities-registry.yaml."""
    p = vault_path / "meta" / "entities-registry.yaml"
    if not p.exists():
        return {}
    from config import _load_yaml
    data = _load_yaml(p) or {}
    entities = data.get("entities") or {}
    out = {}
    for slug, meta in entities.items():
        meta = meta or {}
        title = meta.get("title") or slug.replace("-", " ").title()
        aliases = meta.get("aliases") or [title]
        out[slug] = {
            "kind": meta.get("kind", "tool"),
            "title": title,
            "aliases": aliases,
        }
    return out


def detect_hits(text: str, registry: dict) -> dict:
    hits = {}
    for slug, meta in registry.items():
        for alias in meta["aliases"]:
            if not alias:
                continue
            if re.search(r"\b" + re.escape(alias) + r"\b", text, re.IGNORECASE):
                hits[slug] = meta
                break
    return hits


def build_comparison_stub(a_slug: str, a_meta: dict, b_slug: str, b_meta: dict,
                          lang: str, atom_stem: str, today: str) -> str:
    return (
        f"---\n"
        f"type: comparison\n"
        f"title: {a_meta['title']} vs {b_meta['title']}\n"
        f"slug: {a_slug}-vs-{b_slug}\n"
        f"subjects: [{a_slug}, {b_slug}]\n"
        f"subjects_kind: {a_meta['kind']}\n"
        f"lang: {lang}\n"
        f"source_count: 1\n"
        f"first_seen: {today}\n"
        f"last_seen: {today}\n"
        f"last_updated: {today}\n"
        f"cited_atoms: [{atom_stem}]\n"
        f"---\n"
        f"\n"
        f"# {a_meta['title']} vs {b_meta['title']}\n"
        f"\n"
        f"> Stub — pending enrichment. The atom that triggered this stub is in\n"
        f"> `cited_atoms[]`. Run `/refresh-hubs` (or wait for the\n"
        f"> on-ingest-batch-close hook) to enrich.\n"
    )


def enrich_existing_stub(stub_path: Path, atom_stem: str, today: str) -> bool:
    text = stub_path.read_text(errors="replace")
    m = ATOM_FM_RE.match(text)
    if not m:
        return False
    fm, body = m.group(1), m.group(2)

    cited_re = re.compile(r"^cited_atoms:\s*\[(.*?)\]\s*$", re.MULTILINE)
    cm = cited_re.search(fm)
    if cm:
        existing = [a.strip() for a in cm.group(1).split(",") if a.strip()]
        if atom_stem in existing:
            return False
        existing.append(atom_stem)
        fm = cited_re.sub(f"cited_atoms: [{', '.join(existing)}]", fm)
    else:
        fm = fm.rstrip("\n") + f"\ncited_atoms: [{atom_stem}]"

    sc_re = re.compile(r"^source_count:\s*(\d+)\s*$", re.MULTILINE)
    sm = sc_re.search(fm)
    if sm:
        fm = sc_re.sub(f"source_count: {int(sm.group(1)) + 1}", fm)

    fm = re.sub(r"^last_seen:.*$", f"last_seen: {today}", fm, flags=re.MULTILINE)
    fm = re.sub(r"^last_updated:.*$", f"last_updated: {today}", fm, flags=re.MULTILINE)

    stub_path.write_text(f"---\n{fm}\n---\n{body}")
    return True


def append_to_queue(queue_path: Path, item: str) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    if queue_path.exists():
        existing = set(line.strip() for line in queue_path.read_text(errors="replace").splitlines())
        if item in existing:
            return
    with queue_path.open("a") as f:
        f.write(f"{item}\n")


def resolve_state_dir() -> Path:
    from config import VaultConfig
    return VaultConfig().state_dir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stem")
    parser.add_argument("--lang", required=True)
    parser.add_argument("--vault", required=True, help="Vault data path")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser().resolve()
    wiki_dir = kind_dir(vault_path, "wiki", args.lang)
    atom_path = wiki_dir / f"{args.stem}.md"
    if not atom_path.exists():
        print(f"[comparison-detect] WARN: atom not found: {atom_path}", file=sys.stderr)
        return 0

    text = atom_path.read_text(errors="replace")
    type_match = TYPE_RE.search(text)
    if type_match and type_match.group(1) in ("entity", "comparison"):
        return 0

    fm_match = ATOM_FM_RE.match(text)
    if fm_match:
        claim_m = CLAIM_RE.search(fm_match.group(1))
        claim = claim_m.group(1) if claim_m else ""
        body_text = f"{claim}\n{fm_match.group(2)}"
    else:
        body_text = text

    registry = load_registry(vault_path)
    hits = detect_hits(body_text, registry)
    if len(hits) < 2:
        return 0

    has_cue = CUE_RE.search(body_text) is not None

    by_kind: dict = {}
    for slug, meta in hits.items():
        by_kind.setdefault(meta["kind"], []).append((slug, meta))

    pairs: list = []
    for members in by_kind.values():
        if len(members) >= 2:
            for a, b in itertools.combinations(sorted(members, key=lambda x: x[0]), 2):
                pairs.append((a, b))

    if has_cue and not pairs:
        sorted_hits = sorted(hits.items(), key=lambda x: x[0])
        for a, b in itertools.combinations(sorted_hits, 2):
            pairs.append((a, b))

    if not pairs:
        return 0

    state_dir = resolve_state_dir()
    queue = state_dir / "queue" / "comparison-enrichment.txt"
    today = datetime.date.today().isoformat()

    n_stubs = n_enriched = 0
    seen_slugs = set()
    for (a_slug, a_meta), (b_slug, b_meta) in pairs:
        if a_slug > b_slug:
            a_slug, a_meta, b_slug, b_meta = b_slug, b_meta, a_slug, a_meta
        comp_slug = f"{a_slug}-vs-{b_slug}"
        if comp_slug in seen_slugs:
            continue
        seen_slugs.add(comp_slug)

        stub_path = wiki_dir / f"comparison--{comp_slug}.md"
        if stub_path.exists():
            if enrich_existing_stub(stub_path, args.stem, today):
                n_enriched += 1
        else:
            stub_path.parent.mkdir(parents=True, exist_ok=True)
            stub_path.write_text(
                build_comparison_stub(a_slug, a_meta, b_slug, b_meta, args.lang, args.stem, today)
            )
            n_stubs += 1
        append_to_queue(queue, comp_slug)

    if n_stubs or n_enriched:
        bits = []
        if n_stubs: bits.append(f"{n_stubs} stub(s)")
        if n_enriched: bits.append(f"{n_enriched} enriched")
        print(f"[comparison-detect] {args.stem} [{args.lang}]: " + ", ".join(bits))

    return 0


if __name__ == "__main__":
    sys.exit(main())
