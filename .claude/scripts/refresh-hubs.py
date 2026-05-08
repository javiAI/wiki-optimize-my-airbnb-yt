#!/usr/bin/env python3
"""
refresh-hubs.py — Drain hub enrichment queues and synthesize stub bodies.

For each slug in state/queue/{entity,comparison}-enrichment.txt:
  1. Find the matching hub file across enabled languages.
  2. Read every atom in the hub's `cited_atoms[]`.
  3. Invoke `claude -p` with a per-kind synthesis prompt to generate the body.
  4. Replace the stub body with the synthesis (preserves frontmatter; bumps
     `last_updated`).

Idempotent in the sense that re-running on an already-enriched hub re-synthesises
from the same atoms — output should be substantively the same. Drains the queue
files only on success.

Hub propagation to other enabled langs is NOT done here yet; the canonical
enriched hub stays in the lang where it was first detected. Cross-lang
propagation lives in propagate_atom.py (extension pending — Phase 6 follow-up).

Usage:
    python3 .claude/scripts/refresh-hubs.py --vault <path>
    python3 .claude/scripts/refresh-hubs.py --vault <path> --dry-run
    python3 .claude/scripts/refresh-hubs.py --vault <path> --kind entity
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / ".claude" / "scripts"))
from config import VaultConfig, kind_dir, wikilink_prefix  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from frontmatter import ATOM_FM_RE, CLAIM_RE, TYPE_RE  # noqa: E402
from llm_utils import DEFAULT_TIMEOUT, call_claude, strip_fences  # noqa: E402
TITLE_RE = re.compile(r"^title:\s*(.+?)$", re.MULTILINE)
KIND_RE = re.compile(r"^kind:\s*(\w+)", re.MULTILINE)
SUBJECTS_KIND_RE = re.compile(r"^subjects_kind:\s*(\w+)", re.MULTILINE)
SUBJECTS_RE = re.compile(r"^subjects:\s*\[(.*?)\]", re.MULTILINE)
CITED_ATOMS_RE = re.compile(r"^cited_atoms:\s*\[(.*?)\]", re.MULTILINE)
LAST_UPDATED_RE = re.compile(r"^last_updated:.*$", re.MULTILINE)

AUTO_GEN_MARKER = "<!-- AUTO-GENERATED — edits below this line will be overwritten by /refresh-hubs -->"


# ── Prompt builders ──────────────────────────────────────────────────────────

ENTITY_PROMPT = """You are enriching an entity hub page for a WikiForge wiki, in {lang}.

Synthesize a coherent multi-section markdown body about this entity from the atoms below. Each atom carries one falsifiable claim with a deep-link locator.

ENTITY:
  title: {title}
  kind: {kind}
  slug: {slug}
  lang: {lang}

CITED ATOMS ({n_atoms}):

{atoms_block}

OUTPUT REQUIREMENTS

1. Output the markdown BODY only — no frontmatter, no triple-dash fences.
2. Start with a one-paragraph identity: what this entity IS and why it matters in this corpus. Cite at least one atom with [[{wiki_prefix}/<atom-stem>]].
3. Then add sections matching the entity `kind`:
   - tool: ## What it does, ## Pricing model, ## Connection / integration, ## Key levers, ## Author's stance, ## Pitfalls
   - company: ## What it does, ## Position in the market, ## Author's stance
   - person: ## Background / role, ## Positions advocated, ## Body of work, ## Author's stance toward them
   - product: ## What it is, ## Use case, ## Pricing or access, ## Pitfalls
   - service: ## What it is, ## When it applies, ## Pricing or access, ## Author's stance
   - book / channel: ## What it is, ## Take
4. Every bullet that makes a claim MUST cite the supporting atom with [[{wiki_prefix}/<atom-stem>]]. No claim without a cite. Skip a section if no atom supports it.
5. End with a `## Sources` section listing each atom: `- [[{wiki_prefix}/<stem>]] — <claim short>`.
6. Write natively in `{lang}`. Brand names stay verbatim. No English borrowings if `{lang}` ≠ `en`.
7. Total length: 200–600 words excluding the Sources block.
8. Output the body directly — no JSON wrapper, no preamble, no closing remarks.
"""

COMPARISON_PROMPT = """You are enriching a comparison hub for a WikiForge wiki, in {lang}.

Synthesize a head-to-head decision page about these two subjects from the cited atoms.

COMPARISON:
  {a_title} vs {b_title}
  subjects_kind: {kind}
  lang: {lang}

CITED ATOMS ({n_atoms}):

{atoms_block}

OUTPUT REQUIREMENTS

