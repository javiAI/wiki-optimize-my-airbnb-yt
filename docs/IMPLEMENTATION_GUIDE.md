# Implementation Guide — Fully Automated LLM Wiki

**Purpose**: Step-by-step guide to understanding and using the automated system for vault optimization.

---

## Quick Start (2 minutes)

If you just want to know what to do next:

```bash
./scripts/next-task.sh
# Output: Shows your current phase, next incomplete task, and effort estimate
```

---

## How the Automation Works

### Entry Point: CLAUDE_AUTOMATED.md

This is **the single source of truth**. All scripts read from it, all state lives in it.

**What it contains:**
- **Lines 1-162**: Machine-readable YAML state (scripts read this)
  - Current phase (1-4)
  - Task status (pending_approval, in_progress, complete)
  - Progress metrics
  - Optimization tracker (O1-O16)
  
- **Lines 164-248**: Human-readable summary (you read this)
  - Quick status
  - Key links
  - Approval instructions
  
- **Lines 250+**: Complete kernel (§0-§9) + domain layer (§10)
  - All original instructions preserved
  - Searchable reference

### The Phase System

Four phases, each with specific tasks:

| Phase | Name | Tasks | Effort | Status |
|-------|------|-------|--------|--------|
| 1 | Critical Path | O1, O2, O3 | 4.5h | Pending approval |
| 2 | Quality Foundation | O3-O6 | 9h | Not started |
| 3 | Automation | O7-O9 | 18h | Not started |
| 4 | Integration | O10-O12 | 13h | Not started |

Each phase must be approved before execution.

---

## Your Daily Workflow

### When Starting a Session

```bash
# 1. See current status (30 seconds)
./scripts/show-progress.sh
# Output:
#   Phase: 1 (Critical Path)
#   Status: ⏳ Pending Approval for O1 + O2
#   Progress: 0% (0/3 tasks)
#   Next: User approves → Phase 1 executes

# 2. See next task (if approved)
./scripts/next-task.sh
# Output:
#   Phase: 1
#   Next Task: O1 (Hierarchical Indices)
#   Effort: 4 hours
#   Reference: docs/ARCHITECTURE.md §3 (line 250)
#   ↓ Status: PENDING_APPROVAL
```

### When Approving a Phase

```bash
# Approve Tier 1 (O1 + O2) and start Phase 1
./scripts/approve-phase.sh O1 O2

# This updates CLAUDE_AUTOMATED.md state and marks tasks as in_progress
```

### When Completing a Task

After finishing task O1:

```bash
# Mark task complete
./scripts/mark-complete.sh O1

# This automatically:
#   1. Marks O1 as complete
#   2. Updates progress % 
#   3. Shows next incomplete task
#   4. Logs completion in CLAUDE_AUTOMATED.md
```

### When Blocked

If something fails:

```bash
# Document the blocker (see CLAUDE_AUTOMATED.md for format)
# The next session, Claude will see it and help resolve
```

---

## Script Reference

### ./scripts/next-task.sh
**What it does**: Shows the next incomplete task in your current phase.

**Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Phase: 1
Next Task: O1 (Hierarchical Indices)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Effort: 4 hours
Reference: docs/ARCHITECTURE.md §3 (line 250)
Status: PENDING_APPROVAL

To execute: ./scripts/phase-executor.py O1
To mark done: ./scripts/mark-complete.sh O1
```

---

### ./scripts/show-progress.sh
**What it does**: Shows overall progress across all phases.

**Output**:
```
╔════════════════════════════════════════════╗
║          LLM Wiki Optimization Progress    ║
╚════════════════════════════════════════════╝

Vault: optimize-my-airbnb-yt
Quality: 8.52/10 → Target: 9.8/10
Baseline Tokens: 3,956 → Target: 1,200

PHASE 1: Critical Path
  Status: ⏳ Pending Approval
  Progress: 0/3 tasks (0%)
  Completed: none
  Next: O1 (Hierarchical Indices)

