---
name: ingest
description: Ingest a new source into the vault. Runs ingest.sh, hooks handle atom creation + translation automatically.
allowed-tools: Bash(.claude/scripts/ingest.sh .claude/scripts/batch-ingest.sh .claude/scripts/config.sh .claude/scripts/resolve-vault.sh)
---

Ingest the source identified by the argument.

Usage: `/ingest {source_id}`

Steps:

0. **Resolve vault (mandatory preamble)**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Prints `[wikiforge] Using vault: <name> (<path>)`. **If it exits non-zero, STOP** and ask the user which vault to use; never pick silently.

1. `bash .claude/scripts/ingest.sh {source_id}` — `VAULT_PATH` is already exported by step 0.
2. Confirm the raw file was written to `$VAULT_PATH/raw/{lang}/`.
3. Inform the user: source ingested, hooks have queued it for atom creation. Run `/ingest-queue` when ready to create atoms.

The PostToolUse(Bash) hook will automatically detect ingest.sh completion and update the pending-atoms queue.
