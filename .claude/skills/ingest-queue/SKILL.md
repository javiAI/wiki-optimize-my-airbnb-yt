---
name: ingest-queue
description: Process all pending sources in the atom-creation queue. Reads pending-atoms.txt and creates wiki/{source_lang}/ atoms for each source.
allowed-tools: Read Write Bash(python3)
---

Process the pending atom-creation queue.

Steps:
1. Read `$VAULT_PATH/.claude/queue/pending-atoms.txt`
2. If empty: report "Queue is empty — nothing to process."
3. Read `$VAULT_PATH/agents.md` to understand atom schema and source language.
4. For each source file listed:
   a. Read the raw source — note the `source_lang` field (or infer from content)
   b. Extract ALL distinct atomic claims. No artificial limit — a 3-minute video may yield 3 atoms, a 2-hour video may yield 40. Each atom must be:
      - One falsifiable sentence (no compound claims with "and/y")
      - Specific enough to contradict (not "pricing matters" but "setting minimum price below 50% of base price degrades algorithm ranking")
      - Non-redundant: check if a near-identical claim already exists in `wiki/{source_lang}/` before creating
   c. For each atom, write `wiki/{source_lang}/{topic}--{slug}.md` with full YAML:
      - `lang: {source_lang}` — always the SOURCE language first (not the query language)
      - `claim:` (one falsifiable sentence in source_lang)
      - `topics:` (array matching vault.yaml topic IDs)
      - `confidence:` high | medium | low (based on how explicitly the source states it)
      - `source_lang: {source_lang}` — document original language
      - `sources:` with `source_id`, `locator` (HH:MM-HH:MM), `url` (deep link), `excerpt` (verbatim quote from source)
      - `conflicts_with: []`
      - `last_verified:` today's date
   d. The PostToolUse(Write) hook fires automatically: auto-link + qa + refine (if enabled)
5. After all atoms written, clear `pending-atoms.txt`
6. Report: N atoms created across M sources, K duplicates skipped

**Source language rule**: Atoms are ALWAYS created in the source material's language first.
If source is in English → `wiki/en/`, if in Spanish → `wiki/es/`.
Translations are a separate step (auto via hook or manual via /translate).

**Deep link URL**: `https://youtube.com/watch?v={source_id}&t={seconds}`
where seconds = minutes×60 + secs of the start timestamp.

**Deduplication check**: Before creating an atom, scan claims in `wiki/{source_lang}/{topic}--*.md`
for a claim covering the same specific fact. If found, skip and log "duplicate: {existing_stem}".
