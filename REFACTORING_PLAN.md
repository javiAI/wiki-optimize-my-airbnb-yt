# Refactoring Plan: From Manual to Fully Automated

**Goal**: Eliminate redundancy, restructure for automation, make CLAUDE.md the single source of truth

---

## Current State Analysis (30 .md files)

### ROOT LEVEL (10 files) — Highly redundant

| File | Purpose | Keep? | Action |
|------|---------|-------|--------|
| CLAUDE.md | Schema | ✅ KEEP | **Renovate: Make it automation-ready** |
| ARCHITECTURE_PLAN_FINAL.md | Design | ✅ KEEP | Move to docs/; keep reference |
| README.md | Project info | ✅ KEEP | Update with automation setup |
| llm-wiki.md | Original concept | ✅ KEEP | Archive to docs/ |
| IMPLEMENTATION_INDEX.md | Checklists | ⚠️ INTEGRATE | Merge into CLAUDE.md state section |
| NAVIGATION_SYSTEM_EVALUATION.md | Metrics | ⚠️ CONSOLIDATE | Move to docs/EVALUATION.md |
| cloud.md | Navigation hub | ❌ DELETE | Was interim; now confused with CLAUDE.md |
| MASTER_PLAN.md | ??? | ⚠️ AUDIT | Check if has unique content |
| TEST_BATTERY_PLAN.md | ??? | ⚠️ AUDIT | Likely v1, check if superseded |
| TEST_BATTERY_PLAN_V2.md | ??? | ⚠️ AUDIT | Likely current, consolidate |

### test_battery/ (20 files) — Mostly good

| File | Purpose | Keep? | Action |
|------|---------|-------|--------|
| AGENT_INSTRUCTIONS.md | Test protocol | ✅ KEEP | Reference in CLAUDE.md |
| OPTIMIZATIONS_CONSOLIDATED_MASTER.md | 32 optimizations | ✅ KEEP | Reference in CLAUDE.md |
| OPTIMIZATIONS_ROADMAP_10X.md | Roadmap | ⚠️ CONSOLIDATE | Info duplicates ARCHITECTURE_PLAN_FINAL.md |
| evaluation/ (2) | Baseline results | ✅ KEEP | Reference in CLAUDE.md |
| responses/ (15) | Q1-Q15 baseline | ✅ KEEP | Reference in CLAUDE.md |

---

## Target State After Refactoring

```
Repository/
├── README.md                              # Project overview + automation setup
├── CLAUDE.md                              # ⭐ SINGLE SOURCE OF TRUTH (automated entry point)
│   ├── §0: Metadata (YAML state)
│   ├── §1: Current phase + progress
│   ├── §2: Immediate next steps (for scripts)
│   ├── §3-9: Generic kernel (existing)
│   └── §10: Domain layer (existing)
│
├── docs/                                  # Documentation (not executed)
│   ├── ARCHITECTURE.md                    # Moved from ARCHITECTURE_PLAN_FINAL.md
│   ├── EVALUATION.md                      # Moved from NAVIGATION_SYSTEM_EVALUATION.md
│   ├── ORIGINAL_CONCEPT.md                # Moved from llm-wiki.md
│   └── IMPLEMENTATION_GUIDE.md            # New: how to run scripts
│
├── scripts/                               # Automation (executed by Claude)
│   ├── state-manager.py                   # NEW: read/write CLAUDE.md state
│   ├── phase-executor.py                  # NEW: run current phase tasks
│   ├── next-task.sh                       # NEW: show next incomplete task
│   ├── report-progress.sh                 # NEW: human-friendly output
│   └── [existing scripts]
│
├── test_battery/                          # Test baseline (don't modify)
│   ├── AGENT_INSTRUCTIONS.md              # Keep
│   ├── OPTIMIZATIONS_CONSOLIDATED_MASTER.md
│   ├── evaluation/
│   │   ├── EVALUATION_TEMPLATE.md
│   │   └── EVALUATION_RESULTS_V2.md
│   └── responses/
│       └── Q1-Q15.md
│
└── .env.example                           # Configuration template (NEW)
```

---

## Files to Delete

```
❌ cloud.md                    (confusing, isolated, replaced by CLAUDE.md automation)
❌ IMPLEMENTATION_INDEX.md     (merged into CLAUDE.md)
❌ NAVIGATION_SYSTEM_EVALUATION.md (moved to docs/)
```

**Action needed**: After refactoring is complete, delete these 3 files.

---

## Files to Consolidate

### MASTER_PLAN.md
- **Current**: 30+ lines?
- **Action**: Check content. If unique info → move to docs/. Else delete.

