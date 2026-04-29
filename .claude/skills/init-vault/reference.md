# init-vault reference

## vault.yaml full schema

```yaml
name: "my-vault"               # slug, matches configs/{name}.yaml filename
vault_path: "~/Dev/obsidian_vaults/my-vault"  # where raw/, wiki/, moc/ live
version: "1.0"

languages:
  enabled: ["en", "es"]        # all output languages
  primary: "en"                # first language, atoms created here first
  secondary: ["es"]            # auto-translated from primary if auto_translate: true
  detect_from_query: true      # auto-route queries to correct wiki/{lang}/

topics: []                     # always auto-detected; leave empty

pipeline:
  auto_atoms: true             # create atoms automatically after ingest
  auto_translate: false        # translate primary atoms to secondary languages
  auto_link: true              # update MOC files after each atom write (via hook)
  deep_links: true             # compute YouTube ?t= URLs at atom creation time
  qa_on_create: true           # run atom-qa.py after each atom write (via hook)
  auto_refine: false           # second-pass quality refinement (expensive)

qa:
  completeness: true           # require: claim, source, url, last_verified
  url_validation: true         # sources[].url must match ?v=*&t=* format
  anglicism_check: ["es"]      # check body text for untranslated English terms
  conflict_check: true         # flag atoms that conflict with meta/contradictions.md
```

## Atom schema

```yaml
---
lang: en                       # ISO language code
claim: "Single falsifiable sentence ending with a period."
topics: [pricing]              # one or more topic slugs (auto-inferred)
confidence: high               # high | medium | low
source_lang: en                # language of original source
sources:
  - source_id: Ek8m0ZAhMgA    # YouTube video ID (or PDF name, etc.)
    locator: "03:42-04:15"     # timestamp range in source
    url: "https://youtube.com/watch?v=Ek8m0ZAhMgA&t=222"  # deep link (t=seconds)
    excerpt: "Direct quote from source."
conflicts_with: []             # list of atom stems that contradict this one
last_verified: 2026-04-29
---

Body text (100–300 words). Written natively in the target language.
No anglicisms if non-English. No intro fluff. No trailing summary.
```

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

## .claude/settings.json format

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": "bash {vault_path}/.claude/hooks/on-file-write.sh", "timeout": 120}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "bash {vault_path}/.claude/hooks/on-bash-complete.sh", "timeout": 30}]
      }
    ],
    "Stop": [{"hooks": [{"type": "command", "command": "bash {vault_path}/.claude/hooks/on-session-stop.sh", "timeout": 60}]}],
    "SessionStart": [{"hooks": [{"type": "command", "command": "bash {vault_path}/.claude/hooks/on-session-start.sh", "timeout": 10}]}]
  }
}
```

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