1. Output the markdown BODY only — no frontmatter.
2. Two-sentence framing: what's the comparison axis, who would care. Cite at least one atom.
3. ## At a glance — a markdown table with 3–6 rows comparing both subjects on key dimensions (e.g. pricing model, customisation depth, integration). Every cell with a claim cites [[{wiki_prefix}/<stem>]]. No cell may carry a claim without a cite.
4. ## Per-dimension — one `### <Dimension>` subsection per table row, with prose comparing both subjects. Cites required.
5. ## Recommendation — decision-tree style, 2–4 lines: `- If X, pick {a_title}. <citation>` / `- If Y, pick {b_title}. <citation>`. If neither is a clean winner, name the contextual scope (when each applies).
6. ## Sources — list of all cited atoms with claim short.
7. Write natively in `{lang}`. Brand names verbatim.
8. Total length: 300–700 words excluding Sources.
9. Output the body directly.
"""


# ── Hub I/O ──────────────────────────────────────────────────────────────────

def parse_hub(stub_path: Path) -> tuple[str, str]:
    """Return (frontmatter_text, body_text). Raises if no frontmatter."""
    text = stub_path.read_text(errors="replace")
    m = ATOM_FM_RE.match(text)
    if not m:
        raise ValueError(f"Hub file missing frontmatter: {stub_path}")
    return m.group(1), m.group(2)


def fm_field(fm: str, regex: re.Pattern, default: str = "") -> str:
    m = regex.search(fm)
    return m.group(1).strip() if m else default


def parse_cited_atoms(fm: str) -> list[str]:
    m = CITED_ATOMS_RE.search(fm)
    if not m:
        return []
    return [a.strip() for a in m.group(1).split(",") if a.strip()]


def read_atom_summary(atom_path: Path) -> dict:
    """Return {stem, claim, body}, with claim from frontmatter and body raw."""
    text = atom_path.read_text(errors="replace")
    m = ATOM_FM_RE.match(text)
    if not m:
        return {"stem": atom_path.stem, "claim": "", "body": text}
    fm, body = m.group(1), m.group(2)
    claim_m = CLAIM_RE.search(fm)
    claim = claim_m.group(1).strip().strip('"') if claim_m else ""
    return {"stem": atom_path.stem, "claim": claim, "body": body.strip()}


def render_atoms_block(atom_summaries: list[dict], max_body_chars: int = 1500) -> str:
    """Render atoms as a block the LLM can read; trim long bodies for token budget."""
    blocks = []
    for a in atom_summaries:
        body = a["body"]
        if len(body) > max_body_chars:
            body = body[:max_body_chars].rstrip() + "\n[...]"
        blocks.append(f"### atom: {a['stem']}\nclaim: {a['claim']}\nbody:\n{body}")
    return "\n\n".join(blocks)


def call_claude_md(prompt: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Invoke `claude -p`, strip markdown fences."""
    return strip_fences(call_claude(prompt, timeout=timeout), "markdown", "md")


def write_enriched_hub(stub_path: Path, fm: str, body: str, today: str) -> None:
    """Replace the body, bump last_updated. Frontmatter otherwise preserved."""
    if LAST_UPDATED_RE.search(fm):
        fm = LAST_UPDATED_RE.sub(f"last_updated: {today}", fm)
    else:
        fm = fm.rstrip("\n") + f"\nlast_updated: {today}"
    full = f"---\n{fm}\n---\n\n{AUTO_GEN_MARKER}\n\n{body.strip()}\n"
    stub_path.write_text(full)


# ── Per-hub enrichment ───────────────────────────────────────────────────────

def enrich_entity(stub_path: Path, vault_path: Path, lang: str,
                  dry_run: bool, today: str) -> bool:
    fm, body = parse_hub(stub_path)
    if TYPE_RE.search(fm) is None or TYPE_RE.search(fm).group(1) != "entity":
        print(f"[refresh-hubs] WARN: not an entity hub: {stub_path}", file=sys.stderr)
        return False

    title = fm_field(fm, TITLE_RE)
    kind = fm_field(fm, KIND_RE, "tool")
    slug = stub_path.stem.removeprefix("entity--")
    cited = parse_cited_atoms(fm)

    if not cited:
        print(f"[refresh-hubs] {stub_path.name}: no cited_atoms — skipping")
        return False

    atom_summaries = []
    for stem in cited:
        atom_path = kind_dir(vault_path, "wiki", lang) / f"{stem}.md"
        if not atom_path.exists():
            print(f"[refresh-hubs] WARN: cited atom missing: {atom_path}", file=sys.stderr)
            continue
        atom_summaries.append(read_atom_summary(atom_path))

    if not atom_summaries:
        return False

    prompt = ENTITY_PROMPT.format(
        lang=lang, title=title, kind=kind, slug=slug,
        wiki_prefix=wikilink_prefix(vault_path, "wiki", lang),
        n_atoms=len(atom_summaries),
        atoms_block=render_atoms_block(atom_summaries),
    )

    if dry_run:
        print(f"[refresh-hubs] [DRY-RUN] would enrich entity hub: {stub_path.name} ({len(atom_summaries)} atoms)")
        return True

    print(f"[refresh-hubs] Enriching entity hub: {stub_path.name} ({len(atom_summaries)} atoms)")
    new_body = call_claude_md(prompt)
    if not new_body:
        print(f"[refresh-hubs] WARN: empty synthesis for {stub_path.name}", file=sys.stderr)
        return False
    write_enriched_hub(stub_path, fm, new_body, today)
    return True


