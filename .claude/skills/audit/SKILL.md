---
name: audit
description: |-
  Vault-level health audit. Two modes:
    - structural (default): orphans, stale atoms, missing propagations across
      enabled langs, broken cross-refs, topic gaps. Pattern-match only, no LLM,
      sub-second per lang.
    - `--deep`: structural pass + semantic pass that flags numerical drift,
      framework version shifts, stance reversals, concept-framing collisions,
      and new canonical positions across atoms (LLM-driven).
  Use when the user asks to "audit the vault", "check vault health", "find
  orphans / stale atoms / gaps", or after a batch of ingests. The
  on-ingest-batch-close hook auto-fires a `--deep` advisory every N atoms
  (configurable in `vault.yml.maintenance.audit_every_n_ingests`); the user
  still re-runs `/audit --deep` manually to refresh the on-disk report.
  Use `/qa` for per-atom content checks (claim, URL format, multilingual schema).
allowed-tools: Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/vault-agent.py:*)
arguments:
  - name: --deep
    description: "Add semantic pass (LLM) on top of structural checks."
  - name: --lang
    description: "Comma-separated language codes to audit (e.g. `es` or `es,en`). Defaults to every enabled lang."
  - name: --since
    description: "Only audit atoms modified on or after this date (`YYYY-MM-DD`)."
  - name: --incremental
    description: "Only audit atoms changed in git since last commit."
  - name: --stale-days
    description: "Override the default stale threshold (days since `last_verified`)."
  - name: --output
    description: "`text` (default; writes the markdown report) or `json` (machine-readable structural counters)."
  - name: --dry-run
    description: "Print the report to stdout without writing the dated file."
---

# /audit — Vault Health Audit

Two modes:

- **default (structural)** — orphans, stale, gaps, missing propagations, broken cross-refs, contradiction count. Pattern-match only, no LLM, sub-second per lang.
- **`--deep`** — structural pass first, then a semantic pass that asks the LLM to flag cross-atom anomalies the structural pass cannot detect (numerical drift, framework versions, stance reversals, concept-framing collisions, new canonical positions). Output appended under `# Semantic findings` in the same report.

Scope: **vault structure** + (in deep mode) **cross-atom semantic drift**, not per-atom content. Complements `/qa` (which checks each atom's content).

## /audit vs /qa

| Check | /audit | /audit --deep | /qa |
|-------|--------|---------------|-----|
| Orphan atoms (not in any MOC) | ✅ | ✅ | ❌ |
| Stale `last_verified` | ✅ | ✅ | ❌ |
| Missing propagations across langs | ✅ | ✅ | ❌ |
| Broken cross-refs / index links | ✅ | ✅ | ❌ |
| Topic gaps (no MOC) | ✅ | ✅ | ❌ |
| Numerical / framework / stance drift | ❌ | ✅ | ❌ |
| New canonical positions | ❌ | ✅ | ❌ |
| Missing `claim` field | ❌ | ❌ | ✅ |
| URL format validation | ❌ | ❌ | ✅ |
| `excerpt_source` / `propagated_from` schema | ❌ | ❌ | ✅ |

## Usage

```text
/audit                          # Structural, every enabled lang
/audit --deep                   # Structural + semantic pass (LLM-driven)
/audit --lang es                # Structural, ES only
/audit --deep --lang es,en      # Deep audit on ES and EN
/audit --since 2026-04-01       # Only atoms modified since date
/audit --output json            # Machine-readable counters (structural only)
```

## Steps

1. **Resolve vault**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Sets `$VAULT_NAME` and `$VAULT_PATH`. If it exits non-zero, **STOP** and ask the user which vault to audit — never pick silently.

2. **Run the audit**:

   ```bash
   python3 .claude/scripts/vault-agent.py --vault "$VAULT_PATH" [flags]
   ```

3. **Read the report**. Default mode writes `meta/agent-reports/agent-report-YYYY-MM-DD.md` (per vault) and prints a summary to stdout. `--output json` only emits stats to stdout. `--dry-run` prints the report without writing.

4. **Surface findings to the user**, grouped by severity:
   - **Action required**: orphans > 5, missing propagations > 0, broken cross-refs.
   - **Monitor**: stale claims, topic gaps.
   - **Info**: contradiction count, ingest recommendations.

5. **Suggest next actions** based on what the report flagged:
   - Orphans → `python3 .claude/scripts/auto-link.py --all --lang {lang}`
   - Missing propagations → `/propagate {stem}` (per-atom).
   - Stale → prioritize re-verification; `/ingest` new sources on that topic.
   - "Suggested New Sources" block present → `/suggest-sources` to turn topics into concrete URLs.
   - Want to know what to ask next → `/suggest-questions` mines the corpus for answerable + gap-revealing questions.

## Notes

- **Auto-fire on ingest**: `on-ingest-batch-close.sh` bumps a counter and prints a `/audit --deep` advisory every `vault.yml.maintenance.audit_every_n_ingests` atoms (default 10) when `audit_mode: deep`. The hook only prints the advisory; the on-disk report is refreshed when the user actually runs `/audit --deep`.
- **`/audit` vs `/qa`**: `/audit` is per-vault structure (and, with `--deep`, cross-atom semantics). `/qa` is per-atom content (claim, URL, schema). Run `/audit` after batch ingests or weekly; run `/qa` after content edits.
- **Vault layout**: works on both v1 (kind-first) and v2 (lang-first) layouts — the script auto-detects via filesystem-probing.
