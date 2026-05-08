---
name: ingest-queue
description: Process all pending sources in the atom-creation queue. Reads pending-atoms.txt and creates atoms in the per-source atomization_lang derived from the raw frontmatter — does NOT translate (propagation hook handles other enabled langs).
allowed-tools: Read Write Bash(python3 .claude/scripts/resolve-vault.sh)
---

Process the pending atom-creation queue.

## Mental model

Atoms are created **once** per source, in that source's `atomization_lang` (the video's `native_lang` if it appears in `enabled_languages`, otherwise the first enabled lang as fallback). You do **not** translate. Propagation to the other enabled langs is handled by the `on-file-write` hook, which fires `propagate_atom.py` after each atom is written.

`raw/` is per-language: `$VAULT_PATH/raw/{lang}/{video}.md`. The same source can have an entry per available subtitle language; the **canonical** source for atomization is the one in `native_lang` (or `enabled[0]` if native isn't enabled).

## Steps

0. **Resolve vault (mandatory preamble)**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Prints `[wikiforge] Using vault: <name> (<path>)` and exports `VAULT_PATH` / `VAULT_NAME`. **If it exits non-zero, STOP** and ask the user which vault's queue to process; never pick silently. Use `$VAULT_NAME` for the queue path in step 1.

1. Read the queue file: `vaults/$VAULT_NAME/state/queue/pending-atoms.txt` (per-vault bundle in this repo, NOT inside `$VAULT_PATH`).
2. If empty: report "Queue is empty — nothing to process." and exit.

   **LLM-fallback advisory** — also check `vaults/$VAULT_NAME/state/queue/llm-fallback.txt`. If it has lines, surface a one-liner before processing: *"N source(s) have no transcript in any enabled language; atomization will be done by LLM synthesis from `enabled[0]` transcript and stamped `excerpt_source: llm_fallback`. Quality may be lower."* Each line is `<video_id>\t<native_lang>\t<atomization_lang>` — list the affected video_ids inline. Continue to step 3 regardless; this is informational, not blocking.

3. Read `vaults/$VAULT_NAME/agents.md` to understand atom schema and per-vault rules (native-synthesis directive, brand whitelist, regime contract, etc.).
4. For each raw file path listed in the queue:
   a. **Read frontmatter** — extract `video_id`, `native_lang`, `language` (subtitle lang of this file), `subtitle_source` (manual|auto).
   b. **Determine atomization_lang**:

      ```bash
      python3 -c "
      import sys; sys.path.insert(0,'.claude/scripts')
      from config import VaultConfig
      print(VaultConfig().atomization_lang_for('<native_lang>'))"
      ```

      The result is the lang you write atoms in. If it differs from this file's `language` field, find the sibling raw file at `$VAULT_PATH/raw/{atomization_lang}/{video}.md` and atomize from that one instead. If no sibling exists in `atomization_lang`, atomize from the file you have but produce atoms **in `atomization_lang`** (single combined translate-and-atomize pass — only happens when native_lang ∉ enabled).
   c. **Extract atomic claims** — no fixed count. Each candidate must be:
      - One falsifiable sentence (no compound claims with "and / y").
      - Specific enough to contradict ("setting minimum price below 50% of base price degrades algorithm ranking", not "pricing matters").

      For each candidate, **integrate against the existing wiki before writing**:

      1. Look up: `python3 .claude/scripts/retrieve.py --query "{claim}" --vault $VAULT_NAME --lang {atomization_lang} --top 3`. (Fall back to globbing `wiki/{atomization_lang}/{topic}--*.md` if retrieve is unavailable.)
      2. Pick a branch:
         - **NEW** — no close match → write a new atom (step 4d).
         - **STRENGTHEN** — an existing atom makes the same claim, same direction, compatible scope → **Edit** that atom: append a new entry to its `sources:` list with this video's `source_id`, `locator`, `url`, `excerpt`, `excerpt_source: native_atomization`, `lang_origin: {atomization_lang}`. Do NOT create a new file. If the second corroboration shifts confidence (e.g. medium → high), update the field. Skip step 4d for this candidate.
         - **CONFLICT** — an existing atom contradicts the new claim → write a new atom (step 4d) AND append a HIGH/MEDIUM entry to `meta/contradictions.md` per CLAUDE.md §4.5.5.
         - **REDUNDANT** — an entry with this same `source_id` already exists for this claim (re-ingest) → skip silently, log `duplicate: {existing_stem}`.
   d. **Write each NEW or CONFLICT atom** to `$VAULT_PATH/wiki/{atomization_lang}/{topic}--{slug}.md`:

      ```yaml
      ---
      lang: {atomization_lang}
      claim: <one falsifiable sentence>
      topics: [...]
      confidence: high | medium | low
      conflicts_with: []
      last_verified: YYYY-MM-DD
      sources:
        - source_id: <video_id>
          locator: HH:MM-HH:MM
          url: https://youtube.com/watch?v={source_id}&t={seconds}
          excerpt: "<verbatim quote from raw/{atomization_lang}/{video}.md>"
          excerpt_source: native_atomization
          lang_origin: {atomization_lang}
      ---

      <body 100-300 words in {atomization_lang}>
      ```

      Note `excerpt_source: native_atomization` for canonical atoms (distinguishes them from propagated atoms that use `yt_manual` / `yt_auto` / `llm_fallback`). No top-level `propagated_from` field — that only appears on propagated atoms.
   e. The `on-file-write` hook fires automatically per atom and:
      - Runs `auto-link.py` and `atom-qa.py`.
      - If `pipeline.auto_propagate: true` and 2+ enabled langs → fires `propagate_atom.py` per other lang in the background. **You do not call it manually.**
5. After all atoms are written, clear (truncate) `pending-atoms.txt`.
6. **Close the batch** — invoke the batch-close hook so hub queues drain and the audit threshold tracks correctly:

   ```bash
   bash .claude/hooks/on-ingest-batch-close.sh <N_NEW_OR_CONFLICT_ATOMS_WRITTEN>
   ```

   The hook (a) calls `/refresh-hubs` to enrich any entity/comparison stubs queued by `entity-detect.py` / `comparison-detect.py`, (b) bumps `state/.ingest-counter`, (c) prints an audit advisory if the counter crosses `vault.yml.maintenance.audit_every_n_ingests`. Pass the count of NEW + CONFLICT atoms (STRENGTHEN edits and REDUNDANT skips don't count).
7. Report: `N atoms created in {atomization_lang} across M sources, K duplicates skipped`. If the batch-close hook printed an audit advisory, surface it verbatim.

## Critical rules

- **NEVER translate** in this skill. The atom is born in `atomization_lang` only. Propagation is automatic via hook.
- **NEVER write atoms in a language other than `atomization_lang`**. The same atom in another lang is created by `propagate_atom.py` later, with its own `propagated_from` marker and excerpt from the target-lang transcript.
- **Deep link URL**: `https://youtube.com/watch?v={video_id}&t={seconds}` where `seconds = HH·3600 + MM·60 + SS` of the start timestamp in the locator.
- **Deduplication scope**: only `wiki/{atomization_lang}/`. Don't compare across langs — propagated atoms are by design "duplicate" facts in another language.

## Edge cases

- **native_lang ∉ enabled**: `atomization_lang_for()` returns `enabled[0]`. Atomize from `raw/{native_lang}/{video}.md` and produce `wiki/{enabled[0]}/...` atoms — a single combined translate-and-atomize pass. Mark `excerpt_source: llm_fallback` (the excerpt was synthesized into the target lang, not lifted verbatim).
- **Subtitle missing for atomization_lang**: should not happen if ingest succeeded for native_lang, but if the canonical raw file is missing, fall back to any available raw/{lang}/ for that video and proceed; flag in QA.
- **Hook skipped**: if `auto_atoms: false` or processing offline, run `python3 .claude/scripts/auto-link.py {stem} --lang {atomization_lang}` and `python3 .claude/scripts/atom-qa.py {stem} --lang {atomization_lang}` manually after writing.
