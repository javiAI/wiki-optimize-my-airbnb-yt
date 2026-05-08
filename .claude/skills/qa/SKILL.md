---
name: qa
description: Atom-level content QA. Checks completeness, URL format, acronym definitions, and conflicts. Use /audit for vault-level structural checks.
allowed-tools: Bash(python3 .claude/scripts/atom-qa.py .claude/scripts/resolve-vault.sh)
---

# /qa — Atom Content QA

Scope: **atom content**, not vault structure. See /audit for structural checks (orphans, stale, missing translations).

## Usage

```bash
/qa {stem}                  # Check one atom (primary language)
/qa {stem} --lang es        # Check one atom in specific language
/qa --all                   # Check all atoms in all enabled languages
/qa --all --lang es         # Check all atoms in one language
/qa --all --fix             # Check + auto-fix acronym definitions
```

## Steps

0. **Resolve vault (mandatory preamble)**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Prints `[wikiforge] Using vault: <name> (<path>)`. **If it exits non-zero, STOP** and ask the user which vault to QA; never pick silently.

1. Run `python3 .claude/scripts/atom-qa.py {args} --vault "$VAULT_PATH"`
2. Report results:
   - **CRITICAL** (pipeline-blocking): missing claim, no sources → must fix before atom is usable
   - **WARNING** (non-blocking): missing url, undefined acronym, invalid url format → fix when convenient
   - **PASS**: atom is clean
3. For `--all`, summarize: N passed, M failed. List all CRITICAL failures by stem.
4. If auto-fixable issues exist (acronym definitions), suggest: `--fix` flag or `/qa --all --fix`

Note: language purity (English-borrowing leakage in non-English atoms) is NOT enforced here. It's scored statistically by `/test-vault`'s `language_purity` rubric across N independent evaluators.

## When to use /qa vs /audit

Run `/qa` when you want to verify atom content quality — e.g. after `/ingest-queue` or `/translate`.
Run `/audit` when you want to check vault health — e.g. after a batch ingest session or weekly maintenance.
