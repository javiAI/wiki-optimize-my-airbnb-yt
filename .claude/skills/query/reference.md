# /query — reference

Detail material for `/query` that does not need to be in `SKILL.md` on every invocation. Read this when the user asks for `--format marp` or asks about deferred formats.

## `--format marp` — slide deck

Render the answer as a [Marp](https://marp.app) deck. Use the template at `.claude/templates/response-marp.md.template`. The standard regime-A / B / C ceilings (250 / 600 / 1000 words) still apply to total cumulative bullet text — slide format does not license verbosity.

### Slide budget

| Regime | Slides |
|--------|--------|
| A. Narrow factual | 3 |
| B. Tactical multi-palanca | 5–7 |
| C. Taxonomic / broad | 8–12 |

### Per-slide rules

- **One headline per slide**, ≤ 8 words.
- **3–5 bullets max** per slide, each ≤ 12 words.
- **One atom citation per slide**: `[[wiki/{LANG}/<atom>]]` at the bottom.
- **Last slide is always "Sources"**, listing every cited atom with its locator URL (use the vault's `agents.md` source-linking convention).
- **Conflict caveat**: if a HIGH/MEDIUM conflict applies, add a single ⚠️ slide *before* Sources — never intercalated into the body.

### Save path

`queries/{LANG}/{topic}--{slug}.marp.md`. The `.marp.md` suffix distinguishes the deck from the markdown answer (which would be `queries/{LANG}/{topic}--{slug}.md`).

### Tell the user how to view

- CLI: `npx @marp-team/marp-cli <file> --preview`
- Editor: VS Code Marp extension (live preview)

## Deferred formats

These are not implemented and have no estimated landing date. Ask the user whether the use-case justifies a one-off implementation before promising any of them:

| Format | Why deferred |
|--------|--------------|
| `--format chart` (matplotlib / plotly) | Needs numeric-content detection in atoms + a script execution sandbox. Open design questions: should the script run in a separate process? Where does the output PNG live alongside `queries/{LANG}/`? |
| `--format canvas` (Obsidian Canvas JSON) | Needs a node-positioning algorithm (force-directed layout or similar) plus a stable mapping from atoms / hubs → canvas nodes. |
| Obsidian Web Clipper integration | Out of scope — that workflow goes in the opposite direction (web → vault), and is handled at ingest time, not query time. |
