---
name: suggest-sources
description: |-
  Find new sources (videos, web pages, PDFs) worth ingesting to fill thin
  topics. Reads the latest `/audit` report's "Suggested New Sources" table
  (topics ranked by `demand_ratio`) and runs `WebSearch` for each, returning
  candidate URLs with relevance hints. **Never auto-ingests** — surfaces
  options for the user to approve.
  Use when the user asks "what should I ingest next?", "find sources for X",
  "fill gaps", or runs `/suggest-sources`. Natural follow-up to `/audit`
  when the demand table is non-empty. Pass topics positionally to skip the
  audit lookup (`/suggest-sources pricing market-selection`).
allowed-tools: Read, Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/vault-agent.py:*), WebSearch
arguments:
  - name: topics
    description: "Zero or more topics. With one or more, search those directly (skip audit lookup). With none, read the latest audit report's demand table and use the top 5 by `demand_ratio`."
---

# /suggest-sources — Source discovery for thin topics

Closes the loop between `/audit`'s demand-vs-coverage signal and concrete URLs to ingest. The user decides what to ingest — this skill never writes to the vault.

## When to use

- After `/audit` flagged topics in the **Suggested New Sources** block (high `demand_ratio`).
- The user asks *"what should I ingest next about X?"* (pass `X` as a positional topic).
- Cached queries reveal recurring topics with thin coverage.

## Steps

0. **Resolve vault** (mandatory preamble):

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Stop on non-zero exit and ask which vault to mine.

1. **Determine the topic list**:
   - **If positional `topics` were passed**: use them directly. Skip steps 2–3.
   - **Otherwise**: extract the demand table from the latest `$VAULT_PATH/meta/agent-reports/agent-report-YYYY-MM-DD.md` (or run a fresh audit: `python3 .claude/scripts/vault-agent.py --vault "$VAULT_PATH" --output json`). The block is titled "Suggested New Sources". If absent (no cached queries → no demand signal), STOP and tell the user: *"No demand signal yet — add some queries first or pass topics manually with `/suggest-sources <topic1> <topic2>`."*

2. **Pick the top 5** topics by `demand_ratio`. Skip any with `demand_ratio < 1.0` AND `atoms > 5` (already well-covered).

3. **Read the per-vault search recipe**. `vaults/$VAULT_NAME/agents.md` should contain a **Source discovery templates** section with:
   - Domain context (e.g. *"Vault tracks the @OptimizeMyAirbnb channel"*)
   - Search query templates per source type
   - Topic-translation hints (slugs → search-friendly terms)
   - Quality signals to annotate per candidate

   **Fallback if the section is missing**: derive a generic template from `vault.yml#source.type`:
   - `youtube`: `<topic> site:youtube.com` / `<topic> tutorial`
   - `web`: `<topic> guide` / `<topic> best practices`
   - `pdf`: `<topic> filetype:pdf` / `<topic> whitepaper`

   Translate each topic slug into the first enabled lang of the vault (e.g. `precio-base` → `base price` for an EN-first vault) before composing search queries.

4. **For each topic, run 2–3 WebSearch queries** built from the templates. Read results and pick the most relevant candidate URL per query.

5. **Compose the report** in markdown — print to chat, do NOT write it anywhere:

   ```markdown
   # Source suggestions — <vault-name>

   _Topics ranked by demand_ratio (queries × thinness of coverage). Pick the ones to ingest._

   ## 1. `<topic>` — demand_ratio X.YZ (Q queries, A atoms)

   **Suggested searches**:
   - "<query 1>" → top result: <url> — <why it's relevant + quality signals>
   - "<query 2>" → top result: <url> — <why it's relevant + quality signals>

   **To ingest**: `/ingest <id_or_url>`
   ```

6. **Annotate quality signals** per candidate URL using the vault's `agents.md` list (or, in fallback, the source-type defaults):
   - **Authority**: does the vault already cite this creator / domain?
   - **Recency**: date of the source (older content discounts via score formula).
   - **Ingestability**: for `youtube`, does the video have transcripts? For `pdf`, is it accessible? For `web`, is there a paywall?

7. **Refuse to auto-ingest**. End the report with: *"Reply with `/ingest <id>` for each one you want, or paste a list and I'll batch-ingest."*

## Constraints

- **Max 5 topics per run** (token budget — `WebSearch` is expensive).
- **Max 3 search queries per topic**.
- **Never invent URLs** — if WebSearch returns nothing relevant, say *"no good candidates found, try ingesting from a known source manually"*.
- **Honour the per-vault recipe**. Do not reuse one vault's channel names or domains for another vault — the recipe in `agents.md` is the source of truth.

## Why this is a skill, not a script

`WebSearch` is an LLM tool, not a CLI. The agent must read search results and judge relevance — pattern matching, not pure scoring. Keeping this in a skill means the agent can adapt search queries based on what comes back, instead of running a fixed pipeline that produces noise.
