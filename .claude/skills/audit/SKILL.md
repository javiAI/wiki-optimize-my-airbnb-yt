---
name: audit
description: Vault-level health audit. Two modes — structural (default; orphans, stale, missing translations, contradictions; fast, no LLM) and `--deep` (structural + semantic pass: numerical/framework/stance/concept-framing instabilities, new canonical positions). Does NOT re-run per-atom content checks — use /qa for that.
allowed-tools: Bash(python3 .claude/scripts/vault-agent.py .claude/scripts/resolve-vault.sh)
---

# /audit — Vault Health Audit

Two modes:

- **default (structural)** — orphans, stale, gaps, missing translations, broken links, contradiction count. Pattern-match only, no LLM, sub-second per lang.
- **`--deep`** — structural pass first, then a semantic pass that asks the LLM to flag cross-atom anomalies the structural pass cannot detect (numerical drift, framework versions, stance reversals, concept-framing collisions, new canonical positions). Output appended under `# Semantic findings` in the same report.

Scope: **vault structure** + (in deep mode) **cross-atom semantic drift**, not per-atom content. Complements /qa (which checks each atom's content).

## /audit vs /qa

| Check | /audit | /audit --deep | /qa |
|-------|--------|---------------|-----|
| Orphan atoms (not in any MOC) | ✅ | ✅ | ❌ |
| Stale last_verified | ✅ | ✅ | ❌ |
| Missing translations | ✅ | ✅ | ❌ |
| Broken index links | ✅ | ✅ | ❌ |
| Topic gaps (no MOC) | ✅ | ✅ | ❌ |
| Numerical/framework/stance drift | ❌ | ✅ | ❌ |
| New canonical positions | ❌ | ✅ | ❌ |
| Missing claim field | ❌ | ❌ | ✅ |
| URL format validation | ❌ | ❌ | ✅ |
| Acronym first-use definition | ❌ | ❌ | ✅ |

## Usage

```text
/audit                          # Structural, all languages
/audit --deep                   # Structural + semantic pass (LLM-driven)
/audit --lang es                # Structural, ES only
/audit --deep --lang es,en      # Deep audit on ES and EN
/audit --since 2026-04-01       # Only atoms modified since date
/audit --output json            # Machine-readable stats (structural counters only)
```

`--deep` is auto-fired by `on-ingest-batch-close.sh` every `vault.yml.maintenance.audit_every_n_ingests` atoms (default 10) when `audit_mode: deep`. The hook prints an advisory; you still run `/audit --deep` manually to refresh the report.

## Steps

0. **Resolve vault (mandatory preamble)**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Prints `[wikiforge] Using vault: <name> (<path>)`. **If it exits non-zero, STOP** and ask the user which vault to audit; never pick silently.

1. Run: `python3 .claude/scripts/vault-agent.py --vault "$VAULT_PATH" [flags]`
2. Report findings grouped by severity:
   - **Action required**: orphans > 5, missing translations > 0, broken index links
   - **Monitor**: stale claims, topic gaps
   - **Info**: contradiction count, ingest recommendations
3. Suggest next actions:
   - Orphans → `python3 .claude/scripts/auto-link.py --all --lang {lang}`
   - Missing translations → `/translate {stem}`
   - Stale → prioritize re-verification, `/ingest` new sources on that topic
   - "Suggested New Sources" block present → run `/suggest-sources` to turn topics into concrete URLs to ingest
   - Want to know what to ask next → `/suggest-questions` mines the corpus for answerable + gap-revealing questions
