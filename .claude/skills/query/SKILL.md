---
name: query
description: Run a vault query with explicit language override. Bypasses auto-detection when you need to force a specific language.
allowed-tools: Read Bash(python3)
---

Run a query against the vault with explicit language control.

Usage: `/query [--lang es] "{question}"`

Steps:
1. Set LANG from --lang flag (default: primary language from vault.yaml)
2. Follow the indexing protocol (CLAUDE.md §INDEXING PROTOCOL) using ONLY {LANG} files:
   a. Read `index/{LANG}/index.md` — identify relevant topic(s)
   b. Read `moc/{LANG}/{topic}.md` for matching topic(s)
   c. Read shortlisted atoms from `wiki/{LANG}/` (3-6 max)
   d. Check `meta/contradictions.md` for active conflicts
3. Detect response regime (A/B/C per CLAUDE.md §4.6)
4. Draft response following the regime template from `meta/RESPONSE_TEMPLATES.md`
5. Apply pre-output checklist (CLAUDE.md §pre-output checklist):
   - Word count within ceiling (A=250/B=600/C=1000)
   - No anglicisms (substitution table applied)
   - Each step/cell has exactly one [[atom]] citation
   - Each number backed by source_id
   - No intro filler, no trailing summary
   - Conflict caveat if HIGH/MEDIUM active
6. Save to `queries/{LANG}/{topic}--{question-slug}.md` if synthesis is new

The language flag overrides auto-detection — useful when testing ES responses from an EN session.