### TEST_BATTERY_PLAN.md vs TEST_BATTERY_PLAN_V2.md
- **Action**: Keep V2, delete V1. Consolidate if they have duplicate content.

### OPTIMIZATIONS_ROADMAP_10X.md
- **Current**: 100+ lines on contradictions + optimizations
- **Action**: Info mostly duplicated in ARCHITECTURE_PLAN_FINAL.md. Consolidate into one source.

---

## New CLAUDE.md Structure (Automation-Ready)

```markdown
# LLM Wiki — Schema + Automation State

## §0: Metadata (YAML for automation)

---
# Machine-readable state (scripts read this)
automation:
  enabled: true
  last_update: 2026-04-25T15:30:00Z
  
current_phase: 1
phase_status:
  phase_1:
    status: pending_approval  # pending_approval | in_progress | complete
    completed_tasks: []
    total_tasks: 3
    progress_percent: 0
    next_incomplete_task: O1
    
  phase_2:
    status: not_started
    ...

optimizations:
  O1:
    status: pending_approval  # pending_approval | in_progress | complete | deferred
    name: "Hierarchical Indices"
    effort_hours: 4
    phase: 1
    
  O2:
    status: pending_approval
    name: "Fix Q4 Contradiction"
    effort_hours: 0.5
    phase: 1
    
  O3:
    ...

vault:
  name: "optimize-my-airbnb-yt"
  atoms: 156
  mocs: 12
  sources: 173
  quality_score: 8.52
  
---

## §1: Current Status (Human-readable summary)

**Phase**: Awaiting approval for Phase 1  
**Progress**: 0% (0/3 tasks)  
**Next Step**: User approves O1 + O2 → Phase 1 Checklist executes

**Quick Links**:
- Architecture: See docs/ARCHITECTURE.md
- Evaluation: See docs/EVALUATION.md
- Baseline: See test_battery/EVALUATION_RESULTS_V2.md

## §2: Immediate Next Steps (For scripts/Claude)

If you're an automated script:
```bash
1. Read this CLAUDE.md
2. Check: automation.current_phase
3. Check: phase_status[current_phase].status
4. If "pending_approval": wait for user input
5. If "in_progress": execute next_incomplete_task
6. If "complete": move to next phase
```

If you're Claude (human oversight):
```bash
./scripts/next-task.sh              # See what's next
./scripts/show-progress.sh          # See where we are
./scripts/approve-phase.sh O1 O2    # Approve and start
./scripts/mark-complete.sh O1       # Mark task done
```

## §3-§9: Generic Kernel

[Existing §0-§9 content — unchanged]

## §10: Domain Layer

[Existing §10 content — unchanged]

---
```

---

## New Scripts to Create

### 1. state-manager.py (Core automation)

```python
#!/usr/bin/env python3
import yaml
import json
from pathlib import Path
from datetime import datetime

class CLAUDEStateManager:
    def __init__(self, claude_md_path="CLAUDE.md"):
        self.path = Path(claude_md_path)
    
    def read_state(self):
        """Extract YAML state from CLAUDE.md"""
        with open(self.path) as f:
            content = f.read()
            # Extract frontmatter between --- markers
            _, yaml_content, _ = content.split("---", 2)
            return yaml.safe_load(yaml_content)
    
    def write_state(self, state):
        """Update YAML state in CLAUDE.md"""
        # Read full file
        with open(self.path) as f:
            parts = f.split("---", 2)
        
        # Update frontmatter
        parts[1] = yaml.dump(state, default_flow_style=False)
        
        # Write back
        with open(self.path, 'w') as f:
            f.write("---\n")
            f.write(parts[1])
            f.write("---\n")
            f.write(parts[2])
    
    def get_current_phase(self):
        state = self.read_state()
        return state['current_phase']
    
    def get_next_task(self):
        state = self.read_state()
        phase = state['current_phase']
        return state['phase_status'][f'phase_{phase}']['next_incomplete_task']
    
    def mark_task_complete(self, task_id):
        state = self.read_state()
        phase = state['current_phase']
        phase_key = f'phase_{phase}'
        
        # Add to completed_tasks
        state['phase_status'][phase_key]['completed_tasks'].append(task_id)
        
        # Update progress
        completed = len(state['phase_status'][phase_key]['completed_tasks'])
        total = state['phase_status'][phase_key]['total_tasks']
        state['phase_status'][phase_key]['progress_percent'] = int(100 * completed / total)
        
        # Update timestamp
        state['automation']['last_update'] = datetime.now().isoformat()
        
        # Find next task
        all_tasks = [o for o, v in state['optimizations'].items() 
                     if v['phase'] == phase and v['status'] == 'pending_approval']
        state['phase_status'][phase_key]['next_incomplete_task'] = \
            next((t for t in all_tasks if t not in state['phase_status'][phase_key]['completed_tasks']), None)
        
        self.write_state(state)
    
    def approve_phase(self, *task_ids):
        """Approve tasks to start phase"""
        state = self.read_state()
        for task_id in task_ids:
            state['optimizations'][task_id]['status'] = 'in_progress'
        state['current_phase_status'] = 'in_progress'
        self.write_state(state)
```

