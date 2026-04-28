---
name: ingest
description: Ingest a new source into the vault. Runs ingest.sh, hooks handle atom creation + translation automatically.
allowed-tools: Bash(scripts/ingest.sh scripts/batch-ingest.sh scripts/config.sh)
---

Ingest the source identified by the argument.

Usage: `/ingest {source_id}`

Steps:
1. `source scripts/config.sh && bash scripts/ingest.sh {source_id}`
2. Confirm the raw file was written to `$VAULT_PATH/raw/`.
3. Inform the user: source ingested, hooks have queued it for atom creation. Run `/ingest-queue` when ready to create atoms.

The PostToolUse(Bash) hook will automatically detect ingest.sh completion and update the pending-atoms queue.
