---
name: translate
description: Propagate one canonical atom to a target language by re-atomizing at the same locator. NOT a translation — re-synthesizes claim+body from the target-language transcript using the canonical atom only as a semantic anchor for atom identity.
allowed-tools: Read Write Bash(python3 .claude/scripts/propagate_atom.py) Bash(python3 .claude/scripts/atom-qa.py) Bash(python3 .claude/scripts/extract_excerpt.py)
---

# /translate — Atom Propagation (re-atomization at locator)

Usage: `/translate {stem} [from={lang}] [to={lang}]`

Defaults: `from` = the lang of the canonical atom (auto-detected from `wiki/*/{stem}.md`), `to` = next enabled lang.

## Mental model

This is **not** a translation. The canonical atom is the source of truth for atom **identity** only — same locator, same source_id, same topics, same `conflicts_with`, same MOC links. The actual content (`claim`, `body`, `excerpt`) is **re-synthesized** in the target language using the target-language transcript as primary material. The canonical atom is a semantic anchor that tells the LLM which atom to produce, not what words to translate.

A bilingual professional reading the target-language transcript at the locator would produce this atom. That is your stance.

## Steps

1. Read `wiki/{from}/{stem}.md` — extract frontmatter (claim, topics, confidence, sources[].source_id/locator/url, conflicts_with, last_verified).
2. If `wiki/{to}/{stem}.md` already exists → confirm overwrite with the user before proceeding.
3. For each source in `sources[]`:
   - Resolve `raw/{to}/{video}.md` (lookup by `source_id` → matches `video_id` field in raw frontmatter).
   - If found: run `python3 .claude/scripts/extract_excerpt.py --raw-file <path> --locator <loc>` to lift the verbatim target-language quote. Mark `excerpt_source: yt_manual` (manual subs) or `yt_auto` (auto-generated).
   - If not found: mark `excerpt_source: llm_fallback` and translate the canonical excerpt as part of the same LLM call.
4. Build the target-language atom:
   - `lang: {to}`
   - `claim:` re-synthesized in {to} from the target-lang transcript window. Same fact, native phrasing — not a calque of the canonical.
   - Same `topics`, `confidence`, `conflicts_with`, `last_verified` as canonical.
   - `propagated_from: {from}` (top-level marker).
   - For each source: `source_id`, `locator`, `url` copied verbatim; `excerpt` from step 3; `excerpt_source` and `lang_origin: {from}`.
   - `body:` 80-250 words in {to}, opening with claim restated, drawing vocabulary and idioms from the transcript window — never word-for-word translation of the canonical body.
5. Write natively in `{to}` from the target-lang transcript window. English borrowings (host, listing, fee, review, booking, amenity, rating, ranking, etc.) are forbidden — use the target-lang term. Brand names and standardised tech terms (PriceLabs, Wheelhouse, Airbnb, Booking, Vrbo, Superhost, WiFi, PMS, API, URL, JSON, YAML, SEO, ADR, RevPAR) stay verbatim.
6. Write `wiki/{to}/{stem}.md`. The `on-file-write` hook fires automatically (auto-link + qa).
7. Run `python3 .claude/scripts/atom-qa.py {stem} --lang {to}` — report any violations.

## Automation path

For non-interactive propagation (the on-file-write hook does this) use:

```bash
VAULT_NAME=<vault> python3 .claude/scripts/propagate_atom.py {stem} --from {from} --to {to}
```

The script orchestrates excerpt extraction + LLM re-synthesis + atom rendering. The skill version of this flow is for cases where Claude is in a session and wants to inspect the result before writing.

## Quality standard

The target-language atom should read as if a native {to} speaker who watched the {to} subtitle track wrote it from scratch. Vocabulary, idioms, register all native. Numbers and proper nouns identical to canonical. The atom's `claim` is provably the same fact as the canonical's, but two readers — one of each lang — would not call them translations of each other.
