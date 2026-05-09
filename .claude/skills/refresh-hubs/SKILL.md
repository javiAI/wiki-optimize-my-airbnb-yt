---
name: refresh-hubs
description: |-
  Drain entity- and comparison-hub enrichment queues. For each pending slug,
  synthesises a multi-section body from the hub's `cited_atoms[]` via LLM
  (`refresh-hubs.py` invokes `claude -p` with a per-kind prompt). Frontmatter
  preserved; body replaced inside the `<!-- AUTO-GENERATED -->` markers;
  `last_updated` bumped.
  Use when the user asks to "enrich hubs", "redo hub synthesis", "drain
  entity / comparison queue", or runs `/refresh-hubs`. Most invocations are
  automatic via the `on-ingest-batch-close` hook at the end of `/ingest` —
  invoke manually after a bulk re-ingest, when a previous run failed, or to
  redo enrichment from updated atoms.
allowed-tools: Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/refresh-hubs.py:*)
arguments:
  - name: --kind
    description: "`entity` | `comparison` | `all` (default `all`). Restrict to one queue."
  - name: --dry-run
    description: "Report what would be enriched, no LLM calls."
---

# /refresh-hubs — Enrich pending hub stubs

Hub pages (`{lang}/wiki/entity--<slug>.md`, `{lang}/wiki/comparison--<a>-vs-<b>.md`) are stubbed at ingest time by `entity-detect.py` and `comparison-detect.py`. Slugs land in `state/queue/{entity,comparison}-enrichment.txt`. This skill drains both queues and replaces each stub body with an LLM synthesis built from the hub's `cited_atoms[]`.

## When it runs

- **Automatic**: `on-ingest-batch-close.sh` calls this at the end of `/ingest`. The user shouldn't normally need to invoke manually.
- **Manual**: after a bulk re-ingest, when you want to redo enrichment from updated atoms, or when a previous run failed (queues are only truncated on full success).

## Steps

0. **Resolve vault** (mandatory preamble):

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Prints `[wikiforge] Using vault: <name> (<path>)`. **If it exits non-zero, STOP** and ask the user which vault to refresh; never pick silently.

1. Run the script:

   ```bash
   python3 .claude/scripts/refresh-hubs.py --vault "$VAULT_PATH" [--kind entity|comparison|all] [--dry-run]
   ```

2. **Report** the count from the script's last line: `N hub(s) enriched` (and `M failed` if any).

3. **On failures**, queues are NOT truncated — re-run after fixing the root cause (usually a missing cited atom or LLM timeout).

## What gets written

Each enriched hub keeps its frontmatter, gains `last_updated: <today>`, and has its body replaced with sections rendered to the per-kind layout:

- **Entity** (`type: entity`): identity paragraph + kind-specific sections (varies by `kind: tool | company | person | product | service | book | channel`) + Sources.
- **Comparison** (`type: comparison`): two-sentence framing + `## At a glance` table + `## Per-dimension` sections + `## Recommendation` decision-tree + Sources.

The `<!-- AUTO-GENERATED -->` marker delimits the rewrite zone — anything outside it is preserved across runs. Per-kind section schemas live in the prompt templates inside `refresh-hubs.py`.

## Cross-lang propagation

Currently each hub is enriched **in the lang where it was first detected**. Cross-lang propagation (mirror the synthesis into other enabled langs) is on the follow-up list and will live alongside `propagate_atom.py`. When that ships, this skill won't change shape — the hook will call propagation per enriched hub.
