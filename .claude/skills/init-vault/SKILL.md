---
name: init-vault
description: Creates a new WikiForge vault from scratch with guided setup, source ingestion, and first atom creation — all in one flow. Use when the user says "create a new vault", "init vault", "initialize a vault", "set up a new knowledge base", "start a new vault", or "/init-vault". Runs the complete pipeline: configuration → ingest → atoms. Only requires user input where decisions are needed; automates everything else.
---

This skill guides the user through the full vault creation pipeline interactively.
It replaces the bash wizard entirely when running inside a Claude session.

## Phase 1 — Collect configuration

Ask the user these questions **one at a time**. Do not present them all at once.
Wait for each answer before asking the next.

**Q1. Vault name**
Ask: "What should we call this vault? (slug format, e.g. `my-airbnb-notes`)"
- Lowercase, hyphens only, no spaces
- This becomes the config filename: `configs/{name}.yaml`

**Q2. Data directory**
Ask: "Where should the vault data live? (atoms, sources, MOCs)"
- Default: `~/Dev/obsidian_vaults/{name}`
- Accept `~` expansion
- Tell the user: "This is where Obsidian will open the vault."

**Q3. Output languages**
Ask: "Which languages should atoms be written in? (comma-separated ISO codes, e.g. `en` or `en,es`)"
- Default: `en`
- First code = primary language; others = translations generated automatically
- If multiple languages: auto_translate will be enabled

**Q4. Sources to ingest**
Ask:
```
What sources should we ingest? Supported formats:
  • YouTube video ID:        Ek8m0ZAhMgA
  • Full YouTube URL:        https://youtube.com/watch?v=Ek8m0ZAhMgA
  • YouTube channel URL:     https://www.youtube.com/@ChannelName
  • Path to a .txt file:     ./oma-videos.txt  (one ID/URL per line)

Paste IDs, URLs, or a file path — comma or newline separated.
Leave empty to skip for now (you can add sources later with /ingest).
```

**Q5. Pipeline options**
Ask both as yes/no:
- "Auto-create atoms after ingest? [Y/n]" → default yes → `auto_atoms: true`
- "Auto-refine atoms (second quality pass, costs more tokens)? [y/N]" → default no → `auto_refine: false`

---

## Phase 2 — Write configuration and create vault structure

After collecting answers, do the following **without asking further questions**:

1. Derive values:
   - `primary_lang` = first language code from Q3
   - `extra_langs` = remaining codes (may be empty)
   - `auto_translate` = true if extra_langs is non-empty, else false

2. Write `configs/{vault-name}.yaml` in this repository using this template:
   ```yaml
   name: "{vault-name}"
   vault_path: "{expanded data path}"
   version: "1.0"

   languages:
     enabled: ["{primary}", "{extra1}", ...]
     primary: "{primary}"
     secondary: ["{extra1}", ...]
     detect_from_query: true

   topics: []

   pipeline:
     auto_atoms: {true|false}
     auto_translate: {true|false}
     auto_link: true
     deep_links: true
     qa_on_create: true
     auto_refine: {true|false}

   qa:
     completeness: true
     url_validation: true
     anglicism_check: [{extra langs}]
     conflict_check: true
   ```
   See [reference.md](reference.md) for full schema details.

3. Create the vault directory structure by running:
   ```bash
   bash scripts/init-vault-dirs.sh "{vault-name}"
   ```
   If that script does not exist, create these directories manually using the Bash tool:
   ```
   {vault_path}/raw/
   {vault_path}/wiki/{lang}/    (one per enabled language)
   {vault_path}/moc/{lang}/
   {vault_path}/index/{lang}/
   {vault_path}/queries/{lang}/
   {vault_path}/meta/
   {vault_path}/.claude/hooks/
   {vault_path}/.claude/queue/
   {vault_path}/.claude/logs/
   ```

4. Create stub files:
   - `{vault_path}/index/{lang}/index.md` for each language (see reference.md for format)
   - `{vault_path}/meta/contradictions.md` (empty stub with format comment)
   - `{vault_path}/meta/backlinks.md` (empty)
   - `{vault_path}/meta/glossary.md` (empty)
   - `{vault_path}/agents.md` with atom schema using the primary language

5. Copy hooks from `.claude/hooks/` in this repo to `{vault_path}/.claude/hooks/`

6. Write `{vault_path}/.claude/settings.json` with hook wiring (see reference.md)

7. Show the user the generated `configs/{name}.yaml` and ask:
   **"Here's the config. Edit it in the IDE if you want to adjust anything, then reply 'ready' to continue."**
   Wait for confirmation before proceeding.

---

## Phase 3 — Ingest sources

If the user provided sources in Q4:

1. Write the sources to a temp file `{vault_path}/.claude/queue/init-sources.txt`, one per line.
   - If the user passed a `.txt` file path, use that file directly.
   - Otherwise write the IDs/URLs they provided.

2. Run ingest:
   ```bash
   VAULT_NAME="{vault-name}" bash scripts/batch-ingest.sh {vault_path}/.claude/queue/init-sources.txt
   ```

3. Report progress: show how many ingested OK, skipped, failed.

4. If all failed (e.g. network error), say so and suggest running manually later.

If the user skipped sources, say:
> "No sources ingested. Add them later with: `bash scripts/batch-ingest.sh <file>`"
> "Or run `/ingest {video_id}` to add one at a time."

---

## Phase 4 — Create atoms

If `auto_atoms` is true AND at least one source was ingested successfully:

1. Read the vault config to get vault_path and primary language.

2. List all files in `{vault_path}/raw/` to see what was just ingested.

3. For each ingested source file, extract atomic claims following the atom schema in `agents.md` inside the vault. Rules:
   - One claim per file → `wiki/{lang}/{topic}--{slug}.md`
   - Extract 5–15 atoms per source (quality over quantity)
   - Topics are inferred from content — never restrict to a fixed list
   - Each atom must have: `lang`, `claim`, `topics`, `confidence`, `sources` (with `source_id`, `locator`, `url`, `excerpt`), `last_verified`
   - Compute `url` from `source_id` + `locator` using: start timestamp → seconds → `?v={id}&t={seconds}`
   - Body text (below frontmatter): 100–300 words, written in the target language, no anglicisms if non-English

4. After writing each atom, the `on-file-write` hook fires automatically — do not run auto-link or QA manually.

5. When all atoms are written, run:
   ```bash
   VAULT_NAME="{vault-name}" python3 scripts/vault-agent.py --incremental
   ```
   to populate MOC files and the index.

---

## Phase 5 — Summary

Report to the user:

```
✓ Vault created: {vault-name}
  Config:  configs/{vault-name}.yaml
  Data:    {vault_path}

  Sources ingested:  {N} (ok: X, skip: Y, fail: Z)
  Atoms created:     {N} across {M} topics
  Topics detected:   {list}
  QA warnings:       {N} (run /qa to review)

Next: ask me anything about the content, or run /audit for a full health check.
```

---

## Error handling

- If `yt-dlp` is not installed: tell the user and show install command (`brew install yt-dlp` / `pip install yt-dlp`)
- If a source has no subtitles: log as SKIP, continue with others
- If atom QA fails: log to `{vault_path}/meta/qa-reports/`, continue (non-blocking)
- If the vault already exists at the given path: warn but do not overwrite existing data