### 2. next-task.sh (Show next step)

```bash
#!/bin/bash
# Show next task for current phase (human-friendly)

STATE=$(python3 scripts/state-manager.py --get-next-task)
PHASE=$(python3 scripts/state-manager.py --get-phase)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Current Phase: $PHASE"
echo "Next Task: $STATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To execute: ./scripts/phase-executor.py $STATE"
echo "To mark done: ./scripts/mark-complete.sh $STATE"
```

### 3. show-progress.sh (Human-friendly progress)

```bash
#!/bin/bash
# Show current progress in human-friendly format

python3 scripts/state-manager.py --show-progress
```

---

## Folder Organization After Refactoring

```
/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/
├── README.md
├── CLAUDE.md                                   # ⭐ Single source of truth
│
├── docs/                                       # Documentation (not executed)
│   ├── ARCHITECTURE.md                         # Comprehensive design
│   ├── EVALUATION.md                          # Metrics and how to validate
│   ├── ORIGINAL_CONCEPT.md                    # Original llm-wiki.md concept
│   └── IMPLEMENTATION_GUIDE.md               # How to use scripts
│
├── scripts/                                    # Automation (executed by Claude)
│   ├── state-manager.py                       # Core: read/write CLAUDE.md state
│   ├── phase-executor.py                      # Run current phase tasks
│   ├── next-task.sh                           # Show next incomplete task
│   ├── show-progress.sh                       # Human-friendly progress report
│   ├── mark-complete.sh                       # Mark task as complete
│   ├── approve-phase.sh                       # Approve + start phase
│   └── [existing scripts]
│
├── test_battery/                              # Baseline (don't modify)
│   ├── AGENT_INSTRUCTIONS.md
│   ├── OPTIMIZATIONS_CONSOLIDATED_MASTER.md
│   ├── evaluation/
│   └── responses/
│
└── .env.example                               # Configuration template
```

---

## Implementation Steps

### Step 1: Create Minimal New CLAUDE.md (Automated)

Replace current CLAUDE.md with new version that:
- Has YAML state at top (machine-readable)
- Has human summary below
- Keeps all §3-10 content
- References docs/ for architecture details

### Step 2: Create scripts/ (Python + Bash automation)

Write 5 scripts:
- state-manager.py (core)
- phase-executor.py (run tasks)
- next-task.sh (show next)
- show-progress.sh (progress report)
- mark-complete.sh / approve-phase.sh (actions)

### Step 3: Move Docs

Move large docs to docs/:
- ARCHITECTURE_PLAN_FINAL.md → docs/ARCHITECTURE.md
- NAVIGATION_SYSTEM_EVALUATION.md → docs/EVALUATION.md
- llm-wiki.md → docs/ORIGINAL_CONCEPT.md
- llm-wiki.md → docs/IMPLEMENTATION_GUIDE.md (new)

### Step 4: Clean Up

Delete:
- cloud.md
- IMPLEMENTATION_INDEX.md
- NAVIGATION_SYSTEM_EVALUATION.md (after moving)
- Consolidate TEST_BATTERY_PLAN*.md
- Consolidate OPTIMIZATIONS_ROADMAP_10X.md

### Step 5: Update References

- README.md: Update with new folder structure
- CLAUDE.md: References to docs/
- All scripts: Tested and working

---

## Benefits of This Restructuring

✅ **Single source of truth**: CLAUDE.md (what scripts read)  
✅ **Fully automated**: Scripts execute automatically  
✅ **Human feedback**: output/reports (humans read summaries, not technical docs)  
✅ **No confusion**: cloud.md deleted, structure is clear  
✅ **No redundancy**: Each file has one purpose  
✅ **Easy to maintain**: Central state (YAML) + execution (scripts)  
✅ **Scalable**: Same pattern works for multiple vaults

---

## Timeline

- **Step 1-2**: 2 hours (new CLAUDE.md + scripts)
- **Step 3-4**: 1 hour (move docs, cleanup)
- **Step 5**: 30 min (testing + references)

**Total**: ~3.5 hours for complete automation refactoring

---

This plan transforms from manual navigation system to fully automated execution.

