# Phase 1: Execution Tasks

**Status**: Phase 1 is approved and in_progress.

Execute tasks in order. After each task completes, the system updates CLAUDE.md YAML state and commits. Move to next task only after previous task is verified complete.

---

## O1: Hierarchical Indices (4 hours)

### Steps

1. **Read current `index.md` structure**
   - Observe: 344 lines, flat list grouped by category (Temas, Atómicos, Queries, Fuentes)
   - Measure: Count entries per category

2. **Create `index/` subdirectory structure**
   ```
   vault/
   ├── index.md          (L1 — new, compact overview)
   ├── index/            (L2 — category breakdown)
   │   ├── topics.md     (all MOCs)
   │   ├── atoms.md      (all atoms by topic)
   │   └── queries.md    (cached queries)
   └── index.md.old      (backup of original)
   ```

3. **Partition content from original `index.md`**
   - Extract all MOC lines → save as `index/topics.md` (with one-liner descriptions)
   - Extract all atom lines → save as `index/atoms.md` (grouped by topic)
   - Extract all query lines → save as `index/queries.md` (grouped by topic)
   - Keep system notes (L1 overview) in new `index.md`

4. **Create new `index.md` (L1 overview only)**
   ```markdown
   # Vault Index — Optimize My Airbnb

   **Quick Navigation**:
   - [[index/topics]] — All Maps of Content (MOCs) by theme
   - [[index/atoms]] — All atomic claims by topic
   - [[index/queries]] — Cached queries (fast answers)
   - [[log]] — Activity log

   **Vault Health**: 156 atoms | 12 MOCs | 173 sources | Quality 8.52 → 8.9 (target)

   **Pages**:
   - [[meta/videos]] — Source inventory
   - [[meta/contradictions]] — Known conflicts
   - [[meta/glossary]] — Terminology
   ```

5. **Update all cross-links**
   - Any page currently linking to `[[index]]#atoms` → update to `[[index/atoms]]`
   - Any page linking to `[[index]]#queries` → update to `[[index/queries]]`
   - Search: `grep -r "index#" $VAULT_PATH` → check for broken anchors

6. **Verify in Obsidian**
   - Open vault in Obsidian
   - Click L1 links (index/topics, index/atoms, index/queries)
   - Confirm all page loads work
   - Graph view: no broken red links

7. **Measure token savings**
   ```bash
   wc -l index.md
   # Old: 344 lines ≈ 4k tokens
   # New: ≤100 lines ≈ 1.2k tokens
   # Savings: ≈2.8k tokens per query
   ```

8. **Git commit**
   ```bash
   git add vault/index.md vault/index/*.md vault/index.md.old
   git commit -m "O1: Hierarchical indices (344→100 lines, 4k→1.2k tokens)"
   ```

9. **Update CLAUDE.md YAML**
   - Set O1 status: "completed"
   - Set phase_1 progress: 1/3
   - Update last_update timestamp

### Verification Checklist
- [ ] Old index.md backed up as `index.md.old`
- [ ] New index.md ≤100 lines
- [ ] `index/topics.md`, `index/atoms.md`, `index/queries.md` created
- [ ] All cross-links updated (no `[[index]]#` anchors remain)
- [ ] Obsidian loads without broken links
- [ ] Git commit made with message "O1: ..."

---

## O2: Fix Q4 Contradiction — SKIPPED (2026-04-26)

**Status**: SKIPPED. Premise stale.

### Why skipped

This task was originally written assuming:
- The v1 question set (Q4 = orphan-night pricing question)
- A specific entry in `meta/contradictions.md` titled "Q4 orphan-night pricing" with two atoms in active conflict (raise vs discount)

Verified state on 2026-04-26 (post-O1):
- **v2.0 question set** (active baseline): Q4 is now "¿Debo activar Instant Book desde el principio?". The orphan-night question moved to Q6.
- **`meta/contradictions.md`** has 6 entries (Thu/Sun, review-removal pre/post-2025, refund-for-review scope, broken-vs-loophole, 5%-vs-10% adjustment, max-occupancy-vs-extra-fee). **No entry exists for orphan-night pricing.**
- **Only one orphan-night atom exists**: [[notes/pricing--orphan-night-strategy]] (drop min stay + 20% premium, `confidence: high`, `conflicts_with: []`). Internally consistent.

