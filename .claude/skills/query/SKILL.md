---
name: query
description: Run a vault query with explicit language override. Bypasses auto-detection when you need to force a specific language.
allowed-tools: Read Bash(python3)
---

Run a query against the vault with explicit language control.

Usage: `/query [--lang es] "{question}"`

Steps:
1. Set LANG from --lang flag (default: primary language from vault.yaml)
2. **Pre-load atoms via BM25 retrieval (zero navigation tokens)**:
   ```bash
   python3 scripts/retrieve.py --query "{question}" --lang {LANG} --vault "$VAULT_PATH" --top 6
   ```
   This returns the 6 most relevant atoms pre-loaded as JSON — no index/MOC navigation needed.
   Read the returned JSON directly as your atom context.
3. If retrieval returns 0 results OR the question needs broader context:
   Fall back to manual indexing: read `index/{LANG}/index.md` → `moc/{LANG}/{topic}.md` → atoms
4. Check `meta/contradictions.md` for active conflicts on cited atoms
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
