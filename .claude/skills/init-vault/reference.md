# init-vault reference

## vault.yml full schema

Lives at `vaults/{name}/vault.yml` in the repo (per-vault bundle).

```yaml
name: "my-vault"               # slug, matches the bundle directory: vaults/{name}/
vault_path: "~/Dev/obsidian_vaults/my-vault"  # where raw/, wiki/, moc/ live (data only)
version: "2.0"

source:
  type: youtube
  original_language: null      # optional hint; per-source native_lang is auto-detected from yt-dlp

languages:
  enabled: ["en", "es"]        # all wiki languages — no primary/secondary distinction.
                               # atomization_lang is decided per-source: native_lang if in enabled,
                               # else enabled[0] (single combined translate-and-atomize pass).
  detect_from_query: true      # auto-route queries to correct wiki/{lang}/

topics: []                     # always auto-detected; leave empty

pipeline:
  auto_atoms: true             # create atoms automatically after ingest
  auto_propagate: false        # re-atomize each canonical atom into every other enabled lang at the
                               # same locator using the target-lang transcript (NOT a translation).
                               # Legacy alias `auto_translate` is still read for backwards compat.
  auto_link: true              # update MOC files after each atom write (via hook)
  deep_links: true             # compute YouTube ?t= URLs at atom creation time
  qa_on_create: true           # run atom-qa.py after each atom write (via hook)
  auto_refine: false           # second-pass quality refinement (expensive)

qa:
  completeness: true           # require: claim, source, url, last_verified
  url_validation: true         # sources[].url must match ?v=*&t=* format
  anglicism_check: []          # langs to check; auto-applied to non-English atoms
  conflict_check: true         # flag atoms that conflict with meta/contradictions.md
```

## Atom schema

```yaml
---
lang: en                       # ISO language code of THIS atom file
claim: "Single falsifiable sentence ending with a period."
topics: [pricing]              # one or more topic slugs (auto-inferred)
confidence: high               # high | medium | low
propagated_from: null          # null on canonical atoms; set to source-lang code on propagated atoms
sources:
  - source_id: Ek8m0ZAhMgA    # YouTube video ID (or PDF name, etc.)
    locator: "03:42-04:15"     # timestamp range in source
    url: "https://youtube.com/watch?v=Ek8m0ZAhMgA&t=222"  # deep link (t=seconds)
    excerpt: "Direct quote from source — verbatim in this atom's language."
    excerpt_source: native_atomization  # yt_manual | yt_auto | llm_fallback | native_atomization
    lang_origin: en            # which lang directory holds the canonical atom for this stem
conflicts_with: []             # list of atom stems that contradict this one
last_verified: 2026-04-29
---

Body text (100–300 words). Written natively in the target language.
No anglicisms if non-English. No intro fluff. No trailing summary.
```

**Field semantics**:

- `excerpt_source`:
  - `native_atomization` — canonical atom; excerpt lifted verbatim from `raw/{lang}/{video}.md` during ingest-queue.
  - `yt_manual` — propagated atom; excerpt lifted from creator-authored target-lang subtitles.
  - `yt_auto` — propagated atom; excerpt lifted from YouTube auto-translated subtitles.
  - `llm_fallback` — propagated atom; no target-lang transcript available, excerpt synthesized by LLM.
- `propagated_from`: top-level field present **only** on propagated atoms. Points to the canonical atom's lang.

## Deep link URL formula

```
locator = "MM:SS-MM:SS"  →  start = first part  →  seconds = M*60 + S
url = "https://youtube.com/watch?v={source_id}&t={seconds}"

Example: locator "03:42-04:15", source_id "Ek8m0ZAhMgA"
  start = "03:42"  →  seconds = 3*60 + 42 = 222
  url = "https://youtube.com/watch?v=Ek8m0ZAhMgA&t=222"
```

## Index stub format

```markdown
# Vault Index — {vault-name} ({lang})

| Topic | Atoms | Summary |
|-------|-------|---------|
| — | — | Run /audit to populate |

→ Read `moc/{lang}/{topic}.md` for full topic details.
```

## Hook wiring

Hooks live in `repo/.claude/hooks/` and are wired by `repo/.claude/settings.json`.
**Never** place hooks or `settings.json` inside a vault — vaults contain data only.
Hooks resolve `VAULT_PATH` from the file path being written, so a single hook
configuration in the repo serves every vault.

Per-vault state (queue, logs, locks) lives at `repo/vaults/{vault-name}/state/`
alongside the bundle's `vault.yml` and `agents.md`. State is created on demand
by the hooks. Deleting `vaults/{vault-name}/` removes the entire vault bundle
from the repo (config + per-vault docs + state); the data directory at
`vault_path` is deleted separately.

## Topic slug conventions

| Domain | Example slugs |
|--------|--------------|
| Airbnb hosting | pricing, occupancy, reviews, listing-optimization, cleaning-ops, tools-tech, direct-booking, ranking, hospitality, market-selection, investing, regulations |
| General | operations, content, marketing, finance, product, legal |

Slugs: lowercase, hyphens, no spaces. Topics auto-inferred from content — never restrict manually.

## Atom file naming

Pattern: `{topic}--{slug}.md`
- topic: one of the detected topic slugs
- slug: 2-6 word description of the claim, hyphenated

Examples:
- `pricing--initial-discount-strategy.md`
- `occupancy--minimum-stay-policy.md`
- `tools-tech--pms-cleaning-triggers.md`