There is no contradiction to resolve. Skipping is the correct action.

### What to do instead

If a real contradiction surfaces in a future ingest batch, file it as `OX` in the next phase docs (do not retrofit O2). Phase 1 progress goes O1 → O3 (skipping O2).

---

## O3: Language Consistency (2 hours)

### Steps

1. **Define canonical format (verify against CLAUDE.md §3.2)**
   ```yaml
   ---
   claim: <one sentence capturing the core advice>
   topics: [topic1, topic2]
   confidence: high | medium | low
   sources:
     - source_id: <id>
       locator: <timestamp or page>
       excerpt: "<exact quote>"
   conflicts_with: []
   last_verified: YYYY-MM-DD
   ---
   <body: 3-8 lines, conditions & caveats>
   ```

2. **Audit atom naming consistency**
   - All atoms should be: `<topic>--<kebab-slug>.md`
   - Find outliers: `ls $VAULT_PATH/notes/ | grep -v -- "--"`
   - Rename any non-compliant files to follow pattern

3. **Check casing in frontmatter**
   - Scan all `topics:` lines → standardize capitalization
   - Use `meta/glossary.md` as source of truth for term names
   - Example: "orphan night" (lowercase, per glossary) not "Orphan Night"

4. **Audit claim brevity (1-2 sentences max)**
   - Read each atom's `claim:` field
   - If > 2 sentences or has numbered list → split into separate atoms or move detail to body
   - Rewrite for clarity if needed

5. **Audit body length (≤ 8 lines)**
   - Count body lines (after `---` closing, before next `## ` section if any)
   - If > 8 lines: either trim explanations, split into 2 atoms, or move to conditions section
   - Conditions should be marked `**Applies only if:**` or `**Caveat:**`

6. **Check source excerpt formatting**
   - All excerpts should be in double quotes: `"text"`
   - Excerpts ≤50 chars (summary, not full quote)
   - Missing excerpts? Add them (re-read source if needed with offset/limit)

7. **Standardize confidence levels**
   - Map: very_high → high, pretty_high → high, medium_low → medium, etc.
   - All should be one of: high | medium | low

8. **Verify no duplicate atoms**
   - Look for atoms with identical or near-identical claims under same topic
   - If found: merge sources into single atom, delete duplicate
   - Merge script (if exists): `scripts/merge-atoms.py <atom1> <atom2>`

9. **Git commit (iterative)**
   - After each fix type, commit:
   ```bash
   git add vault/notes/
   git commit -m "O3: Standardize atom naming/format (batch 1/4)"
   ```
   - Repeat for: naming (batch 1), casing (batch 2), claim length (batch 3), body length (batch 4)

10. **Final verification**
    - Random sampling: pick 10 atoms, verify all follow format
    - Check `log.md`: add entry for O3 completion
    - Obsidian: scan Graph view for any new errors

11. **Update CLAUDE.md YAML**
    - Set O3 status: "completed"
    - Set phase_1 progress: 3/3, status: "complete"

### Verification Checklist
- [ ] All atoms named `<topic>--<kebab>.md`
- [ ] All topics use canonical casing (per glossary)
- [ ] All claims: 1-2 sentences max
- [ ] All bodies: ≤ 8 lines
- [ ] All source excerpts: quoted, ≤50 chars, present
- [ ] All confidence: high | medium | low only
- [ ] No duplicate atoms (deduped)
- [ ] 4 sequential git commits made
- [ ] Random 10-atom sample verified

---

## After Phase 1 Completion

1. **Update CLAUDE.md YAML**
   ```yaml
   phase_1:
     status: "complete"
     progress: 100
   automation:
     current_phase: 2
     phase_status: "pending_approval"
   ```

2. **Git commit final state**
   ```bash
   git commit -m "Phase 1 complete: Critical path optimizations (O1, O2, O3)"
   ```

3. **Announce Phase 2 readiness**
   - Show: docs/PHASE_2_SUMMARY.md
   - Wait for: "Approve Phase 2"

