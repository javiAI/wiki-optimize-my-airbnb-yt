---
name: ingest-queue
description: Process all pending sources in the atom-creation queue. Reads pending-atoms.txt and creates wiki/en/ atoms for each source.
allowed-tools: Read Write Bash(python3)
---

Process the pending atom-creation queue.

Steps:
1. Read `$VAULT_PATH/.claude/queue/pending-atoms.txt`
2. If empty, report "Queue is empty — nothing to process."
3. For each source file listed:
   a. Read the raw source from the path listed
   b. Extract atomic claims (one claim per atom, topic--slug.md naming)
   c. Write each atom to `wiki/en/{topic}--{slug}.md` with full YAML frontmatter:
      - `lang: en`
      - `claim:` (one-sentence factual claim)
      - `topics:` (array from vault.yaml topics)
      - `confidence:` high | medium | low
      - `sources:` with `source_id`, `locator` (HH:MM-HH:MM), `url` (computed deep link), `excerpt`
      - `conflicts_with: []`
      - `last_verified:` today's date
   d. The PostToolUse(Write) hook fires automatically after each write: auto-link + qa + translate
4. After all atoms written, clear `pending-atoms.txt`
5. Report: N atoms created across M sources

Deep link URL formula: `https://youtube.com/watch?v={source_id}&t={seconds}`
where seconds = minutes*60 + secs of the start timestamp.
