#!/usr/bin/env python3
"""
entity-detect.py — register + queue entity hubs from atom mentions.

Pattern-matches an atom's claim+body against `meta/entities-registry.yaml`
aliases. For each registry hit:
  - Creates wiki/{lang}/entity--{slug}.md stub if absent (frontmatter +
    "Stub — pending enrichment" prose, so wikilinks resolve immediately).
  - If the stub already exists, appends the atom stem to `cited_atoms[]`,
    bumps `source_count` and `last_seen` / `last_updated`.
  - Queues the slug in state/queue/entity-enrichment.txt (dedup), to be
    drained by /refresh-hubs at ingest-batch close.

Capitalised multi-word phrases NOT in the registry are written to
state/queue/entity-candidates.txt for user curation — no stub is created
since the registry hasn't declared a `kind` yet. The user adds the entry
to the registry, after which subsequent ingests stub & enrich normally.

Idempotent: re-running on the same atom does not duplicate citations or
queue entries.

Usage:
    python3 .claude/scripts/entity-detect.py <atom-stem> --lang <lang> --vault <vault_path>
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

# Capitalised multi-word noun-phrase candidates we always suppress: days,
# months (en + es), and a handful of generic phrases that look like entities
# but aren't. Real false-positives discovered in practice get added here.
NP_STOPWORDS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    "new year", "black friday", "smart pricing",
}

# Words that mean a phrase starting with them is structural, not an entity
LEADING_NOISE = {
    "the", "this", "that", "these", "those", "a", "an",
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "este", "esta", "estos", "estas",
}


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
        aliases = meta.get("aliases") or []
        if not aliases:
            aliases = [title]
        out[slug] = {
            "kind": meta.get("kind", "tool"),
            "title": title,
            "aliases": aliases,
        }
    return out


def detect_registry_hits(text: str, registry: dict) -> dict:
    """Return {slug: meta} for every registry entity whose alias appears in text."""
    hits = {}
    for slug, meta in registry.items():
        for alias in meta["aliases"]:
            if not alias:
                continue
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                hits[slug] = meta
                break
    return hits


def detect_noun_phrase_candidates(text: str, registry: dict) -> set:
    """Return capitalised multi-word phrases (lowercased) NOT in the registry.

    Filtered by: stopwords, leading-noise words, and known aliases. Surfaces
    candidates for user curation in state/queue/entity-candidates.txt.
    """
    cleaned = re.sub(r"\[\[[^\]]+\]\]", "", text)
    cleaned = re.sub(r"https?://\S+", "", cleaned)

    np_re = re.compile(r"\b([A-Z][\w]*(?:\s+[A-Z][\w]*){1,3})\b")

    known = set()
    for meta in registry.values():
        known.add(meta["title"].lower())
        for a in meta["aliases"] or []:
            known.add(a.lower())

    candidates = set()
    for m in np_re.finditer(cleaned):
        phrase = m.group(1).strip()
        low = phrase.lower()
        if low in NP_STOPWORDS or low in known:
            continue
        first = low.split()[0]
        if first in LEADING_NOISE:
            continue
        candidates.add(low)
    return candidates


def build_entity_stub(slug: str, meta: dict, lang: str, atom_stem: str, today: str) -> str:
    aliases_csv = ", ".join(f'"{a}"' for a in meta["aliases"]) if meta["aliases"] else ""
    return (
        f"---\n"
        f"type: entity\n"
        f"title: {meta['title']}\n"
        f"slug: {slug}\n"
        f"kind: {meta['kind']}\n"
        f"aliases: [{aliases_csv}]\n"
        f"lang: {lang}\n"
        f"source_count: 1\n"
        f"first_seen: {today}\n"
        f"last_seen: {today}\n"
        f"last_updated: {today}\n"
        f"cited_atoms: [{atom_stem}]\n"
        f"---\n"
        f"\n"
        f"# {meta['title']}\n"
        f"\n"
        f"> Stub — pending enrichment. The atom that triggered this stub is in\n"
        f"> `cited_atoms[]`. Run `/refresh-hubs` (or wait for the\n"
        f"> on-ingest-batch-close hook) to enrich.\n"
    )


def enrich_existing_stub(stub_path: Path, atom_stem: str, today: str) -> bool:
    """Append atom_stem to cited_atoms[], bump counters & dates. Returns True on change."""
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
    """Append item to a newline-delimited queue file, deduplicating against existing lines."""
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    if queue_path.exists():
        existing = set(line.strip() for line in queue_path.read_text(errors="replace").splitlines())
        if item in existing:
            return
    with queue_path.open("a") as f:
        f.write(f"{item}\n")


def resolve_state_dir() -> Path:
    """Resolve state dir via VaultConfig (uses $VAULT_NAME env or active vault)."""
    from config import VaultConfig
    return VaultConfig().state_dir()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stem", help="Atom stem (file name without .md)")
    parser.add_argument("--lang", required=True)
    parser.add_argument("--vault", required=True, help="Vault data path")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser().resolve()
    wiki_dir = kind_dir(vault_path, "wiki", args.lang)
    atom_path = wiki_dir / f"{args.stem}.md"
    if not atom_path.exists():
        print(f"[entity-detect] WARN: atom not found: {atom_path}", file=sys.stderr)
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
    hits = detect_registry_hits(body_text, registry)

    state_dir = resolve_state_dir()
    enrich_queue = state_dir / "queue" / "entity-enrichment.txt"
    candidates_queue = state_dir / "queue" / "entity-candidates.txt"

    today = datetime.date.today().isoformat()
    n_stubs = n_enriched = 0

    for slug, meta in hits.items():
        stub_path = wiki_dir / f"entity--{slug}.md"
        if stub_path.exists():
            if enrich_existing_stub(stub_path, args.stem, today):
                n_enriched += 1
        else:
            stub_path.parent.mkdir(parents=True, exist_ok=True)
            stub_path.write_text(build_entity_stub(slug, meta, args.lang, args.stem, today))
            n_stubs += 1
        append_to_queue(enrich_queue, slug)

    candidates = detect_noun_phrase_candidates(body_text, registry)
    for cand in candidates:
        append_to_queue(candidates_queue, cand)

    if n_stubs or n_enriched or candidates:
        bits = []
        if n_stubs: bits.append(f"{n_stubs} stub(s)")
        if n_enriched: bits.append(f"{n_enriched} enriched")
        if candidates: bits.append(f"{len(candidates)} candidate(s)")
        print(f"[entity-detect] {args.stem} [{args.lang}]: " + ", ".join(bits))

    return 0


if __name__ == "__main__":
    sys.exit(main())
