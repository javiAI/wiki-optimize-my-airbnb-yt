---
name: query
description: Run a vault query. Auto-detects response language from the question itself; falls back to config.yaml.active_lang and then enabled[0]. Use --lang to force.
allowed-tools: Read Bash(python3) Bash(source)
---

# /query

Run a query against the vault.

Usage: `/query [--lang es|en] [--format markdown|marp] "{question}"`

## Language resolution chain

The retrieval lang is decided in this order — first hit wins:

1. `--lang` flag (explicit, always wins)
2. **Auto-detect** from the question itself (chars + stopwords scoring; only triggers if confident — ties and zero-score return None)
3. `config.yaml.active_lang` in `.claude/config/` (sticky across sessions)
4. `enabled[0]` from `vaults/{name}/vault.yml` (deterministic fallback)

Once resolved, retrieval **strictly searches `wiki/{LANG}/` only** — atoms in other langs are ignored at retrieval time. The response is rendered in `LANG`. The atom propagation pipeline guarantees per-lang parity, so cross-lang citations stay consistent.

## Steps

0. **Resolve vault + retrieve atoms (one bash block, chain with &&)**. CRITICAL: All commands in same shell, no separate invocations.

   ```bash
   source .claude/scripts/resolve-vault.sh && \
   python3 .claude/scripts/retrieve.py --query "{question}" --vault "$VAULT_PATH" --top 6 --lang-source
   ```

   - `resolve-vault.sh` exports VAULT_PATH, resolves from state.yaml (or asks if ambiguous)
   - `retrieve.py` reads VAULT_PATH from same shell, returns top-6 atoms as JSON
   - **Important**: Use `&&` to chain — separate Bash invocations lose environment variables
   - To force a lang: add `--lang es` to retrieve.py command

1. If retrieval returns 0 results OR the question needs broader context: fall back to manual indexing — `index/{LANG}/index.md` → `moc/{LANG}/{topic}.md` → atoms.
2. Check `meta/contradictions.md` for active conflicts on cited atoms.
3. Detect response regime (A/B/C per CLAUDE.md §4.6) and draft following `meta/RESPONSE_TEMPLATES.md`.
4. Apply pre-output checklist (CLAUDE.md §pre-output checklist):
   - Word count within ceiling (A=250/B=600/C=1000)
   - No anglicisms (substitution table applied)
   - Each step/cell has exactly one [[atom]] citation
   - **Each number backed by inline [[atom]] citation or source_id** (not just at end)
   - No intro filler, no trailing summary
   - Conflict caveat if HIGH/MEDIUM active
   - **YouTube URL linking**: For each atom cited, extract `sources_url` from the JSON and include in Sources section as `Vídeo: https://...` with timestamp if available from locator field.
5. Save to `queries/{LANG}/{topic}--{question-slug}.md` if synthesis is new.
   - Include `sources_used` frontmatter with full atom stems
   - For each source, preserve YouTube URL in frontmatter comment or dedicated field
6. **Update `config.yaml.active_lang`** to `LANG` so the next query in the same session inherits it (sticky behaviour). Only do this if lang was auto-detected (not explicit `--lang` flag).

   ```bash
   bash .claude/scripts/set-config.sh active_lang "$LANG"
   ```

Queries are NOT auto-propagated across langs — they're per-language caches reflecting what the user asked, when. Atoms are propagated; queries are rendered on demand.

## YouTube linking requirement

Every response MUST include YouTube video URLs from the cited atoms. The JSON from `retrieve.py` includes `sources_url` for each atom — extract and surface this in the final response.

**Format for Sources section** (all regimes A/B/C):

```markdown
## Fuentes

- [[wiki/{lang}/{stem}]] — {one-line summary of claim}
  Vídeo: {sources_url}
  
- [[wiki/{lang}/{stem2}]] — {another claim}
  Vídeo: {sources_url2}
```

**When to include locator**: If the atom frontmatter contains a `locator` field (e.g., `01:23-01:47`), append to the YouTube URL:
```markdown
Vídeo: https://youtube.com/watch?v=VIDEO_ID&t=83  (01:23-01:47)
```

**Inline citation requirement**: Numbers (percentages, prices, durations) in the response body MUST have immediate [[atom]] or `source_id` next to them. Do NOT defer all citations to the end.

Bad: "The 53% of travelers..." [body text without citation] ... "Fuentes: [[atom]]"
Good: "The 53% of travelers [[wiki/es/occupancy--allow-pets-expand-guest-pool]]..." or "The 53% (source_id: VIDEO_ID@01:23)..."

## Output formats

`--format markdown` (default): the standard regime-A/B/C response per CLAUDE.md §4.6.

`--format marp`: render the answer as a [Marp](https://marp.app) slide deck. Use the template at `.claude/templates/response-marp.md.template` and apply these rules on top of the standard checklist:

- **Slide budget by regime**: A=3 slides, B=5-7 slides, C=8-12 slides
- **One headline per slide** (≤8 words), 3-5 bullets max, each ≤12 words
- **One atom citation per slide**: `[[wiki/{LANG}/<atom>]]` at the bottom
- **Last slide is always "Sources"** listing every cited atom with locator URL
- **Conflict caveat**: if HIGH/MEDIUM conflict applies, add a ⚠️ slide before Sources (not intercalated)
- **Save to**: `queries/{LANG}/{topic}--{slug}.marp.md` (note `.marp.md` suffix so it's distinguishable from the markdown answer)
- **Tell the user how to view**: `npx @marp-team/marp-cli <file> --preview` or VS Code Marp extension

The word ceiling (A=250/B=600/C=1000) still applies to total cumulative bullet text — slide format doesn't license verbosity.

**Deferred formats** (not implemented):

- `--format chart` (matplotlib/plotly) — needs numeric content detection + script execution sandbox. Design open: should the script run in a separate process? Where does the output PNG live? Punted for now; ask if you need it urgently.
- `--format canvas` (Obsidian Canvas JSON) — needs node-positioning algorithm. Punted.
- Obsidian Web Clipper integration — out of scope for this repo.