PHASE 2: Quality Foundation
  Status: ⏹ Not Started
  Progress: 0/4 tasks

PHASE 3: Automation
  Status: ⏹ Not Started
  Progress: 0/3 tasks

PHASE 4: Integration
  Status: ⏹ Not Started
  Progress: (see docs/ARCHITECTURE.md for details)

═══════════════════════════════════════════
Total Effort: 44.5 hours across 4 phases
Estimated Completion: 5 weeks (2h/day)
```

---

### ./scripts/approve-phase.sh
**What it does**: Approve a phase and transition tasks to in_progress.

**Usage**:
```bash
./scripts/approve-phase.sh O1 O2      # Approve O1 and O2 for Phase 1
./scripts/approve-phase.sh O3 O4 O5   # Approve multiple tasks at once
```

**Effect**:
- Sets approved tasks to `status: in_progress`
- Updates CLAUDE_AUTOMATED.md YAML state
- `next-task.sh` now shows executable task instead of "PENDING_APPROVAL"

---

### ./scripts/mark-complete.sh
**What it does**: Mark a task as done and show the next one.

**Usage**:
```bash
./scripts/mark-complete.sh O1    # Mark O1 complete, show next task
```

**Effect**:
- Adds O1 to `completed_tasks[]` in CLAUDE_AUTOMATED.md
- Recalculates progress % for current phase
- Shows next incomplete task
- Logs completion event

---

### ./scripts/state-manager.py
**What it does**: Core automation script that reads/writes CLAUDE_AUTOMATED.md state.

**Usage** (for debugging):
```bash
python3 scripts/state-manager.py --read-state
# Output: entire YAML structure (for inspection)

python3 scripts/state-manager.py --get-phase
# Output: 1 (current phase number)

python3 scripts/state-manager.py --get-next-task
# Output: O1 (next incomplete task ID)
```

---

### ./scripts/phase-executor.py
**What it does**: Determines current phase and shows what to execute next.

**Usage**:
```bash
./scripts/phase-executor.py          # Show next executable task
./scripts/phase-executor.py --run    # Execute the task (if implemented)
```

---

## Understanding the Optimization Tracker

All optimizations are listed in CLAUDE_AUTOMATED.md lines 65-142:

```yaml
optimizations:
  O1:
    name: "Hierarchical Indices"
    status: "pending_approval"
    phase: 1
    effort_hours: 4
    impact_high: true
    reference: "docs/ARCHITECTURE.md §3 (line 250)"
  
  O2:
    name: "Fix Q4 Contradiction"
    status: "pending_approval"
    phase: 1
    effort_hours: 0.5
    impact_high: true
    reference: "test_battery/OPTIMIZATIONS_ROADMAP_10X.md"
  
  # ... O3 through O16
