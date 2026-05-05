#!/usr/bin/env python3
"""
propagate_atom.py — Re-atomize a canonical atom at the same locator in another language.

This is NOT a translation. The canonical atom acts as a semantic anchor — it
tells the LLM which atom to produce. The actual claim/body content is
synthesized from the target-language transcript at the same locator. The
excerpt is lifted verbatim from the target-language transcript via
extract_excerpt.py (no LLM call when target subtitles are available).

Output atom structure (per target lang):
  - locator, url, source_id, topics, conflicts_with, last_verified: copied from canonical
  - excerpt:    extract_excerpt.py if raw/{LANG}/{video}.md exists (excerpt_source: yt_manual|yt_auto)
                else LLM-translated from canonical excerpt    (excerpt_source: llm_fallback)
  - claim:      LLM-synthesized in target lang from target-lang transcript
  - body:       LLM-synthesized in target lang from target-lang transcript
  - propagated_from: <atomization_lang> (top-level frontmatter marker)

Usage:
  python3 .claude/scripts/propagate_atom.py <atom_stem> --to es
  python3 .claude/scripts/propagate_atom.py <atom_stem> --to es --from en --force
  python3 .claude/scripts/propagate_atom.py <atom_stem>           # propagate to all enabled - {from}

The --from lang is auto-detected from the atom's `lang` field if not given.
By default, only target langs that have raw/{LANG}/{video}.md available will
emit excerpts via the script path; the rest fall back to LLM-translated
excerpts (still synthesized claim/body).

Idempotent: if wiki/{TARGET}/{stem}.md exists, skip unless --force.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / ".claude" / "scripts"))
from config import VaultConfig  # noqa: E402
from extract_excerpt import extract_at_locator  # noqa: E402
from frontmatter import parse_frontmatter  # noqa: E402

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
DEFAULT_MAX_TURNS = "3"


# ── Frontmatter / source parsing ─────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
SOURCE_BLOCK_RE = re.compile(
    r"^- source_id:\s*(\S+)\s*\n"
    r"((?:    [^\n]*\n)+)",
    re.MULTILINE,
)


def _load_yaml(text: str) -> dict:
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        fm, _ = parse_frontmatter(text)
        return fm




def parse_atom(atom_text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(atom_text)
    if not m:
        raise ValueError("atom missing frontmatter")
    fm = _load_yaml(m.group(1))
    body = atom_text[m.end():]
    return fm, body


# ── Raw-file index (video_id → raw/{LANG}/{file}.md) ─────────────────────────

VIDEO_ID_RE = re.compile(r"^video_id:\s*(\S+)", re.MULTILINE)


def index_raw_files(raw_dir: Path) -> dict:
    """Map video_id → raw file path for one lang dir."""
    index: dict[str, Path] = {}
    if not raw_dir.exists():
        return index
    for path in sorted(raw_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = VIDEO_ID_RE.search(text)
        if not m:
            continue
        index[m.group(1)] = path
    return index


# ── Excerpt resolution ───────────────────────────────────────────────────────

def resolve_target_excerpt(
    source_id: str,
    locator: str,
    target_lang: str,
    raw_index: dict,
) -> tuple[Optional[str], str]:
    """Return (excerpt_text, excerpt_source).

    excerpt_source ∈ {yt_manual, yt_auto, llm_fallback, native_atomization}.
    Returns (None, "llm_fallback") when no target-lang transcript exists; the
    LLM is then expected to translate the canonical excerpt as fallback.
    """
    raw_file = raw_index.get(source_id)
    if raw_file is None:
        return None, "llm_fallback"

    text = raw_file.read_text(encoding="utf-8", errors="replace")
    sub_source = "yt_manual"
    m = re.search(r"^subtitle_source:\s*(\S+)", text, re.MULTILINE)
    if m:
        v = m.group(1).strip()
        sub_source = "yt_auto" if v == "auto" else "yt_manual"

    try:
        excerpt = extract_at_locator(raw_file, locator)
    except (FileNotFoundError, ValueError):
        return None, "llm_fallback"

    if not excerpt:
        return None, "llm_fallback"
    return excerpt, sub_source


# ── LLM call ─────────────────────────────────────────────────────────────────

PROPAGATE_PROMPT = """\
You are PROPAGATING (not translating) a wiki atom from {from_lang} to {to_lang}.

The canonical atom in {from_lang} is the source of truth for atom IDENTITY only:
  - same locator, same source_id, same topics, same conflicts_with, same links
  - "this atom" must remain the same atom across languages

Your job: re-express that atom NATIVELY in {to_lang}, drawing vocabulary,
phrasing, and idioms from the {to_lang} transcript at the locator. DO NOT
translate the canonical word-for-word. A bilingual professional reading the
{to_lang} transcript would produce this atom; that is your stance.

