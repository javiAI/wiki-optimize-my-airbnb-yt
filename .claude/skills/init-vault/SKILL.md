---
name: init-vault
description: Creates a new WikiForge vault from scratch with guided setup, source ingestion, and first atom creation — all in one flow. Use when the user says "create a new vault", "init vault", "initialize a vault", "set up a new knowledge base", "start a new vault", or "/init-vault". Runs the complete pipeline: configuration → ingest → atoms. Accepts an optional YAML answers file OR an input directory containing `config.yaml` (+ optional `sources.txt`) as argument to skip the interactive Q&A.
---

## Phase 0 — Choose mode (directory / config-file / interactive)

The user's argument decides:

1. **Directory-mode**. Argument is a directory (e.g. `/init-vault vaults/oma-test-1/`). The script auto-detects `config.yaml` (or `config.yml`) and `sources.txt` inside it. Run:

   ```bash
   bash .claude/scripts/init-vault.sh <input_dir>
   ```

   - If the dir is `vaults/{name}/`, its basename becomes the vault slot name (config.yaml's `name:` field is informational and should match).
   - If `sources.txt` is present, the script runs batch-ingest automatically after bundle creation — **skip Phase 3**, you don't need to write a queue file or invoke ingest separately.
   - Skip Phase 1 entirely. **If `auto_atoms: true` in config.yaml, Phase 4 is mandatory in this same turn** — do not stop and tell the user to run `/ingest-queue`. The post-ingest hook populates `vaults/{name}/state/queue/pending-atoms.txt`; read it and atomize each entry exactly as Phase 4 prescribes (parallel subagents, one per source).

2. **Config-file mode**. Argument is a YAML file (e.g. `/init-vault path/to/answers.yml`). Run `init-vault.sh --config <path>`. The script reads every answer from the file; skip Phase 1 and continue with Phase 3 (sources) — no auto-ingest in this mode.

3. **Interactive mode**. No argument. Run **Phase 1** below to collect answers conversationally.

The expected schema is in `.claude/templates/init-answers.yml.example`. Required fields: `name`, `data_path`, `languages`. All others fall back to interactive defaults. If a file is missing fields you'd like the user to confirm (e.g. they didn't list languages), prompt only for those — don't re-ask everything.

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

**Q3. Enabled languages**
Ask: "Which languages should atoms exist in? (comma-separated ISO codes, e.g. `en` or `en,es`)"
- Default: `en`
- All languages listed are equal — there is no "primary" / "secondary".
- Each video's native language is auto-detected per-source from yt-dlp metadata. The atom is created (atomized) in that language, then propagated to every other enabled language by re-atomizing at the same locator using the target-language subtitle (or LLM fallback if YouTube has no subs in that lang).
- If a video's native lang isn't in this list, the atom is created in the first enabled language directly (single combined translate-and-atomize pass).
- Order doesn't matter — but the first lang acts as the fallback when native lang isn't enabled.

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
Ask each as yes/no:
- "Auto-create atoms after ingest? [Y/n]" → default yes → `auto_atoms: true`
- (Only if Q3 enabled 2+ languages) "Auto-propagate atoms to other enabled languages? [Y/n]" → default yes → `auto_propagate: true`. Propagation re-atomizes at the same locator using the target-lang subtitle (or LLM fallback if YouTube has no subs in that lang) — not a wholesale translation.
- "Auto-refine atoms (second quality pass, costs more tokens)? [y/N]" → default no → `auto_refine: false`

---

## Phase 2 — Write configuration and create vault structure

After collecting answers, **prefer the deterministic script** to do the structural work — do not recreate this logic by hand. Run:

```bash
bash .claude/scripts/init-vault.sh
```

…feeding it the answers Q1–Q5. Each terminal `read` prompt maps 1:1 to a question:
1. Vault name (slug)
2. Vault data path
3. Description (short)
4. Enabled languages (comma-separated, no primary/secondary)
5. Auto-create atoms? (y/n) — answers Q5a
6. Auto-propagate atoms across enabled langs? (y/n) — answers Q5b. Only prompted if 2+ languages were given.
7. Auto-refine atoms? (y/n) — answers Q5c
8. Final "Create vault?" confirmation — answer y

The script:
- Creates the bundle `vaults/{vault-name}/` in this repo with `vault.yml` (rendered from `.claude/templates/vault.yml.template`), `agents.md` (rendered from `.claude/templates/agents.md.template`), and `state/` for runtime queue/logs.
- Creates the vault data directory tree at the chosen path with `{lang}/raw/`, `{lang}/wiki/`, `{lang}/moc/`, `{lang}/index/`, `{lang}/queries/`, `meta/`.
- Writes data stubs (per-language index, contradictions, backlinks, glossary).

