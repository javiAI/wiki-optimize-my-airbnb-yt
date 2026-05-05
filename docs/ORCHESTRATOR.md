# Orchestrator Design — Autonomous Execution

**Purpose**: Define how scripts, hooks, and phases execute automatically without manual intervention.

**Principle**: Claude Code reads CLAUDE.md state automatically. Router determines action. Hooks trigger execution. No manual scripts.

---

## 1. Entry Point: CLAUDE.md Router

Every session, Claude reads CLAUDE.md and executes based on `automation.phase_status`:

```yaml
automation:
  current_phase: 1
  phase_status: "pending_approval"  # ← determines what happens next
```

**Router logic** (§ ROUTER in CLAUDE.md):

```
IF phase_status == "pending_approval"
  → Show PHASE_X_SUMMARY.md
  → Wait for user: "Approve Phase X"
  → User approves → Update YAML, git commit, move to "in_progress"

IF phase_status == "in_progress"
  → Show PHASE_X_TASKS.md
  → Execute next incomplete task in tasks[]
  → After task done: update YAML, git commit
  → Loop until all tasks complete → move to "complete"

IF phase_status == "complete"
  → Advance to next phase
  → Set phase_status = "pending_approval"
  → Show next phase summary
```

---

## 2. Task Execution (Manual → Claude Code)

Each task (O1, O2, ..., O12) executes in this sequence:

### Phase 1: Critical Path

```
USER: "Approve Phase 1"
  ↓
CLAUDE: Update CLAUDE.md
  - phase_1.status = "in_progress"
  - automation.phase_status = "in_progress"
  ↓
GIT: Commit "Phase 1 approved, moving to in_progress"
  ↓
CLAUDE: Execute O1 (per PHASE_1_TASKS.md §O1)
  - Read current index.md structure
  - Create index/ subdirectory
  - Partition content
  - Create new index.md (L1)
  - Update cross-links
  - Verify in Obsidian
  - Measure token savings
  - GIT commit: "O1: Hierarchical indices..."
  ↓
CLAUDE: Update CLAUDE.md
  - O1.status = "completed"
  - phase_1.completed_tasks = [O1]
  - phase_1.progress = 1/3
  ↓
GIT: Commit "O1 complete"
  ↓
CLAUDE: Execute O2 (per PHASE_1_TASKS.md §O2)
  [... repeat structure ...]
  ↓
CLAUDE: Execute O3 (per PHASE_1_TASKS.md §O3)
  [... repeat structure ...]
  ↓
CLAUDE: Update CLAUDE.md
  - phase_1.status = "complete"
  - phase_1.progress = 100
  ↓
GIT: Commit "Phase 1 complete"
  ↓
CLAUDE: Show PHASE_2_SUMMARY.md
  → Wait for user: "Approve Phase 2"
```

### Phases 2, 3, 4

Same pattern as Phase 1, repeating for all 4 phases.

---

## 3. Testing Hooks (if opt-in)

**Optional**: Run automated test cycle alongside optimizations.

### 3.1 Pre-Optimization Hook

```bash
# .git/hooks/pre-commit-O1
# Triggered before committing "O1: ..."

if git log --oneline -1 | grep -q "^O[0-9]"; then
  echo "🧪 Pre-optimization test..."
  python3 scripts/run-optimization-cycle.py --optimization O1 --phase pre
  if [ $? -ne 0 ]; then
    echo "❌ Pre-test failed"
    exit 1
  fi
fi
```

### 3.2 Post-Optimization Hook

```bash
# .git/hooks/post-commit-OX
# Triggered after "OX: Optimization implemented"

if git log --oneline -1 | grep -q "optimization implemented"; then
  echo "🧪 Post-optimization test..."
  OPT=$(git log --oneline -1 | grep -oE "O[0-9]+")
  python3 scripts/run-optimization-cycle.py --optimization $OPT --phase post
  
  # Compare and decide
  DECISION=$(python3 scripts/compare-test-results.py $OPT)
  
  if [ "$DECISION" = "REVERT" ]; then
    echo "❌ Regression detected. Reverting..."
    git revert --no-edit HEAD
  elif [ "$DECISION" = "ITERATE" ]; then
    echo "⚠️ Marginal improvement. Recommend iteration."
  else
    echo "✅ Improvement verified. Keeping commit."
  fi
  
  # Update master report
  python3 scripts/update-test-report.py $OPT $DECISION
fi
```