Rules:
  - Output ONLY a JSON object with keys "claim" and "body". No markdown
    fences, no commentary.
  - "claim": one falsifiable sentence in {to_lang}. Restates the same fact
    as the canonical, but in native {to_lang} phrasing.
  - "body": 80–250 words in {to_lang}, markdown allowed. Open with the
    claim restated, then supporting detail drawn from the transcript window.
    No filler ("Es importante destacar", "Como podemos observar").
  - Anglicisms: replace forbidden English terms per the table at the end of
    this prompt. Whitelisted terms (PriceLabs, Airbnb, WiFi, etc.) stay.
  - Numbers, percentages, proper nouns: copy verbatim from the canonical.

Inputs:

[CANONICAL ATOM — IDENTITY ANCHOR, do NOT translate verbatim]
```
{canonical_atom}
```

[TARGET-LANGUAGE TRANSCRIPT WINDOW — primary material for re-synthesis]
```
{target_window}
```

[ANGLICISM TABLE — replacements to apply in body]
{anglicism_block}

Now output the JSON object."""


def render_anglicism_block(target_lang: str) -> str:
    """Inline a compact anglicism table for non-English targets."""
    if target_lang == "en":
        return "(target is English — no anglicism check)"
    try:
        sys.path.insert(0, str(REPO_ROOT / ".claude" / "scripts"))
        from qa_lexicon import ANGLICISM_TABLE  # noqa: E402
    except ImportError:
        return "(no anglicism table available)"
    lines = [f"  {en} → {es}" for en, es in ANGLICISM_TABLE[:50]]
    return "\n".join(lines)


def call_llm_propagate(
    canonical_atom_text: str,
    target_window: str,
    from_lang: str,
    to_lang: str,
    timeout_sec: int = 180,
) -> dict:
    """Invoke `claude -p` with the propagate prompt, parse JSON output.

    Returns {claim, body, excerpt?} dict. May raise CalledProcessError on failure.
    """
    prompt = PROPAGATE_PROMPT.format(
        from_lang=from_lang,
        to_lang=to_lang,
        canonical_atom=canonical_atom_text.strip(),
        target_window=target_window.strip() or "(target-lang transcript unavailable — translate the canonical excerpt as fallback)",
        anglicism_block=render_anglicism_block(to_lang),
    )
    cmd = [CLAUDE_BIN, "-p", prompt, "--max-turns", DEFAULT_MAX_TURNS]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_sec, check=True
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"LLM call timed out after {timeout_sec}s")
    raw = result.stdout.strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM did not return valid JSON: {e}\nOutput head: {raw[:300]!r}")


# ── Atom rendering ───────────────────────────────────────────────────────────

def render_atom(
    fm: dict,
    body: str,
    target_lang: str,
    from_lang: str,
    target_excerpts: dict,
) -> str:
    """Render a propagated atom file.

    target_excerpts: {source_id: {"excerpt": str, "excerpt_source": str}}
    """
    today = date.today().isoformat()
    lines = ["---"]
    lines.append(f"lang: {target_lang}")
    lines.append(f"claim: \"{_yaml_escape(fm.get('claim', ''))}\"")
    topics = fm.get("topics", [])
    if isinstance(topics, str):
        topics = [t.strip() for t in topics.strip("[]").split(",") if t.strip()]
    lines.append("topics: [" + ", ".join(topics) + "]")
    lines.append(f"confidence: {fm.get('confidence', 'medium')}")
    lines.append(f"propagated_from: {from_lang}")

    lines.append("sources:")
    for src in fm.get("sources", []) or []:
        sid = src.get("source_id", "")
        loc = src.get("locator", "")
        url = src.get("url", "")
        meta = target_excerpts.get(sid, {})
        excerpt = meta.get("excerpt", src.get("excerpt", ""))
        excerpt_source = meta.get("excerpt_source", "llm_fallback")
        lines.append(f"  - source_id: {sid}")
        lines.append(f"    locator: \"{loc}\"")
        if url:
            lines.append(f"    url: \"{url}\"")
        lines.append(f"    excerpt: \"{_yaml_escape(excerpt)}\"")
        lines.append(f"    excerpt_source: {excerpt_source}")
        lines.append(f"    lang_origin: {from_lang}")

    conflicts = fm.get("conflicts_with", [])
    if isinstance(conflicts, str):
        conflicts = [c.strip() for c in conflicts.strip("[]").split(",") if c.strip()]
    lines.append("conflicts_with: [" + ", ".join(conflicts) + "]")
    lines.append(f"last_verified: {fm.get('last_verified', today)}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines) + "\n"


def _yaml_escape(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


# ── Orchestration ────────────────────────────────────────────────────────────

def propagate(
    cfg: VaultConfig,
    stem: str,
    from_lang: Optional[str],
    to_lang: str,
    force: bool = False,
    skip_llm: bool = False,
) -> Path:
    """Propagate one atom to one target lang. Returns the written path."""
    enabled = cfg.enabled_languages

    # Find canonical atom: explicit --from, else scan enabled langs
    atom_path: Optional[Path] = None
    if from_lang:
        cand = cfg.wiki_dir(from_lang) / f"{stem}.md"
        if cand.exists():
            atom_path = cand
    else:
        for cand_lang in enabled:
            cand = cfg.wiki_dir(cand_lang) / f"{stem}.md"
            if cand.exists():
                atom_path = cand
                from_lang = cand_lang
                break
    if atom_path is None:
        raise FileNotFoundError(f"canonical atom not found: {stem}.md (searched in wiki/{enabled})")
    if to_lang == from_lang:
        raise ValueError(f"--to and --from are the same lang: {to_lang}")

    target_path = cfg.wiki_dir(to_lang) / f"{stem}.md"
    if target_path.exists() and not force:
        print(f"SKIP (exists): {target_path}")
        return target_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    canonical_text = atom_path.read_text(encoding="utf-8")
    fm, canonical_body = parse_atom(canonical_text)

    raw_index = index_raw_files(cfg.raw_dir(to_lang))

    target_excerpts: dict = {}
    primary_target_window = ""
    for src in fm.get("sources", []) or []:
        sid = src.get("source_id", "")
        loc = src.get("locator", "")
        excerpt, source_kind = resolve_target_excerpt(sid, loc, to_lang, raw_index)
        target_excerpts[sid] = {
            "excerpt": excerpt or src.get("excerpt", ""),
            "excerpt_source": source_kind,
        }
        if not primary_target_window and excerpt:
            primary_target_window = excerpt

    if skip_llm:
        new_claim = fm.get("claim", "")
        new_body = canonical_body
    else:
        llm_out = call_llm_propagate(
            canonical_atom_text=canonical_text,
            target_window=primary_target_window,
            from_lang=from_lang,
            to_lang=to_lang,
        )
        new_claim = (llm_out.get("claim") or fm.get("claim", "")).strip()
        new_body = (llm_out.get("body") or canonical_body).strip()
        if "excerpt" in llm_out:
            for sid, meta in target_excerpts.items():
                if meta["excerpt_source"] == "llm_fallback":
                    meta["excerpt"] = llm_out["excerpt"]

    new_fm = dict(fm)
    new_fm["claim"] = new_claim
    rendered = render_atom(new_fm, new_body, to_lang, from_lang, target_excerpts)
    target_path.write_text(rendered, encoding="utf-8")
    print(f"OK propagated: {atom_path} → {target_path}")

    # The on-file-write.sh hook only fires for Claude Code's Write tool, not for
    # Python subprocess writes — so propagated atoms would otherwise never get
    # wired into MOCs/Related blocks until a manual `auto-link.py --all` run.
    # Invoke it inline so each propagation is self-contained.
    try:
        link_cmd = [
            sys.executable,
            str(REPO_ROOT / ".claude" / "scripts" / "auto-link.py"),
            stem,
            "--lang", to_lang,
            "--vault", cfg.name,
        ]
        subprocess.run(link_cmd, check=False, timeout=60)
    except Exception as e:
        print(f"WARN auto-link failed for {stem} ({to_lang}): {e}", file=sys.stderr)

    return target_path


def main():
    p = argparse.ArgumentParser(description="Propagate a canonical atom to other enabled languages")
    p.add_argument("stem", help="Atom stem (no .md), e.g. pricing--five-percent")
    p.add_argument("--from", dest="from_lang", default=None,
                   help="Source lang (default: auto-detect from wiki/{lang}/{stem}.md)")
    p.add_argument("--to", default=None,
                   help="Target lang (default: every enabled lang minus --from)")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing target file")
    p.add_argument("--skip-llm", action="store_true",
                   help="Don't invoke claude -p; copy canonical claim/body verbatim (debug only)")
    p.add_argument("--vault", default=None, help="Vault name or path (default: $VAULT_NAME)")
    args = p.parse_args()

    cfg = VaultConfig(args.vault)
    enabled = cfg.enabled_languages

    targets: list[str]
    if args.to:
        targets = [args.to]
    else:
        # Default: every enabled lang except the from_lang (resolved inside propagate())
        targets = list(enabled)

    rc = 0
    for to_lang in targets:
        if to_lang == args.from_lang:
            continue
        try:
            propagate(cfg, args.stem, args.from_lang, to_lang,
                      force=args.force, skip_llm=args.skip_llm)
        except Exception as e:
            print(f"FAIL {args.stem} → {to_lang}: {e}", file=sys.stderr)
            rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
