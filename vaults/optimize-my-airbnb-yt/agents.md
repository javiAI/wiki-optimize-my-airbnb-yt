# optimize-my-airbnb-yt — agents.md

Per-vault reference for agents. Read alongside `vault.yml` (same folder).
The vault's data directory is at `/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt`
and contains data only — no hooks, no settings.json, no queues. All runtime state lives at
`vaults/optimize-my-airbnb-yt/state/` in this repo.

## Languages

- Primary: `es` (atoms created here first)
- Enabled: `es`, `en`
- Source material original language: `en` (transcripts from @OptimizeMyAirbnb / Daniel Rusteen)

## Vault data layout

```
{vault_path}/
  raw/                           # Immutable YouTube transcripts
    YYYY-MM-DD--{slug}.md
  wiki/{lang}/                   # Monolingual atoms — primary truth
    {topic}--{slug}.md
  moc/{lang}/                    # Maps of Content per topic
    {topic}.md
  index/{lang}/
    index.md                     # Tier-0 compact nav (≤150 tokens)
  queries/{lang}/                # Cached query responses
    {topic}--{question}.md
  meta/
    contradictions.md
    backlinks.md
    glossary.md
    qa-reports/{stem}.{lang}.json
    agent-reports/agent-report-YYYY-MM-DD.md
```

## Atom YAML schema

```yaml
---
lang: es
claim: "Single falsifiable sentence."
topics: [pricing]
confidence: high | medium | low
source_lang: en
sources:
  - source_id: VIDEO_ID
    locator: "HH:MM-HH:MM"
    url: "https://youtube.com/watch?v=VIDEO_ID&t=SECONDS"
    excerpt: "Direct quote from source."
    views: 123456                # for source priority
    published: YYYY-MM-DD        # for recency scoring
conflicts_with: []
last_verified: YYYY-MM-DD
---

Body: 100–300 words, native in `lang`. No anglicisms if Spanish.
No intro fluff, no trailing summaries.
```

## Naming

- Atoms: `{topic}--{slug}.md` (lowercase, hyphens)
- Sources (raw): `YYYY-MM-DD--{slug}.md`
- Queries: `{topic}--{question-slug}.md`

## Deep link URL formula

```
locator = "MM:SS-MM:SS"  →  start = first part  →  seconds = M*60 + S
url = "https://youtube.com/watch?v={source_id}&t={seconds}"
```

Computed once at atom-creation time, stored in `sources[].url`. Same URL across language versions.

## Source priority score

```
score = 0.40·recency + 0.30·views_normalized + 0.20·specificity + 0.10·authority
```

When two atoms conflict, the one with higher score is primary.
Documented conflicts: `meta/contradictions.md`.

## Domain topic slugs (auto-inferred, examples)

`pricing`, `occupancy`, `listing-optimization`, `cleaning-ops`, `reviews`, `hospitality`, `ranking`, `direct-booking`, `market-selection`, `regulations`, `tools-tech`, `investing`.

Topics are inferred from content; never restricted to a fixed list.