---

## 4. Execution Timeline (Realistic)

```
DAY 1 — Morning (30 min)
  10:00 — USER: "Approve Phase 1"
  10:05 — CLAUDE: Updates CLAUDE.md, commits
  10:10 — CLAUDE: Executes O1 (Hierarchical Indices, 4h work)
  10:50 — O1 complete, test results: tokens ↓14%, quality ↑2.6%
  10:55 — CLAUDE: Commits "O1 complete"
  11:00 — CLAUDE: Starts O2 (Fix Contradiction, 0.5h work)

  12:00 — O2 complete, test results: tokens ↓1.4%, quality ↑1.3%
  12:05 — CLAUDE: Commits "O2 complete"
  12:10 — CLAUDE: Starts O3 (Language Consistency, 2h work)

DAY 1 — Afternoon (continues)
  13:00 — O3 complete, test results: tokens ↓2%, quality ↑3.2%
  13:05 — CLAUDE: Commits "O3 complete"
  13:10 — CLAUDE: All Phase 1 tasks done
  13:15 — CLAUDE: Updates CLAUDE.md (phase_1.status = "complete")
  13:20 — CLAUDE: Shows PHASE_2_SUMMARY.md

  USER REVIEWS Phase 2 summary (10 min)
  13:30 — USER: "Approve Phase 2"
  13:35 — CLAUDE: Continues with O4 (Phase 2, 3h work)
  ...

DAY 2+ — Continues autonomously
  (Repeat for Phases 2, 3, 4)
```

**Key**: Once Phase is approved, Claude executes all tasks sequentially without manual intervention.

---

## 5. Atomic Git Commits

Each optimization results in **exactly one commit**:

```bash
# After O1 execution complete:
git commit -m "O1: Hierarchical indices (index.md 344→100 lines, 4k→1.2k tokens)

Test results:
- Pre-test avg tokens: 2150 → Post-test: 1847 ↓14.1%
- Pre-test quality: 7.6 → Post-test: 7.8 ↑2.6%
- Decision: IMPLEMENT (tokens down, quality up)

Changes:
- Created index/ subdirectory with tiered indices
- Reorganized index.md to L1 overview only
- Updated all cross-links
- Verified in Obsidian

Artifacts:
- meta/tests/O1-PRE.json, O1-POST.json, comparison-O1.json"
```

This makes `git log` a readable history of each optimization's impact.

---

## 6. State Management

CLAUDE.md is the **single source of truth**. All state lives in YAML:

```yaml
automation:
  version: "3.1"
  current_phase: 1
  phase_status: "in_progress"
  last_update: "2026-04-25T13:20:00Z"

phases:
  phase_1:
    name: "Critical Path"
    status: "in_progress"
    tasks: [O1, O2, O3]
    completed: [O1, O2]          # ← updated after each task
    progress: 67                  # 2/3
  phase_2:
    name: "Quality Foundation"
    status: "not_started"
    ...

optimizations:
  O1: { status: "completed", phase: 1, hours: 4, impact: "tokens ↓14%, quality ↑2.6%" }
  O2: { status: "completed", phase: 1, hours: 0.5, impact: "tokens ↓1.4%, quality ↑1.3%" }
  O3: { status: "in_progress", phase: 1, hours: 2, impact: "TBD" }
  ...
```

**Update script** (`scripts/update-state.py`):

```python
#!/usr/bin/env python3
"""Update CLAUDE.md YAML state"""

def mark_task_complete(task_id, impact_summary):
    """Mark task as complete, update progress"""
    # 1. Read CLAUDE.md
    # 2. Find optimization[task_id]
    # 3. Set status = "completed"
    # 4. Add impact summary
    # 5. Update parent phase.progress
    # 6. Write CLAUDE.md back
    pass

def advance_phase(current_phase):
    """Move to next phase"""
    # 1. Set phases[phase_X].status = "complete"
    # 2. Set automation.current_phase = X+1
    # 3. Set phases[phase_X+1].status = "pending_approval"
    # 4. Set automation.phase_status = "pending_approval"
    # 5. Write CLAUDE.md back
    pass
```

---

## 7. Conditional Execution

Some tasks have **conditions** that affect execution:

### Example: O8 (Auto-Linking System)

