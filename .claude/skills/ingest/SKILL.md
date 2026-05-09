---
name: ingest
description: |-
  End-to-end source ingestion: download new sources, queue them, atomize each
  one in its `atomization_lang` (with NEW / STRENGTHEN / CONFLICT / REDUNDANT
  integration against the existing wiki), and close the batch (drains hub
  enrichment queues + bumps the audit counter).
  Atoms are created **once** per source in the canonical lang; the on-file-write
  hook handles propagation to the other enabled langs automatically. The skill
  itself never translates.
  Use when the user asks to "ingest", "ingest a source / video", "process the
  queue", "atomize pending sources", or pastes a source ID / URL. Pass one or
  more source IDs as positional args to download + atomize them in one flow;
  pass none to just process whatever is already in the pending queue.
  See `reference.md` for the full integration tree and edge cases (LLM-fallback
  for native_lang ∉ enabled, missing transcripts, hook bypass).
allowed-tools: Read, Write, Edit, Bash(source .claude/scripts/resolve-vault.sh:*), Bash(bash .claude/scripts/ingest.sh:*), Bash(bash .claude/scripts/batch-ingest.sh:*), Bash(bash .claude/hooks/on-ingest-batch-close.sh:*), Bash(python3 .claude/scripts/retrieve.py:*), Bash(python3 -c:*)
arguments:
  - name: source_id
    description: "Zero or more source identifiers (e.g. YouTube video IDs or URLs). With one or more, the skill downloads each, queues it, and then processes the queue. With none, only the existing queue is processed."
---

# /ingest — Source Ingestion + Atomization

End-to-end ingestion in one flow. Replaces the old two-step `/ingest` + `/ingest-queue` UI — the user no longer has to choose.

## Mental model

Atoms are created **once** per source, in that source's `atomization_lang` (the source's `native_lang` if it appears in `enabled_languages`, otherwise the first enabled lang as fallback). You do **not** translate. Propagation to the other enabled langs is handled by the `on-file-write` hook, which fires `propagate_atom.py` after each atom is written.

`raw/` is per-language: `$VAULT_PATH/raw/{lang}/{source}.md`. The same source can have an entry per available subtitle language; the **canonical** source for atomization is the one in `native_lang` (or `enabled[0]` if native isn't enabled).

## Steps

1. **Resolve vault**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Sets `$VAULT_NAME` and `$VAULT_PATH`. If it exits non-zero, **STOP** and ask the user which vault to ingest into — never pick silently.

2. **Download phase** (skip if no source IDs were passed):

   For each `source_id` argument:

   ```bash
   bash .claude/scripts/ingest.sh "$source_id"
   ```

   The on-bash-complete hook automatically appends each new raw file to `vaults/$VAULT_NAME/state/queue/pending-atoms.txt`. Multiple source IDs are downloaded sequentially before atomization, so they all share a single integration pass (this is what lets STRENGTHEN find atoms produced earlier in the same batch).

3. **Read the queue** at `vaults/$VAULT_NAME/state/queue/pending-atoms.txt`. If it is empty after the download phase, report `Queue is empty — nothing to process.` and exit before step 6.

   **LLM-fallback advisory** — also read `vaults/$VAULT_NAME/state/queue/llm-fallback.txt`. If it has lines, surface a one-liner before atomizing: *"N source(s) have no transcript in any enabled language; atomization will be done by LLM synthesis from `enabled[0]` transcript and stamped `excerpt_source: llm_fallback`. Quality may be lower."* Each line is `<video_id>\t<native_lang>\t<atomization_lang>` — list the affected video_ids inline. Continue regardless; this is informational, not blocking.

4. **Read** `vaults/$VAULT_NAME/agents.md` to load per-vault rules (native-synthesis directive, vault-specific verbatim terms, source-linking convention, regime contract, integration branches).

5. **Atomize each pending raw file**. For each path in the queue:

   1. Read frontmatter — extract `video_id` (or generic `source_id`), `native_lang`, `language` (subtitle lang of this file), `subtitle_source`.
   2. **Determine `atomization_lang`**:

      ```bash
      python3 -c "
      import sys; sys.path.insert(0,'.claude/scripts')
      from config import VaultConfig
      print(VaultConfig().atomization_lang_for('<native_lang>'))"
      ```

      The result is the lang you write atoms in. If it differs from this file's `language` field, find the sibling raw file at `$VAULT_PATH/raw/{atomization_lang}/{source}.md` and atomize from that one. If no sibling exists in `atomization_lang`, atomize from the file you have but produce atoms **in `atomization_lang`** (single combined translate-and-atomize pass — only happens when `native_lang ∉ enabled`).
   3. Extract atomic claims (no fixed count — driven by what the source actually says). Each candidate must be one falsifiable sentence, specific enough to contradict.
   4. **Integrate against the existing wiki before writing each candidate**: look up via `retrieve.py`, then pick a branch (NEW / STRENGTHEN / CONFLICT / REDUNDANT). The full decision tree, atom YAML schema, and CONFLICT bookkeeping are in `reference.md`. Read it once at the start of step 5 if you have not already.
   5. Write each NEW or CONFLICT atom to `$VAULT_PATH/wiki/{atomization_lang}/{topic}--{slug}.md`. STRENGTHEN edits an existing atom in place (no new file). REDUNDANT skips silently.
   6. The `on-file-write` hook fires automatically per atom: `auto-link.py`, `atom-qa.py`, and (when `pipeline.auto_propagate: true` and 2+ enabled langs) `propagate_atom.py` for each other lang. **You do not call any of these manually.**

6. **Clear** (truncate) `pending-atoms.txt` after all atoms are written.

7. **Close the batch** so hub enrichment queues drain and the audit counter advances:

   ```bash
   bash .claude/hooks/on-ingest-batch-close.sh <N_NEW_OR_CONFLICT_ATOMS_WRITTEN>
   ```

   The hook (a) calls `/refresh-hubs` to enrich any entity / comparison stubs queued by `entity-detect.py` / `comparison-detect.py`, (b) bumps `state/.ingest-counter`, (c) prints an audit advisory if the counter crosses `vault.yml.maintenance.audit_every_n_ingests`. Pass the count of NEW + CONFLICT atoms only — STRENGTHEN edits and REDUNDANT skips do not count.

8. **Report** to the user: `N atoms created in {atomization_lang} across M sources, K duplicates skipped`. If the batch-close hook printed an audit advisory, surface it verbatim.

## Critical rules

- **Never translate** in this skill. The atom is born in `atomization_lang` only. Propagation to other enabled langs is automatic via the `on-file-write` hook.
- **Never write atoms in a lang other than `atomization_lang`**. The same atom in another lang is created by `propagate_atom.py` later, with its own `propagated_from` marker and excerpt from the target-lang transcript.
- **Deep link URL** uses the formula in the vault's `agents.md` (varies by source type — for video sources typically `https://youtube.com/watch?v={source_id}&t={seconds}` derived from the locator).
- **Deduplication scope**: only `wiki/{atomization_lang}/`. Do not compare across langs — propagated atoms are by design "duplicate" facts in another language.

For the integration decision tree (NEW / STRENGTHEN / CONFLICT / REDUNDANT), the atom YAML schema, and edge cases (LLM-fallback, missing transcripts, hook bypass), see `reference.md`.
