# /ingest — reference

Detail material for `/ingest` that does not need to live in `SKILL.md` on every invocation. Read this once at the start of step 5 (atomization).

## Atom YAML schema (canonical, written by this skill)

```yaml
---
lang: {atomization_lang}
claim: <one falsifiable sentence>
topics: [...]
confidence: high | medium | low
conflicts_with: []
last_verified: YYYY-MM-DD
sources:
  - source_id: <video_id>
    locator: HH:MM-HH:MM
    url: https://youtube.com/watch?v={source_id}&t={seconds}
    excerpt: "<verbatim quote from raw/{atomization_lang}/{source}.md>"
    excerpt_source: native_atomization
    lang_origin: {atomization_lang}
---

<body 100–300 words in {atomization_lang}>
```

Notes:

- **No top-level `propagated_from` field on canonical atoms** — that field only appears on atoms produced by `propagate_atom.py` for the other enabled langs.
- **`excerpt_source: native_atomization`** marks atoms born from a verbatim transcript in `atomization_lang`. Propagated atoms use `yt_manual` / `yt_auto` / `llm_fallback` depending on the target-lang transcript availability.
- **Deep link URL formula** is per-vault — it lives in the vault's `agents.md`. The example above is the YouTube convention.

## Per-candidate integration tree

For each atomic claim extracted from a raw file, **before writing anything**:

1. **Look up** existing coverage:

   ```bash
   python3 .claude/scripts/retrieve.py --query "{claim}" --vault $VAULT_NAME --lang {atomization_lang} --top 3
   ```

   Fall back to globbing `wiki/{atomization_lang}/{topic}--*.md` if `retrieve.py` is unavailable.

2. **Pick a branch** based on the top-1 result's `claim` and score:

   | Branch | Trigger | Action |
   | --- | --- | --- |
   | **NEW** | No close match (top-1 score below relevance threshold, or no matches at all) | Write a new atom at `wiki/{atomization_lang}/{topic}--{slug}.md` per the schema above. |
   | **STRENGTHEN** | An existing atom makes the same claim, same direction, compatible scope | **Edit** that atom: append a new entry to its `sources:` list with this video's `source_id`, `locator`, `url`, `excerpt`, `excerpt_source: native_atomization`, `lang_origin: {atomization_lang}`. Do NOT create a new file. If the second corroboration shifts confidence (e.g. medium → high), update the field. Skip the new-atom write for this candidate. |
   | **CONFLICT** | An existing atom contradicts the new claim (opposite direction, incompatible threshold, declared `conflicts_with`) | **BEFORE writing the new atom**, append a HIGH/MEDIUM entry to `meta/contradictions.md` per CLAUDE.md §4.5.5: severity, both `[[atom]]` ids, topic, proposed resolution criterion (per §4.5.3 hierarchy: temporal_supersession / contextual_scope / confidence_tier / authority_tier / specificity_tier), evidence (≤80 words). THEN write the new atom (writing first leaves the contradiction undocumented if anything fails). Both atoms gain each other's stem in their `conflicts_with:` list. |
   | **REDUNDANT** | An entry with this same `source_id` already exists for this claim (re-ingest) | Skip silently and log `duplicate: {existing_stem}`. |

3. **Cap is empirical, not numeric**. There is no fixed atoms-per-source target. The number emerges from what the source actually says — a tactical/how-to source produces roughly `duration_sec / 120` distinct claims; sponsor-heavy or vlog content produces fewer. Padding to hit a number degrades the wiki — stop when you stop finding falsifiable, non-redundant claims.

## Edge cases

- **`native_lang ∉ enabled`**: `atomization_lang_for()` returns `enabled[0]`. Atomize from `raw/{native_lang}/{source}.md` and produce `wiki/{enabled[0]}/...` atoms — a single combined translate-and-atomize pass. Mark `excerpt_source: llm_fallback` (the excerpt was synthesized into the target lang, not lifted verbatim from a target-lang transcript).
- **Subtitle missing for `atomization_lang`**: should not happen if ingest succeeded for `native_lang`, but if the canonical raw file is missing, fall back to any available `raw/{lang}/` for that source and proceed; flag in QA.
- **Hook skipped** (e.g. `auto_atoms: false`, processing offline, or `on-file-write` disabled): run the per-atom hooks manually after writing each atom:

  ```bash
  python3 .claude/scripts/auto-link.py {stem} --lang {atomization_lang}
  python3 .claude/scripts/atom-qa.py {stem} --lang {atomization_lang}
  ```

  Then propagate manually if `auto_propagate` is off:

  ```bash
  python3 .claude/scripts/propagate_atom.py {stem} --from {atomization_lang} --to {other_lang}
  ```
