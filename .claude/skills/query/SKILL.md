---
name: query
description: |-
  Run a query against the vault and produce a cited, regime-aware response.
  Auto-detects the response language from the question itself (chars + stopwords);
  falls back to `.claude/state/wikiforge.yaml#active_lang`, then the active vault's
  `enabled[0]`. Retrieves the top atoms (and any matching entity / comparison
  hubs) via BM25, drafts in regime A / B / C per `meta/RESPONSE_TEMPLATES.md`,
  applies the pre-output checklist from `CLAUDE.md`, and saves the result to
  `queries/{lang}/` for cache reuse.
  Use when the user asks a substantive question about the vault's domain (the
  default answering path), or types `/query`. Pass `--vault NAME` to scope to a
  specific bundle, `--lang CODE` to force the response lang, `--format marp` to
  render as a slide deck (see `reference.md`).
allowed-tools: Read, Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/retrieve.py:*), Bash(bash .claude/scripts/set-config.sh:*)
arguments:
  - name: question
    description: "The user's question, in any enabled lang. Positional, required."
  - name: --vault
    description: "Vault bundle name (skips the active-vault lookup). Useful when running multiple vaults in parallel."
  - name: --lang
    description: "Force the response lang (e.g. `en`, `es`). Skips auto-detection."
  - name: --format
    description: "`markdown` (default) or `marp` (slide deck — see `reference.md`)."
---

# /query — Vault Query

Usage: `/query [--vault NAME] [--lang CODE] [--format markdown|marp] "{question}"`

## Language resolution chain

The retrieval lang is decided in this order — first hit wins:

1. `--lang` flag (explicit, always wins).
2. **Auto-detect** from the question itself (chars + stopwords scoring; only triggers when confident — ties and zero-score return None).
3. `active_lang` in `.claude/state/wikiforge.yaml` (sticky across sessions).
4. `enabled[0]` from the active vault's `vault.yml` (deterministic fallback).

Once resolved, retrieval **strictly searches `wiki/{LANG}/` only** — atoms in other langs are ignored. The response is rendered in `LANG`. The atom propagation pipeline guarantees per-lang parity, so cross-lang citations stay consistent.

## Steps

1. **Resolve vault + retrieve atoms (one bash block, chained with `&&`)**. Critical: same shell, no separate invocations.

   ```bash
   source .claude/scripts/resolve-vault.sh && \
   python3 .claude/scripts/retrieve.py --query "{question}" --vault "$VAULT_PATH" --top 6 --lang-source
   ```

   - `resolve-vault.sh` exports `$VAULT_NAME` and `$VAULT_PATH`. If it asks for a vault choice, **STOP** and surface the question — never pick silently.
   - `retrieve.py` returns top-K atoms (and matching hub pages) as JSON. Each result carries a `type` field — `atom` (default), `entity`, or `comparison` (pre-compiled hub pages).
   - Use `&&` to chain — separate Bash invocations lose env vars.
   - To force a lang in the same shell: add `--lang es` to the retrieve.py call.

   **Top-K** (`--top`, default 6): raise to **10–12** for taxonomic-C questions where you want broader coverage; lower to **3** for narrow-A factual lookups where extra atoms are noise. Regime detection (`CLAUDE.md §4.6`) drives this.

   **Shape hint** (`--query-shape {entity|comparison|topic|atom|auto}`, default `auto`): the script infers shape from the query string + `meta/entities-registry.yaml` (comparison cues, then registered entity mention, then topic cue, else atom). Pass `--query-shape entity|comparison` only to force the boost — e.g. when the user asks about a tool the registry doesn't yet know.

2. **If retrieval returns 0 results** OR the question needs broader context: fall back to manual indexing — `index/{LANG}/index.md` → `moc/{LANG}/{topic}.md` → atoms.

   **If the top result is a hub** (`type: entity` or `type: comparison`): use it as the **scaffold for the response** rather than rebuilding from atoms. Hubs are pre-compiled curated answers cited from atoms — quoting the hub directly (with citations to the atoms it lists) gives the user the best version of the answer. Atoms ranked below the hub are fallback / supporting material.

3. **Check `meta/contradictions.md`** for active conflicts on cited atoms.

4. **Detect response regime** (A / B / C per `CLAUDE.md §4.6`) and draft following `meta/RESPONSE_TEMPLATES.md`. Read the template before drafting — the section list is contract, not suggestion.

5. **Apply the pre-output checklist** (`CLAUDE.md §pre-output checklist`). The full list is canonical there; the high-violation invariants worth keeping in mind while drafting:
   - Word count within ceiling (A=250 / B=600 / C=1000).
   - Written natively in the response lang (per the vault's `agents.md` — proper nouns and universally-known acronyms stay verbatim).
   - **Each step (B) / each cell (C) has exactly one `[[atom]]` citation**; in A, 1–3 atoms inline.
   - **Every number** (percentage, price, threshold) carries an inline `[[atom]]` or `source_id` citation — never deferred to the Sources section.
   - No intro filler ("Excelente pregunta…"), no trailing summary ("En resumen…").
   - Conflict caveat (⚠️) at the end if HIGH/MEDIUM applies.
   - **Surface every cited source's URL** in the Sources section using the convention from the vault's `agents.md` ("Source linking convention" — typically the public URL with locator suffix when the source is timestamped media).

6. **Save** to `queries/{LANG}/{topic}--{question-slug}.md` if the synthesis is new. Include `sources_used` frontmatter with full atom stems and the source URLs.

7. **Update `active_lang`** so the next query in the same session inherits the lang (sticky behaviour). Only when the lang was auto-detected, **not** when the user passed `--lang` explicitly:

   ```bash
   bash .claude/scripts/set-config.sh active_lang "$LANG"
   ```

Queries are **not** auto-propagated across langs — they're per-language caches reflecting what the user asked, when. Atoms are propagated; queries are rendered on demand.

## Inline citation invariant

Numbers (percentages, prices, durations, thresholds) in the response body MUST have an immediate `[[atom]]` or `source_id` next to them. Do **not** defer all citations to the Sources block at the end.

```text
Bad:   "53% of travellers …" [body without citation] … "## Sources [[atom]]"
Good:  "53% of travellers [[en/wiki/occupancy--allow-pets-expand-guest-pool]] …"
       "53% (source_id: VIDEO_ID@01:23) …"
```

## Source linking

The Sources section format and label come from the vault's `agents.md` ("Source linking convention"). The skill is source-type agnostic — for video sources the convention is typically a deep-link URL with timestamp; for articles or PDFs the convention may be a URL with anchor or page number. Read the vault's `agents.md` before drafting if you have not already.

**Fallback** when the vault's `agents.md` does not yet define the section: surface each cited atom's `sources[].url` with a generic label in the response lang (`Source:` / `Fuente:` / etc.), append the `locator` in parentheses when the atom has one. This keeps the response navigable while you (or the vault owner) backfill the section.

## Output formats

- **`--format markdown`** (default): the standard regime-A / B / C response per `CLAUDE.md §4.6` and `meta/RESPONSE_TEMPLATES.md`.
- **`--format marp`**: render the answer as a [Marp](https://marp.app) slide deck. Slide budgets, citation rules per slide, save path, and viewing instructions live in `reference.md`.

Deferred formats (chart, canvas, web-clipper) are out of scope — see `reference.md` for status.
