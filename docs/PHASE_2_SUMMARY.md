# Phase 2: Quality Foundation

**Objective**: Build systematic quality assurance into the vault.

After Phase 1's structural improvements, Phase 2 focuses on content quality: detecting and preventing contradictions, enforcing response format consistency, and creating executable checklists that guide future ingests.

---

## What Phase 2 Accomplishes

- **O3 (Language Consistency)**: See Phase 1 (carried over from phase_1 task list; actually belongs here)
- **O4 (Contradiction Detection L1)**: Automated detection of semantic conflicts at atom read-time, not just post-hoc audit
- **O5 (Response Format Templates)**: Standardized query response structure with mandatory sections (scope, assumptions, caveats)
- **O6 (Executable Checklists)**: Task lists in atoms that Obsidian can execute (Dataview integration)

**Effort**: ~9 hours total  
**Quality Impact**: Quality score 8.9 → 9.3  
**Unlock**: Phase 3 (Automation) depends on Phase 2 quality gates

---

## Optimizations

### O3: Language Consistency (2 hours)

**Covered in Phase 1 Tasks.** Restate here: standardize all atoms to YAML format, consistent terminology, proper claim brevity, source citations.

---

### O4: Contradiction Detection L1 (3 hours)

**What it does**: Implement a heuristic that flags potential contradictions the moment an atom is read during query execution, not just during lint sweeps.

**Current state**: Contradictions only surfaced by manual lint passes (§4.3).

**Target state**: When reading an atom during query (step 6 of §4.2), automatically check:
- Do any other atoms share this topic but have opposite `claim`?
- Is the `confidence` of this atom lower than the conflicting one?
- Has this been resolved in `meta/contradictions.md`?

If unresolved conflict detected: flag in response with caveat "Note: conflicting advice from [[other-atom]]; confidence 0.8 vs 0.6."

**Why**: Users see the conflict up-front, reducing trust issues. Encourages proactive resolution.

**Implementation**: Add to §4.2 step 6 a sub-step "Check for conflicts before citing".

---

### O5: Response Format Templates (2.5 hours)

**What it does**: Define canonical response structure for different query types.

**Templates by regime (§4.2.a)**:
- **Regime A (factual)**: Question → Direct answer (1-2 sentences) → Conditions/exceptions → Sources → Confidence level
- **Regime B (tactical)**: Question → 3-5 step list → Why this approach → Expected outcome → Caveats → Sources
- **Regime C (taxonomic)**: Question → Intro → Table/list of options (comparison) → How to choose → Sources

**Why**: Consistent structure reduces cognitive load for users. Easier to validate completeness.

**Implementation**: Create `queries/RESPONSE_TEMPLATES.md` with templates + examples.

---

### O6: Executable Checklists (1.5 hours)

**What it does**: Convert advice from atoms into Obsidian-executable checklists.

**Example**: Atom `pricing--dynamic-adjustments.md` contains a procedure. Add a Dataview block:

```
```dataview
TASK
WHERE file.path = this.file.path
GROUP BY status
```
```

Then in the body:
```markdown
## Procedure
- [ ] Log into PriceLabs
- [ ] Review last 7 days performance
- [ ] Adjust base price ±5-10%
- [ ] Check competitor pricing
- [ ] Publish changes
```

Obsidian users can tick boxes; Dataview aggregates completion status across vault.

**Why**: Actionable content. Users can track what they've done based on vault advice.

---

## Next Steps

1. Approve Phase 2
2. Execute O3 (if not complete from Phase 1)
3. Execute O4 (add conflict detection to query flow)
4. Execute O5 (create response templates)
5. Execute O6 (add checklists to relevant atoms)
6. Verify quality improvement
7. Move to Phase 3