```

**Key fields:**
- `status`: pending_approval | in_progress | complete | deferred
- `phase`: Which phase this optimization belongs to (1-4)
- `effort_hours`: Time estimate for this optimization
- `impact_high`: Whether this is high-impact for quality/token savings
- `reference`: Where to find detailed instructions

---

## Understanding Phases

### Phase 1: Critical Path (4.5 hours, Pending Approval)

**Goal**: Reduce token overhead and fix known contradiction.

**Tasks**:
- **O1** (4h): Hierarchical Indices
  - Reduce root index from 344 lines to ~100
  - Create 12 category-specific indices
  - Token savings: 3.9k → 1.2k baseline (-69%)
  
- **O2** (0.5h): Fix Q4 Contradiction
  - Resolve "2-3 veces/año vs 2-3 meses" in meta/contradictions.md
  
- **O3** (0.5h): Validation
  - Verify improvements with test battery

**Expected Result**: Quality 8.52 → 9.0

---

### Phase 2: Quality Foundation (9 hours)

**Goal**: Improve response quality and consistency.

**Tasks**:
- **O3** (2h): Language Consistency
  - Ensure all Spanish terminology standardized
  
- **O4** (3h): Contradiction Detection (Layer 1)
  - Heuristic checks at ingest time
  
- **O5** (2.5h): Response Format Templates
  - Standardized response structures per query type
  
- **O6** (1.5h): Executable Checklists
  - Make task lists self-verifying

**Expected Result**: Quality 9.0 → 9.4

---

### Phase 3: Automation (18 hours)

**Goal**: Fully automate vault maintenance.

**Tasks**:
- **O7** (8h): Agent Orchestration
  - Ingester, Linker, Auditor, Query-Cacher agents
  
- **O8** (4h): Auto-Linking System
  - Automatic cross-references between atoms
  
- **O9** (6h): Query Caching
  - Cache responses for repeat queries

**Expected Result**: Quality 9.4 → 9.7, Automation ✅

---

### Phase 4: Integration (13+ hours)

**Goal**: Documentation and multi-vault support.

**Tasks**:
- **O10** (3h): Semantic Gap Detection
- **O11** (4h): Backlink Generation  
- **O12** (6h): RAG Fallback

**Expected Result**: Quality 9.7 → 9.8, Ready for project-OS integration

---

## Key References

For detailed technical understanding:

- **Architecture**: See [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Evaluation Framework**: See [docs/EVALUATION.md](EVALUATION.md)
- **Original Concept**: See [docs/ORIGINAL_CONCEPT.md](ORIGINAL_CONCEPT.md)
- **Vault Instructions**: See [CLAUDE_AUTOMATED.md](../CLAUDE_AUTOMATED.md) (§0-§10)
- **Test Baseline**: See [test_battery/EVALUATION_RESULTS_V2.md](../test_battery/EVALUATION_RESULTS_V2.md)

---

## Troubleshooting

### "Command not found: ./scripts/next-task.sh"

Make scripts executable:
```bash
chmod +x scripts/*.sh scripts/*.py
```

### "ModuleNotFoundError: yaml" (when running Python scripts)

Install required Python packages:
```bash
pip3 install pyyaml
```

### "CLAUDE_AUTOMATED.md YAML doesn't parse"

Validate YAML syntax:
```bash
python3 -c "import yaml; yaml.safe_load(open('CLAUDE_AUTOMATED.md'))"
# If it fails, check for syntax errors in lines 1-162
```

### "Progress shows 0% but I completed O1"

Manually update progress:
```bash
./scripts/mark-complete.sh O1
# This recalculates and shows correct progress
```

---

## Advanced: Reading YAML State Directly

If you want to understand what the scripts are reading:

```bash
python3 << 'EOF'
import yaml

with open("CLAUDE_AUTOMATED.md") as f:
    content = f.read()
    # Extract YAML between --- markers
    _, frontmatter, _ = content.split("---", 2)
    state = yaml.safe_load(frontmatter)

# Current phase
print(f"Phase: {state['execution_state']['current_phase']}")

# Next task
phase = state['execution_state']['current_phase']
next_task = state['phases'][f'phase_{phase}']['next_incomplete_task']
print(f"Next: {next_task}")

# Progress
progress = state['phases'][f'phase_{phase}']['progress_percent']
print(f"Progress: {progress}%")
EOF
```

---

## Summary

The automation works by:

1. **All state lives in CLAUDE_AUTOMATED.md** (single source of truth)
2. **Scripts read YAML** from lines 1-162
3. **You run scripts** to see progress and approve phases
4. **Scripts update state** when you complete tasks
5. **Next session** opens CLAUDE_AUTOMATED.md, sees current state, continues

**No confusion. No lost context. Fully automated.**

---

**Ready to start?**

```bash
./scripts/show-progress.sh              # See current status
./scripts/approve-phase.sh O1 O2        # Approve Phase 1
./scripts/next-task.sh                  # See next task to execute
```
