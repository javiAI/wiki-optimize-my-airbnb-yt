# Phase 2: Execution Tasks

**Status**: Phase 2 is approved and in_progress.

Execute tasks in order: O3 (if needed from Phase 1), O4, O5, O6.

---

## O3: Language Consistency — Phase 1 Carryover

If not completed in Phase 1, execute now. See PHASE_1_TASKS.md for details. If already done, skip to O4.

---

## O4: Contradiction Detection L1 (3 hours)

### Purpose
Add real-time conflict detection to §4.2 (QUERY operation) so users see conflicting advice immediately, not just during lint audits.

### Implementation

1. **Add conflict-check logic to §4.2 step 6**
   - When selecting atom candidates for shortlist, cross-reference each atom's topics
   - For each atom selected, scan MOC for other atoms with same topic
   - Build conflict matrix: does other atom have opposite claim?
   - Mark conflicts for display

2. **Update CLAUDE.md kernel (§4.2.6a — new section)**
   ```
   6a. CONFLICT CHECK (new substep)
       For each candidate atom:
       - Scan MOC[topics[0]] for other atoms
       - If same topic, different claim: flag as "potential_conflict"
       - Check meta/contradictions.md: resolved or unresolved?
       - If unresolved: add caveat to response
   ```

3. **Create scoring for conflict severity**
   - Same topic, explicit contradiction: severity=HIGH
   - Same topic, conflicting evidence: severity=MEDIUM
   - Related topic, different recommendation: severity=LOW
   - Use severity to decide whether to flag in response

4. **Create conflict display template**
   ```markdown
   ⚠️ **Conflicting advice**: [[atom-A]] recommends X, while [[atom-B]] recommends Y.
   **Confidence**: atom-A is higher-confidence (8.1 vs 6.3 based on {{recency|popularity}}).
   **Caveat**: atom-B's approach applies if [condition].
   See [[meta/contradictions]] for full analysis.
   ```

5. **Test with known contradictions**
   - Run a query that touches the O2-resolved orphan-night contradiction
   - Verify: response includes conflict caveat if both atoms in shortlist
   - Verify: caveat cites higher-confidence atom as primary

6. **Update `log.md`**
   ```
   ## [2026-04-25] O4 complete | Contradiction detection L1
   - Added §4.2.6a conflict-check substep to CLAUDE.md kernel
   - Implemented severity scoring (HIGH/MEDIUM/LOW)
   - Created conflict caveat template
   - Tested with orphan-night contradiction
   ```

7. **Git commit**
   ```bash
   git commit -m "O4: Contradiction detection L1 (real-time conflict flagging)"
   ```

### Verification Checklist
- [ ] §4.2.6a added to CLAUDE.md
- [ ] Severity scoring defined and documented
- [ ] Conflict template created
- [ ] Test query executed against known conflict
- [ ] Response includes caveat with correct format
- [ ] `log.md` updated
- [ ] Git commit made

---

## O5: Response Format Templates (2.5 hours)

### Purpose
Standardize response structure by query type (regime) to ensure consistency and completeness.

### Implementation

1. **Create templates document**
   ```bash
   touch $VAULT_PATH/queries/RESPONSE_TEMPLATES.md
   ```

2. **Define Regime A (Narrow Factual) template**
   ```markdown
   **Question**: <user question>
   
   **Answer**: <direct answer, 1-2 sentences>
   
   **Applies only if**: <conditions where answer is valid>
   
   **See also**: [[related-atom-1]], [[related-atom-2]]
   
   **Confidence**: High (based on [[source-id]], 0.9)
   ```
   - Example: "¿4.8 rating es bueno?" → answer with tier table + conditions

3. **Define Regime B (Tactical Multi-Palanca) template**
   ```markdown
   **Question**: <user question>
   
   **Approach**: <intro explaining the strategy>
   
   **Steps**:
   1. [[atom-1]] — <step 1 summary>
   2. [[atom-2]] — <step 2 summary>
   3. [[atom-3]] — <step 3 summary>
   
   **Why this works**: <explanation of interdependencies>
   
   **Expected outcome**: <what to expect>
   
   **Caveats**: [[atom-caveat]] applies if <condition>
   
   **Confidence**: Medium-High (based on [[source-A]], [[source-B]])
   ```
   - Example: "¿Cómo optimizar precio para noche huérfana?" → 3-step approach

4. **Define Regime C (Taxonomic/Broad) template**
   ```markdown
   **Question**: <user question>
   
   **Overview**: <landscape of options/factors>
   
   **Comparison**:
   | Factor | Option A | Option B | Option C |
   |--------|----------|----------|----------|
   | [[aspect-1]] | ... | ... | ... |
   | [[aspect-2]] | ... | ... | ... |
   
   **How to choose**: <decision heuristic>
   - Use Option A if [[condition-a]]
   - Use Option B if [[condition-b]]
   
   **See also**: [[related-topic-1]], [[related-topic-2]]
   
   **Confidence**: Medium (incomplete coverage; only 8 of 12 aspects covered)
   ```
   - Example: "¿Todas las tácticas de pricing?" → comparison table

