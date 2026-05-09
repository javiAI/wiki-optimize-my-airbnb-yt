---
name: propagate
description: |-
  Propagate one canonical atom to another enabled language by **re-atomizing at
  the same locator** — not by translating. The canonical atom is a semantic
  anchor (same locator, source_id, topics, conflicts_with); claim and body are
  re-synthesised in the target lang from the target-lang transcript window. The
  resulting atom carries `propagated_from: {from}` and an `excerpt_source` that
  reflects how the target-lang excerpt was obtained (verbatim subs vs. LLM
  fallback).
  Use when the user asks to "propagate an atom", "translate this atom" (legacy
  wording), "create the {lang} version of {stem}", or runs `/propagate`. Most
  propagations happen automatically via the `on-file-write` hook —
  invoke this skill manually only for inspection, repairs, or when
  `pipeline.auto_propagate: false`.
allowed-tools: Read, Write, Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/propagate_atom.py:*), Bash(python3 .claude/scripts/atom-qa.py:*), Bash(python3 .claude/scripts/extract_excerpt.py:*)
arguments:
  - name: stem
    description: "Atom stem (e.g. `pricing--allow-pets-expand-guest-pool`). Positional, required."
  - name: --from
    description: "Source lang (defaults to the lang of the canonical atom, auto-detected)."
  - name: --to
    description: "Target lang (defaults to the next enabled lang in `vault.yml.languages.enabled[]`)."
---

# /propagate — Atom propagation (re-atomization at locator)

## Mental model

This is **not a translation**. The canonical atom is the source of truth for atom **identity** only — same locator, same `source_id`, same topics, same `conflicts_with`, same MOC links. The actual content (`claim`, `body`, `excerpt`) is **re-synthesised** in the target lang using the target-lang transcript window as primary material. The canonical atom tells the LLM *which* atom to produce, not *what words* to translate.

A bilingual native of the target lang reading the target-lang transcript at the locator would produce this atom from scratch. That is the stance to write from.

## When this runs

- **Automatic** (preferred): the `on-file-write` hook fires `propagate_atom.py` for every other enabled lang after each canonical atom is written, when `vault.yml.pipeline.auto_propagate: true` and 2+ langs are enabled.
- **Manual** (this skill): run when the auto pipeline is off, when a propagation failed and needs a redo, or when you want to inspect the result before writing.

## Steps

0. **Resolve vault** (mandatory preamble):

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Sets `$VAULT_NAME` and `$VAULT_PATH`. If it exits non-zero, **STOP** and ask the user which vault to operate on.

1. **Read the canonical atom** at `$VAULT_PATH/wiki/{from}/{stem}.md`. Extract frontmatter: `claim`, `topics`, `confidence`, `sources[].source_id/locator/url`, `conflicts_with`, `last_verified`.

2. If `wiki/{to}/{stem}.md` already exists, **confirm overwrite** with the user before proceeding. Propagation is idempotent (same locator, same identity), but re-running will overwrite the prior synthesis.

3. **For each entry in `sources[]`**, lift the target-lang excerpt:

   - Resolve the target-lang raw file at `$VAULT_PATH/raw/{to}/{source}.md` (lookup by `source_id` ↔ `video_id` / generic `source_id` field in raw frontmatter).
   - **If found**: run `python3 .claude/scripts/extract_excerpt.py --raw-file <path> --locator <loc>` to lift the verbatim quote. Stamp `excerpt_source: yt_manual` (creator-authored subs) or `yt_auto` (auto-generated). For non-video source types, the excerpt-source vocabulary lives in the vault's `agents.md` "Excerpt source taxonomy" section.
   - **If not found**: stamp `excerpt_source: llm_fallback` and synthesise the excerpt in the target lang as part of the same LLM call (no verbatim source available).

4. **Build the target-lang atom**:

   ```yaml
   ---
   lang: {to}
   claim: <re-synthesised in {to} from the target-lang transcript window — same fact, native phrasing, never a calque>
   topics: <copied from canonical>
   confidence: <copied>
   conflicts_with: <copied>
   last_verified: <copied>
   propagated_from: {from}        # top-level marker — only on propagated atoms
   sources:
     - source_id: <copied verbatim>
       locator: <copied verbatim>
       url: <copied verbatim>
       excerpt: <from step 3>
       excerpt_source: yt_manual | yt_auto | llm_fallback
       lang_origin: {from}
   ---

   <body 80–250 words in {to}, opening with claim restated, drawing vocabulary
   and idioms from the target-lang transcript window>
   ```

5. **Write natively in `{to}`**, as a bilingual native of `{to}` would write for a monolingual reader of `{to}`. Vocabulary, register, idioms come from the target-lang transcript window — never word-for-word translation of the canonical body. Proper nouns (brand / product / place / person names) and universally-known technical acronyms (`API`, `URL`, `JSON`, `YAML`) stay verbatim. The vault's `agents.md` defines what counts as a proper noun and which acronyms are universal in the target domain.

6. **Write** `wiki/{to}/{stem}.md`. The `on-file-write` hook fires automatically (auto-link + qa) — do not run them manually unless the hook is disabled.

7. **Run QA**: `python3 .claude/scripts/atom-qa.py {stem} --lang {to}` — surface any violations.

## Automation path (script-driven)

For non-interactive propagation (this is what the `on-file-write` hook calls):

```bash
VAULT_NAME="$VAULT_NAME" python3 .claude/scripts/propagate_atom.py {stem} --from {from} --to {to}
```

The script orchestrates excerpt extraction + LLM re-synthesis + atom rendering. Use the skill version when you want to inspect the candidate atom before writing.

## Quality standard

The target-lang atom should read as if a native `{to}` speaker who watched the `{to}` transcript wrote it from scratch. Vocabulary, idioms, register all native. Numbers and proper nouns identical to canonical. Two readers — one of each lang — should not be able to call them translations of each other; both should read as the natural way to state the claim in their lang.

## Critical rules

- **Never word-for-word translate** the canonical body. Read the target-lang transcript window and write the atom from there.
- **Never invent claims** beyond the canonical's `claim`. Re-atomization is identity-preserving — same falsifiable fact, native phrasing.
- **Locator and `source_id` are immutable** — they identify the atom across langs. Copy them verbatim.
- `propagated_from` only ever appears on the propagated atom, never on the canonical.