def enrich_comparison(stub_path: Path, vault_path: Path, lang: str,
                      dry_run: bool, today: str) -> bool:
    fm, body = parse_hub(stub_path)
    if TYPE_RE.search(fm) is None or TYPE_RE.search(fm).group(1) != "comparison":
        print(f"[refresh-hubs] WARN: not a comparison hub: {stub_path}", file=sys.stderr)
        return False

    title = fm_field(fm, TITLE_RE)
    kind = fm_field(fm, SUBJECTS_KIND_RE, "tool")
    subjects_match = SUBJECTS_RE.search(fm)
    if subjects_match:
        subjects = [s.strip() for s in subjects_match.group(1).split(",") if s.strip()]
    else:
        subjects = []
    if len(subjects) < 2:
        print(f"[refresh-hubs] WARN: comparison missing subjects: {stub_path}", file=sys.stderr)
        return False
    a_slug, b_slug = subjects[0], subjects[1]
    a_title = a_slug.replace("-", " ").title()
    b_title = b_slug.replace("-", " ").title()
    if " vs " in title:
        parts = title.split(" vs ", 1)
        a_title, b_title = parts[0].strip(), parts[1].strip()

    cited = parse_cited_atoms(fm)
    if not cited:
        return False

    atom_summaries = []
    for stem in cited:
        atom_path = kind_dir(vault_path, "wiki", lang) / f"{stem}.md"
        if not atom_path.exists():
            continue
        atom_summaries.append(read_atom_summary(atom_path))
    if not atom_summaries:
        return False

    prompt = COMPARISON_PROMPT.format(
        lang=lang, a_title=a_title, b_title=b_title, kind=kind,
        wiki_prefix=wikilink_prefix(vault_path, "wiki", lang),
        n_atoms=len(atom_summaries),
        atoms_block=render_atoms_block(atom_summaries),
    )

    if dry_run:
        print(f"[refresh-hubs] [DRY-RUN] would enrich comparison: {stub_path.name} ({len(atom_summaries)} atoms)")
        return True

    print(f"[refresh-hubs] Enriching comparison: {stub_path.name} ({len(atom_summaries)} atoms)")
    new_body = call_claude_md(prompt)
    if not new_body:
        return False
    write_enriched_hub(stub_path, fm, new_body, today)
    return True


# ── Queue helpers ────────────────────────────────────────────────────────────

def read_queue(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()]


def find_hub_files(vault_path: Path, kind_prefix: str, slug: str, langs: list[str]) -> list[tuple[Path, str]]:
    """Return [(path, lang)] for every existing hub stub for this slug across langs."""
    out = []
    for lang in langs:
        p = kind_dir(vault_path, "wiki", lang) / f"{kind_prefix}--{slug}.md"
        if p.exists():
            out.append((p, lang))
    return out


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Vault data path (else resolved via $VAULT_NAME)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--kind", choices=["entity", "comparison", "all"], default="all")
    args = parser.parse_args()

    cfg = VaultConfig()
    vault_path = Path(args.vault).expanduser().resolve() if args.vault else cfg.vault_path
    enabled_langs = cfg.enabled_languages
    state_dir = cfg.state_dir()

    e_queue = state_dir / "queue" / "entity-enrichment.txt"
    c_queue = state_dir / "queue" / "comparison-enrichment.txt"

    e_slugs = read_queue(e_queue) if args.kind in ("entity", "all") else []
    c_slugs = read_queue(c_queue) if args.kind in ("comparison", "all") else []

    if not e_slugs and not c_slugs:
        print("[refresh-hubs] Hub queues empty — nothing to refresh.")
        return 0

    today = date.today().isoformat()
    n_enriched = 0
    n_failed = 0

    for slug in e_slugs:
        targets = find_hub_files(vault_path, "entity", slug, enabled_langs)
        if not targets:
            print(f"[refresh-hubs] WARN: no entity stub found for slug={slug}", file=sys.stderr)
            continue
        for stub_path, lang in targets:
            try:
                if enrich_entity(stub_path, vault_path, lang, args.dry_run, today):
                    n_enriched += 1
            except Exception as e:
                n_failed += 1
                print(f"[refresh-hubs] ERROR enriching {stub_path.name}: {e}", file=sys.stderr)

    for slug in c_slugs:
        targets = find_hub_files(vault_path, "comparison", slug, enabled_langs)
        if not targets:
            print(f"[refresh-hubs] WARN: no comparison stub found for slug={slug}", file=sys.stderr)
            continue
        for stub_path, lang in targets:
            try:
                if enrich_comparison(stub_path, vault_path, lang, args.dry_run, today):
                    n_enriched += 1
            except Exception as e:
                n_failed += 1
                print(f"[refresh-hubs] ERROR enriching {stub_path.name}: {e}", file=sys.stderr)

    if not args.dry_run and n_failed == 0:
        e_queue.write_text("")
        c_queue.write_text("")

    print(f"[refresh-hubs] {n_enriched} hub(s) enriched"
          + (f", {n_failed} failed" if n_failed else "")
          + (" (dry-run)" if args.dry_run else ""))
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
