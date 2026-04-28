---
name: audit
description: Full vault health audit. Runs vault-agent.py (orphans, stale, missing translations, contradictions) + batch QA report.
allowed-tools: Bash(python3 scripts/vault-agent.py python3 scripts/atom-qa.py)
---

Run a full vault health audit.

Steps:
1. `python3 scripts/vault-agent.py --vault "$VAULT_PATH"`
   - Detects: orphans (atoms not in any MOC), stale claims (>180 days), topic gaps, broken index links, missing translations, unresolved contradictions
   - Writes: `meta/agent-report-{date}.md`
2. `python3 scripts/atom-qa.py --all --vault "$VAULT_PATH"`
   - Checks all atoms in all enabled languages
   - Writes per-atom reports to `meta/qa-reports/`
3. Summarize findings:
   - Counts: orphans, stale, missing translations, QA failures
   - List all CRITICAL QA failures by atom
   - List missing translations (primary → secondary)
   - List unresolved contradictions count
4. Recommend next actions:
   - If missing translations > 0: suggest running `/translate {stem}` for each
   - If QA critical failures: list atoms to fix
   - If orphans > 5: suggest running `python3 scripts/auto-link.py --all`
   - If stale > 10: suggest prioritizing re-verification of those atoms
