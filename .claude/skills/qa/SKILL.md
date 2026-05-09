---
name: qa
description: |-
  Atom-level content QA. Validates each atom's completeness (claim, sources, last_verified),
  URL deep-link format, multilingual schema (per-source `excerpt_source`, top-level
  `propagated_from` coherence) and surfaces known conflicts against `meta/contradictions.md`.
  Optional `--fix` auto-injects missing source URLs derived from `source_id + locator`.
  Use when the user asks to "qa", "validate atoms", "check atom quality / health", or
  before publishing / running `/test-vault`. Use `/audit` for vault-level structural checks
  (orphans, stale, missing propagations, broken cross-refs).
allowed-tools: Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/atom-qa.py:*)
arguments:
  - name: stem
    description: "Atom stem (e.g. `pricing--base-price`). Omit when using `--all`."
  - name: --lang
    description: "Language code (`en`, `es`, …). Defaults to the first enabled lang for a single-atom run, or every enabled lang with `--all`."
  - name: --all
    description: "Check every atom across enabled langs."
  - name: --fix
    description: "Auto-inject missing source URLs from `source_id + locator`."
  - name: --source-type
    description: "Source-type used to validate URL format (`youtube` by default). Per-vault default will move to `vault.yml`."
---

# /qa — Atom Content QA

Scope: **atom content**, not vault structure. Run `/audit` for structural checks.

## Usage

```text
/qa <stem>              # Check one atom in the first enabled lang
/qa <stem> --lang es    # Check one atom in a specific lang
/qa --all               # Every atom, every enabled lang
/qa --all --lang es     # Every atom in one lang
/qa --all --fix         # Same + auto-inject missing source URLs
```

## Steps

1. **Resolve vault**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Sets `$VAULT_NAME` and `$VAULT_PATH`. If it exits non-zero, **STOP** and ask the user which vault to QA — never pick silently.

2. **Run the script**:

   ```bash
   python3 .claude/scripts/atom-qa.py [<stem>] [--lang <lang>] [--all] [--fix] --vault "$VAULT_PATH"
   ```

3. **Read the result**. Reports persist at `meta/qa-reports/{stem}.{lang}.json` only when violations exist; clean atoms have no report (any stale report is deleted).

4. **Summarise** for the user, grouped by severity:
   - **CRITICAL** (pipeline-blocking): missing `claim`, no `sources`, invalid `propagated_from`. Must fix before the atom is usable.
   - **WARNING** (informational): missing source URL, invalid URL format, missing `last_verified`, missing or unknown `excerpt_source`, propagated atom carrying `excerpt_source: native_atomization`. Fix when convenient.
   - **INFO**: atom appears in `meta/contradictions.md` — verify the conflict is documented.

5. For `--all`, give one summary line per lang (`[lang] N/M passed, K failed`) and list every CRITICAL by stem. Don't dump warnings unless the user asks.

6. If `--fix` was passed, report how many URLs were auto-injected. The script re-runs QA after fixes; the final report reflects post-fix state.

## Output schema

A persisted report at `meta/qa-reports/{stem}.{lang}.json` has this shape:

```json
{
  "atom": "topic--slug",
  "lang": "en",
  "timestamp": "ISO-8601",
  "pass": true,
  "critical_count": 0,
  "warning_count": 0,
  "violations": [
    {"type": "...", "severity": "critical|warning|info", "message": "...", "auto_fixable": false}
  ],
  "auto_fixable": []
}
```

## Notes

- **Language purity is not enforced here.** Source-language calque leakage in cross-lang atoms is scored statistically by `/test-vault`'s `language_purity` rubric across N independent evaluators — not by string-mapping.
- **URL-format validation** uses `--source-type youtube` by default. Pass `--source-type <other>` when the vault sources are not YouTube; the per-vault default will move to `vault.yml` in a follow-up.
- **`/qa` vs `/audit`**: `/qa` is per-atom content; `/audit` is per-vault structure. Run `/qa` after content edits (ingest, propagation, manual fixes); run `/audit` after batch operations or weekly.