You do not need to write any of those files directly.

**What the script does NOT do** (and you must NOT do either):
- Copy hooks into the vault — repo's `.claude/hooks/` are the live ones; they derive `VAULT_PATH` from the file path on write, so they work for any vault.
- Write `.claude/settings.json` inside the vault — repo's settings.json is the only source of hook wiring.
- Write `agents.md` inside the vault data — per-vault `agents.md` lives in `vaults/{vault-name}/agents.md` (repo).
- Init git inside the vault — that's the user's call.

After the script finishes, show the user the generated `vaults/{name}/vault.yml` and ask:
**"Here's the config. Edit it in the IDE if you want to adjust anything, then reply 'ready' to continue."**
Wait for confirmation before proceeding.

To delete a vault entirely later: `rm -rf vaults/{name}/` removes the bundle from the repo (config + agents + state). The data directory at `vault_path` is deleted separately.

See [reference.md](reference.md) for the full schema.

---

## Phase 3 — Ingest sources

If the user provided sources in Q4:

1. Write the sources to a temp file at `vaults/{vault-name}/state/queue/init-sources.txt`, one per line.
   - If the user passed a `.txt` file path, use that file directly (no copy needed).
   - Otherwise write the IDs/URLs they provided into the queue file above.
   - **Never** place this file inside the vault data dir.

2. Run ingest:
   ```bash
   VAULT_NAME="{vault-name}" bash .claude/scripts/batch-ingest.sh vaults/{vault-name}/state/queue/init-sources.txt
   ```

3. Report progress: show how many ingested OK, skipped, failed.

4. If all failed (e.g. network error), say so and suggest running manually later.

If the user skipped sources, say:
> "No sources ingested. Add them later with: `bash .claude/scripts/batch-ingest.sh <file>`"
> "Or run `/ingest {video_id}` to add one at a time."

---

## Phase 4 — Create atoms (integration-aware)

If `auto_atoms` is true AND at least one source was ingested successfully, launch one subagent per source. Subagents can run in parallel for **extraction**; **integration is serial within each subagent** (so each candidate claim sees its sibling writes from the same source).

Each subagent reads `vaults/{vault-name}/agents.md` for the atom schema and follows the integration loop documented there. The high-level shape:

1. **Orient against the existing wiki**. Read `{vault_path}/index/{atomization_lang}/index.md` for the topic catalog. For each topic the source plausibly touches, read the corresponding `moc/{atomization_lang}/{topic}.md` and skim the top-listed atoms. On a fresh vault these will be empty — that is fine, every claim becomes NEW.

2. **Read the source** at `raw/{atomization_lang}/{video}.md`.

3. **For each falsifiable claim found**, run a lookup against the existing corpus and pick a branch:

   | Branch | Trigger | Action |
   | --- | --- | --- |
   | **NEW** | No close match in the wiki | Write new atom at `wiki/{atomization_lang}/{topic}--{slug}.md` |
   | **STRENGTHEN** | Existing atom makes the same claim, same direction, compatible scope | **Edit** the existing atom — append a new entry to its `sources:` list with this video's `source_id`, `locator`, `url`, `excerpt`. Do not Write a new file. If the second corroboration shifts confidence (e.g. medium → high), update the field |
   | **CONFLICT** | Existing atom contradicts the new claim (opposite direction, incompatible threshold) | Write new atom **AND** append a HIGH/MEDIUM entry to `meta/contradictions.md` per CLAUDE.md §4.5.5 |
   | **REDUNDANT** | An entry with this same `source_id` already exists for this claim (re-ingest) | Skip silently |

   Lookup tool: `python3 .claude/scripts/retrieve.py --query "{claim}" --vault $VAULT_NAME --lang {atomization_lang} --top 3`. Fall back to globbing the relevant MOC if retrieve is unavailable.

4. **No fixed atom count**. The number emerges from what the source says. As a sanity check, a tactical/how-to video produces roughly `duration_sec / 120` distinct claims — far fewer for vlogs or sponsor-heavy content. If you find yourself padding to hit a number, you have already over-extracted; stop.

5. After every Write/Edit, the `on-file-write` hook fires automatically — do not run auto-link, qa, or propagate manually.

6. When all sources are processed:
   ```bash
   VAULT_NAME="{vault-name}" python3 .claude/scripts/vault-agent.py --incremental
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