```python
# In PHASE_3_TASKS.md, before O8:

# Condition: Is O7 (vault-agent.py) already complete?
if optimizations["O7"]["status"] != "completed":
  print("❌ O8 requires O7. Please complete O7 first.")
  exit(1)

# If O7 complete:
# Proceed with O8 (auto-linking depends on vault-agent foundational structure)
```

---

## 8. Failure Handling

### 8.1 Script Failure

```bash
# If a task script fails (e.g., file not found):

CLAUDE logs:
  ❌ O1: Hierarchical Indices failed
  Error: sources/ not found at $VAULT_PATH
  Action: Update CLAUDE.md.O1.status = "blocked"
  Next: Human investigates, fixes path in .claude/scripts/config.sh or vaults/{name}/vault.yml
  Resume: ./scripts/update-state.py --resume O1
```

### 8.2 Test Failure (Regression)

```bash
# If post-test shows regression:

DECISION = "REVERT"
  ↓
AUTO: git revert --no-edit HEAD
  ↓
CLAUDE: Update CLAUDE.md.O1.status = "reverted"
  ↓
Log entry: meta/tests/master-report.md
  "O1: Reverted due to quality regression (-0.5 points)"
  ↓
CLAUDE: Skip to next optimization
  (O1 marked as "failed"; can retry later with different approach)
```

### 8.3 Blocked on User Input

```bash
# If task requires human decision:

CLAUDE logs:
  ⚠️  O2: Fix Q4 Contradiction
  Found two conflicting atoms: A (score 8.1) vs B (score 7.9)
  
  Which should be primary?
  Option 1: A (higher score, newer source)
  Option 2: B (more cited, more specific)
  
  Awaiting user input...
  
USER: Option 1
  ↓
CLAUDE: Marks O2 complete with choice documented
```

---

## 9. Performance Targets

For full automation to be practical:

| Task | Effort | Execution time | Total time (effort + testing) |
|------|--------|---|---|
| O1 | 4h | ~1-2h manual work | ~4h (with 2h pre/post test) |
| O2 | 0.5h | ~15 min | ~1h (with 30min test) |
| O3 | 2h | ~1h | ~2.5h (with test) |
| **Phase 1 Total** | **6.5h** | ~3.5h | ~7.5h |
| **Phase 2 Total** | **9h** | ~4h | ~9h |
| **Phase 3 Total** | **18h** | ~8h | ~18h |
| **Phase 4 Total** | **13h** | ~6h | ~13h |

**Full cycle (all phases)**: ~50 hours work + ~8 hours testing = ~58 hours total

**With autonomous execution**: Can complete in 2-3 days of continuous work.

---

## 10. Monitoring & Alerts

Real-time dashboard (optional):

```bash
# scripts/show-status.sh
# Displays current state + progress

🔄 ORCHESTRATOR STATUS

Current Phase: 1 (Critical Path)
Status: in_progress
Progress: 2/3 tasks complete

✅ O1 Complete (tokens ↓14%, quality ↑2.6%)
✅ O2 Complete (tokens ↓1.4%, quality ↑1.3%)
⏳ O3 In Progress (Language Consistency, 2h)

Next Expected Completion: 2026-04-25 13:30 UTC
Last Activity: 2026-04-25 12:05 UTC (O2 committed)

Upcoming: Phase 2 (Quality Foundation) — awaiting approval
```

---

## 11. Rollback & Iteration

If an optimization needs iteration:

```bash
# Manual iteration (not automatic):

USER: Review test results, sees marginal improvement
USER: "Iterate O1 with different strategy"
  ↓
CLAUDE: Revert O1 commit
  $ git revert --no-edit <O1-commit-hash>
  ↓
CLAUDE: Update CLAUDE.md.O1.status = "in_progress" (iteration 2)
  ↓
CLAUDE: Apply revised O1 (different approach)
  ↓
Test again, re-compare
  ↓
If improvement > iteration 1: commit
If improvement < iteration 1: try once more, then give up
```

---

## 12. Success Criteria for Orchestrator

Orchestrator is **working** when:

✅ User says "Approve Phase 1" → Claude executes all Phase 1 tasks without manual intervention  
✅ Each task ends in atomic git commit with test results  
✅ CLAUDE.md state stays in sync (no manual YAML edits)  
✅ Full Phase 1 cycle completes in <8 hours  
✅ If test shows regression, auto-reverts without breaking state  
✅ Readable git log showing each optimization's impact  
✅ No orphaned files or half-completed tasks  