5. **Create `queries/RESPONSE_TEMPLATES.md` file**
   ```bash
   # Write header explaining when to use each template
   # Include all 3 templates above with full examples
   ```

6. **Audit existing queries**
   - List all files in `queries/`
   - Check each against nearest template
   - If format differs significantly: reformat to match template
   - Git commit reformat batch: `git commit -m "O5: Reformat existing queries to templates"`

7. **Add template reference to §4.2 (CLAUDE.md kernel)**
   - After step 9 (response generation), add:
   ```
   9a. FORMAT CHECK
       - Identify query regime (A/B/C from step 4)
       - Match response to {{regime}}_TEMPLATE from queries/RESPONSE_TEMPLATES.md
       - Verify all required sections present
   ```

8. **Update `log.md`**
   ```
   ## [2026-04-25] O5 complete | Response format templates
   - Created queries/RESPONSE_TEMPLATES.md with Regime A/B/C templates
   - Reformatted {{N}} existing queries to templates
   - Added §4.2.9a format-check substep
   ```

9. **Git commit**
   ```bash
   git commit -m "O5: Response format templates (Regime A/B/C standardization)"
   ```

### Verification Checklist
- [ ] `queries/RESPONSE_TEMPLATES.md` created with 3 templates
- [ ] Regime A template includes: answer + conditions + sources + confidence
- [ ] Regime B template includes: steps + why + caveats + sources + confidence
- [ ] Regime C template includes: comparison + decision heuristic + sources + confidence
- [ ] Existing queries reformatted (or marked "legacy" if exempt)
- [ ] §4.2.9a added to CLAUDE.md
- [ ] `log.md` updated
- [ ] Git commit made

---

## O6: Executable Checklists (1.5 hours)

### Purpose
Convert procedural advice in atoms into Obsidian-executable checklists that users can check off.

### Implementation

1. **Install Dataview plugin (if not present)**
   - User should have this; if not: Obsidian → Community Plugins → search "Dataview" → install
   - No special config needed for basic TASK queries

2. **Identify procedural atoms**
   - Scan `notes/` for atoms with claim containing "do", "steps", "procedure"
   - Example atoms: "dynamic-price-adjustments", "message-guest-before-checkout", "cleaning-between-guests"
   - Create list: `meta/procedural-atoms.txt` (one filename per line)

3. **Add TASK lists to procedural atoms**
   - For each atom in list, open the body section
   - After claim explanation, add checklist:
   ```markdown
   ## Procedure
   - [ ] Step 1 description
   - [ ] Step 2 description
   - [ ] Step 3 description
   ```

4. **Add Dataview summary block (optional)**
   - At bottom of atom, add optional completion tracker:
   ```
   ```dataview
   TASK
   WHERE file.path = this.file.path
   GROUP BY status
   ```
   ```
   - Obsidian will render completion counts (e.g., "2 of 3 done")

5. **Document checkbox convention**
   - Add note to `CLAUDE.md` kernel §4.2.9b:
   ```
   9b. CHECKBOXES IN ATOMS
       Procedural atoms may include task lists (- [ ] step).
       Users can check boxes in Obsidian to track progress.
       Dataview plugin aggregates completion status.
   ```

6. **Create example atom with checklist**
   - Pick 1 high-value atom (e.g., pricing optimization procedure)
   - Implement full checklist + Dataview block
   - Screenshot result (for docs)

7. **Batch-add checklists to other procedural atoms**
   - For each atom in `meta/procedural-atoms.txt`, add task list
   - Group in single git commit: `git commit -m "O6: Add executable checklists to {{N}} procedural atoms"`

8. **Update `log.md`**
   ```
   ## [2026-04-25] O6 complete | Executable checklists
   - Added task lists to {{N}} procedural atoms
   - Documented checkbox convention in §4.2.9b
   - Obsidian users can now track procedure completion via Dataview
   ```

9. **Git commit**
   ```bash
   git commit -m "O6: Executable checklists ({{N}} procedural atoms + Dataview integration)"
   ```

### Verification Checklist
- [ ] Dataview plugin installed and working
- [ ] {{N}} procedural atoms identified and listed in `meta/procedural-atoms.txt`
- [ ] Task lists added to all procedural atoms
- [ ] Dataview blocks added (optional but recommended for high-value atoms)
- [ ] Convention documented in §4.2.9b
- [ ] Example atom with full checklist visible in Obsidian
- [ ] `log.md` updated
- [ ] Git commit made

---

## After Phase 2 Completion

1. **Update CLAUDE.md YAML**
   ```yaml
   phase_2:
     status: "complete"
     progress: 100
   automation:
     current_phase: 3
     phase_status: "pending_approval"
   ```

2. **Measure vault quality**
   - Run: `scripts/quality-check.sh` (if exists)
   - Expected score improvement: 8.9 → 9.3

3. **Git commit**
   ```bash
   git commit -m "Phase 2 complete: Quality foundation (O3, O4, O5, O6)"
   ```

4. **Show Phase 3 summary**
   - Ready for: "Approve Phase 3"
