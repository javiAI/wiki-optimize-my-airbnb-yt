---
name: refresh-hubs
description: Drain entity- and comparison-hub enrichment queues. Synthesises stub bodies from cited atoms via LLM. Runs automatically via on-ingest-batch-close hook; invoke manually after bulk imports or to redo enrichment.
allowed-tools: Bash(python3 .claude/scripts/refresh-hubs.py source .claude/scripts/resolve-vault.sh)
---

# /refresh-hubs — Enrich pending hub stubs

Hub pages (`{lang}/wiki/entity--<slug>.md`, `{lang}/wiki/comparison--<a>-vs-<b>.md`) are stubbed at ingest time by `entity-detect.py` and `comparison-detect.py`. Slugs land in `state/queue/{entity,comparison}-enrichment.txt`. This skill drains both queues and replaces each stub body with an LLM synthesis built from its `cited_atoms[]`.

## When it runs

- **Automatic**: `on-ingest-batch-close.sh` calls this at the end of `/ingest`. The user shouldn't normally need to invoke manually.
- **Manual**: after a bulk re-ingest, when you want to redo enrichment from updated atoms, or when a previous run failed (queues are only truncated on full success).

## Usage

```
/refresh-hubs                      # active vault, all enabled langs, both kinds
/refresh-hubs --kind entity        # only entity hubs
/refresh-hubs --kind comparison    # only comparison hubs
/refresh-hubs --dry-run            # report what would be enriched, no LLM calls
```

## Steps

0. **Resolve vault (mandatory preamble)**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Prints `[wikiforge] Using vault: <name> (<path>)`. **If it exits non-zero, STOP** and ask the user which vault to refresh; never pick silently.

1. Run: `python3 .claude/scripts/refresh-hubs.py --vault "$VAULT_PATH" [--kind entity|comparison|all] [--dry-run]`

2. Report the count from the script's last line: `N hub(s) enriched` (and `M failed` if any).

3. If failures occurred, queues are NOT truncated — re-run after fixing root cause (usually a missing cited atom or LLM timeout).

## What gets written

Each enriched hub keeps its frontmatter, gains `last_updated: <today>`, and has its body replaced with sections rendered to the per-kind layout (entity: identity + kind-specific sections + Sources; comparison: framing + At a glance table + Per-dimension + Recommendation + Sources). The `<!-- AUTO-GENERATED -->` marker delimits the rewrite zone.

## Cross-lang propagation

Currently each hub is enriched **in the lang where it was first detected**. Cross-lang propagation (mirror the synthesis into other enabled langs) is on the Phase 6 follow-up list and lives in `propagate_atom.py`. When that ships, this skill won't change shape — the hook will just call propagation per enriched hub.
