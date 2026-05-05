---
name: suggest-sources
description: Find new YouTube videos / web pages worth ingesting to fill thin topics. Reads /audit's "Suggested New Sources" table and runs WebSearch for each high-demand topic, returning candidate URLs with relevance hints. Does NOT auto-ingest — surfaces options for the user to approve.
allowed-tools: Bash(python3 .claude/scripts/vault-agent.py .claude/scripts/resolve-vault.sh) Read WebSearch
---

# /suggest-sources

Closes the loop between `/audit`'s demand-vs-coverage suggestions and concrete sources to ingest. The user decides which to ingest — this skill never writes to the vault.

## When to use

- After `/audit` flagged "Suggested New Sources" with high `demand_ratio`
- When the user asks "what should I ingest next about X?"
- When cached queries reveal recurring topics with thin coverage

## Steps

0. **Resolve vault**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Stop on non-zero exit (ambiguous vault) — surface the error and ask which vault to use.

1. **Get the demand table** from `/audit --output json` or, if missing, run a fresh audit:

   ```bash
   python3 .claude/scripts/vault-agent.py --vault "$VAULT_PATH" --output json
   ```

   The shell-side audit doesn't currently print the suggestions block in JSON output — read the latest `meta/agent-reports/agent-report-YYYY-MM-DD.md` and extract the **Suggested New Sources** table. If that block is absent (no cached queries → no demand signal), STOP and tell the user: "No demand signal yet — add some queries first or pass topics manually with `/suggest-sources <topic1> <topic2>`."

2. **For each topic** in the table (cap at top 5 by demand_ratio), run **2-3 WebSearch queries** crafted from the topic + vault domain context (read `vaults/{name}/agents.md` for domain hints — e.g. "@OptimizeMyAirbnb channel" for OMA vault).

   Search query templates by source type:

   - **YouTube** (preferred for OMA-style vaults — transcripts available, free):
     `<topic> site:youtube.com "OptimizeMyAirbnb"` (or whatever channel the vault tracks)
     `<topic> Airbnb host tips youtube`
   - **Web** (fallback when YouTube is thin):
     `<topic> Airbnb host guide 2025`
     `<topic> short-term rental best practices`

   Translate the topic into the **first enabled lang** of the vault for the query (e.g. `precio-base` → `base price` for an EN-first vault). Topic slugs aren't search-friendly raw.

3. **Compose the report** in markdown — do NOT write it anywhere; print to chat:

   ```markdown
   # Source suggestions — <vault-name>

   _Topics ranked by demand_ratio (queries × thinness of coverage). Pick the ones to ingest._

   ## 1. `<topic>` — demand_ratio X.YZ (Q queries, A atoms)

   **Suggested searches**:
   - "<query 1>" → top result: <url> — <why it's relevant>
   - "<query 2>" → top result: <url> — <why it's relevant>

   **To ingest**: `/ingest <video_id_or_url>`
   ```

4. **Annotate quality signals** for each candidate URL:
   - Author/channel reputation (does the vault already cite this source?)
   - Date (recency matters — see CLAUDE.md §5 score formula)
   - Whether it has YouTube subtitles available (skip if not — `yt-dlp` would NO_SUBS-skip)

5. **Refuse to auto-ingest**. End the report with: "Reply with `/ingest <id>` for each one you want, or paste a list and I'll batch-ingest."

## Constraints

- Max 5 topics per run (token budget — WebSearch is expensive)
- Max 3 search queries per topic
- Skip topics with `demand_ratio < 1.0` AND `atoms > 5` (already well-covered)
- Never invent URLs — if WebSearch returns nothing relevant, say "no good candidates found, try ingesting from a known channel manually"

## Why this is a skill, not a script

WebSearch is an LLM tool, not a CLI. The agent must read search results and judge relevance — that's pattern matching, not pure scoring. Keeping this in a skill (vs. a Python script) means the agent can adapt search queries based on what comes back, instead of running a fixed pipeline that produces noise.
