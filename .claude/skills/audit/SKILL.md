---
name: audit
description: Vault-level health audit. Checks structure (orphans, stale, missing translations, contradictions). Does NOT re-run per-atom content checks — use /qa for that.
allowed-tools: Bash(python3 scripts/vault-agent.py)
---

# /audit — Vault Health Audit

Scope: **vault structure**, not atom content. Complements /qa (which checks atom content).

## /audit vs /qa

| Check | /audit | /qa |
|-------|--------|-----|
| Orphan atoms (not in any MOC) | ✅ | ❌ |
| Stale last_verified | ✅ | ❌ |
| Missing translations | ✅ | ❌ |
| Broken index links | ✅ | ❌ |
| Topic gaps (no MOC) | ✅ | ❌ |
| Missing claim field | ❌ | ✅ |
| URL format validation | ❌ | ✅ |
| Anglicism violations | ❌ | ✅ |

## Usage

```
/audit                          # Full audit, all languages
/audit --lang es                # Audit only ES
/audit --lang es,en             # Audit ES and EN
/audit --since 2026-04-01       # Only atoms modified since date
/audit --output json            # Machine-readable stats
```

## Steps

1. Run: `python3 scripts/vault-agent.py --vault "$VAULT_PATH" [flags]`
2. Report findings grouped by severity:
   - **Action required**: orphans > 5, missing translations > 0, broken index links
   - **Monitor**: stale claims, topic gaps
   - **Info**: contradiction count, ingest recommendations
3. Suggest next actions:
   - Orphans → `python3 scripts/auto-link.py --all --lang {lang}`
   - Missing translations → `/translate {stem}`
   - Stale → prioritize re-verification, `/ingest` new sources on that topic
