---
name: qa
description: Run QA checks on one or all atoms. Reports completeness, URL format, anglicism, and conflict violations.
allowed-tools: Bash(python3 scripts/atom-qa.py)
---

Run atom QA checks.

Usage:
- `/qa {stem}` — check one atom in primary language
- `/qa {stem} --lang es` — check one atom in specific language
- `/qa --all` — check all atoms in all enabled languages
- `/qa --all --lang en` — check all atoms in one language

Steps:
1. Run `python3 scripts/atom-qa.py {args} --vault "$VAULT_PATH"`
2. Parse the JSON output (written to `meta/qa-reports/`)
3. Report:
   - PASS: atom is clean
   - WARNINGS: list each (url format, anglicism) with suggested fix
   - CRITICAL FAIL: list each (missing claim, no sources) — must fix before using atom

For `--all`, summarize: N passed, M failed. List all CRITICAL failures.
Auto-fixable issues (missing url field): suggest running `python3 scripts/deep_link.py --backfill`.
