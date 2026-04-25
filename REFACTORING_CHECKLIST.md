# Refactoring Checklist — From Manual to Fully Automated

**Status**: Ready to execute  
**Timeline**: ~4 hours total  
**Risk**: Low (non-destructive, can rollback anytime)

---

## WHAT WILL CHANGE

### Current State (Confusing)
```
Repository Root (10 .md files) — Confusion + Redundancy
├── CLAUDE.md (schema)
├── cloud.md (navigation hub — isolated, not used)
├── IMPLEMENTATION_INDEX.md (checklists — duplicates cloud.md)
├── ARCHITECTURE_PLAN_FINAL.md (design — large, 450 lines)
├── NAVIGATION_SYSTEM_EVALUATION.md (metrics — duplicates ARCHITECTURE_PLAN_FINAL.md)
├── MASTER_PLAN.md (??? unclear purpose)
├── TEST_BATTERY_PLAN.md + TEST_BATTERY_PLAN_V2.md (both exist)
├── README.md (project info)
├── llm-wiki.md (original concept)
└── test_battery/ (20 files) — Good

PROBLEM: 
- Multiple entry points (CLAUDE.md vs cloud.md vs IMPLEMENTATION_INDEX.md)
- Humans must read & choose
- Scripts have no single source of truth
- Lots of redundancy
```

### Target State (Clear + Automated)
```
Repository Root (5 .md files + 1 docs/ folder) — Clean + Automated
├── CLAUDE_AUTOMATED.md ← ⭐ SINGLE ENTRY POINT
│   ├── YAML frontmatter (machine-readable state)
│   ├── Human summary
│   ├── Script instructions
│   └── Full kernel + domain
├── README.md (updated with new structure)
├── .env.example (configuration template — NEW)
│
├── docs/ ← Documentation (not executed)
│   ├── ARCHITECTURE.md (moved from ARCHITECTURE_PLAN_FINAL.md)
│   ├── EVALUATION.md (moved from NAVIGATION_SYSTEM_EVALUATION.md)
│   ├── ORIGINAL_CONCEPT.md (moved from llm-wiki.md)
│   └── IMPLEMENTATION_GUIDE.md (new: how to use scripts)
│
├── scripts/ ← Automation (executed)
│   ├── state-manager.py (NEW: read/write CLAUDE_AUTOMATED.md state)
│   ├── phase-executor.py (NEW: run current phase tasks)
│   ├── next-task.sh (NEW: show next incomplete task)
│   ├── show-progress.sh (NEW: human-friendly progress)
│   ├── approve-phase.sh (NEW: approve & start phase)
│   └── [existing scripts: ingest-video.sh, batch-ingest.sh, etc.]
│
├── test_battery/ (untouched — 20 files)
│
└── DELETED:
    ❌ cloud.md
    ❌ IMPLEMENTATION_INDEX.md
    ❌ NAVIGATION_SYSTEM_EVALUATION.md
    ❌ MASTER_PLAN.md (if no unique content)
    ❌ TEST_BATTERY_PLAN.md (consolidated into V2)
    ❌ ARCHITECTURE_PLAN_FINAL.md (moved to docs/)
    ❌ llm-wiki.md (moved to docs/)
```

---

## EXECUTION STEPS (In Order)

### Phase A: Preparation (30 min)

- [ ] Read this checklist (2 min)
- [ ] Backup current repo state (git status, git log)
  - All changes will be traceable in git
- [ ] Confirm: No uncommitted changes? (if yes, stash or commit)
- [ ] Confirm: CLAUDE.md is backed up? (read to memory)

### Phase B: Create New Structure (2 hours)

#### Step B1: Finalize CLAUDE_AUTOMATED.md (30 min)
- [ ] Read original CLAUDE.md completely (keep in memory)
- [ ] Create CLAUDE_AUTOMATED.md with:
  - YAML frontmatter (150 lines)
  - Full kernel §0-§9 (original content)
  - Full domain §10 (original content)
  - Automation instructions
- [ ] Validate: No content lost from original CLAUDE.md
- [ ] Save: CLAUDE_AUTOMATED.md

#### Step B2: Create docs/ folder + move large docs (45 min)
- [ ] Create docs/ folder
- [ ] Move ARCHITECTURE_PLAN_FINAL.md → docs/ARCHITECTURE.md
- [ ] Move NAVIGATION_SYSTEM_EVALUATION.md → docs/EVALUATION.md
- [ ] Move llm-wiki.md → docs/ORIGINAL_CONCEPT.md
- [ ] Create docs/IMPLEMENTATION_GUIDE.md (new, ~500 lines)
  - How to run scripts
  - What each script does
  - Expected outputs
  - How to interpret progress reports

#### Step B3: Create scripts/ automation (45 min)
- [ ] Write scripts/state-manager.py (150 lines)
  - Read YAML from CLAUDE_AUTOMATED.md
  - Write state updates back
  - Manage phase transitions
- [ ] Write scripts/phase-executor.py (200 lines)
  - Determine current phase
  - Show next task
  - Execute task (placeholder: just show instructions)
- [ ] Write scripts/next-task.sh (30 lines)
  - Show next incomplete task in human-friendly format
- [ ] Write scripts/show-progress.sh (50 lines)
  - Display progress report
  - Show time estimates
  - Show next actions
- [ ] Write scripts/approve-phase.sh (40 lines)
  - Mark optimization as approved
  - Update state
  - Trigger phase-executor

#### Step B4: Create .env.example (15 min)
- [ ] Create .env.example with template configs
  - VAULT_PATH
  - AUTOMATION_ENABLED
  - LOG_LEVEL
  - etc.

### Phase C: Validation (1 hour)

- [ ] CLAUDE_AUTOMATED.md:
  - [ ] YAML parses cleanly (no syntax errors)
  - [ ] All original content preserved
  - [ ] Frontmatter has all fields
  - [ ] Scripts can read it
  
- [ ] docs/ folder:
  - [ ] All large docs moved
  - [ ] No content lost
  - [ ] All links updated in README
  
- [ ] scripts/:
  - [ ] All scripts executable (chmod +x)
  - [ ] ./scripts/next-task.sh works
  - [ ] ./scripts/show-progress.sh works
  - [ ] ./scripts/approve-phase.sh works
  
- [ ] Test automation:
  - [ ] python3 scripts/state-manager.py --read-state
  - [ ] Output shows current phase = 1
  - [ ] ./scripts/next-task.sh shows "Next: O1"

### Phase D: Cleanup (30 min)

- [ ] Delete old files (via git rm):
  - [ ] cloud.md
  - [ ] IMPLEMENTATION_INDEX.md
  - [ ] NAVIGATION_SYSTEM_EVALUATION.md
  - [ ] ARCHITECTURE_PLAN_FINAL.md (copy moved to docs/)
  - [ ] llm-wiki.md (copy moved to docs/)
  - [ ] TEST_BATTERY_PLAN.md (if superseded by V2)
  - [ ] MASTER_PLAN.md (if no unique content)

- [ ] Update README.md:
  - [ ] Add "New Structure" section
  - [ ] Add "How to Run Automation" section
  - [ ] Update links to docs/
  - [ ] Add script documentation

- [ ] Git commit:
  - [ ] git add .
  - [ ] git commit -m "Refactor: Automation-first structure (CLAUDE_AUTOMATED.md as single source of truth)"
  - [ ] git log --oneline (verify commit)

### Phase E: Validation Round 2 (15 min)

- [ ] Test: `./scripts/next-task.sh` → outputs human-friendly next task
- [ ] Test: `./scripts/show-progress.sh` → outputs progress report
- [ ] Test: `./scripts/approve-phase.sh O1 O2` → updates state
- [ ] Verify: README.md has clear instructions
- [ ] Verify: No broken links

### Phase F: Documentation (15 min)

- [ ] Update memory: Log the refactoring completion
- [ ] Create: First progress report
- [ ] Ready: For Phase 1 execution

---

## TOTAL TIME ESTIMATE

| Phase | Task | Time | Status |
|-------|------|------|--------|
| A | Prep | 30 min | ⏳ |
| B1 | CLAUDE_AUTOMATED.md | 30 min | ⏳ |
| B2 | docs/ folder | 45 min | ⏳ |
| B3 | scripts | 45 min | ⏳ |
| B4 | .env.example | 15 min | ⏳ |
| C | Validation 1 | 1 hour | ⏳ |
| D | Cleanup + commit | 30 min | ⏳ |
| E | Validation 2 | 15 min | ⏳ |
| F | Documentation | 15 min | ⏳ |
| **TOTAL** | | **~4 hours** | ⏳ |

---

## BENEFITS AFTER REFACTORING

✅ **Single entry point**: CLAUDE_AUTOMATED.md (no confusion)  
✅ **Fully automated**: Scripts run autonomously  
✅ **No human reading required**: Outputs are intuitive summaries  
✅ **No redundancy**: Each file has one purpose  
✅ **No missing context**: State is centralized in YAML  
✅ **Scalable**: Same pattern works for multiple vaults  
✅ **Reproducible**: Git history shows all changes  

---

## ROLLBACK PLAN (If needed)

If something breaks:

```bash
# Easy rollback (last commit)
git revert HEAD

# Or reset to before refactoring
git reset --hard <commit-before-refactoring>

# All old files still in git history
git checkout <old-commit> -- cloud.md IMPLEMENTATION_INDEX.md ...
```

---

## APPROVAL REQUIRED

Before starting, confirm:

- [ ] Understand the refactoring goals
- [ ] Agree with the new structure
- [ ] Ready to execute 4-hour refactoring
- [ ] OK with deleting cloud.md, IMPLEMENTATION_INDEX.md, etc.

---

**Ready to start?**

Reply: "Start Refactoring Phase A"  
Then: Follow steps A → F in order

Or if you have questions: Ask before starting (safer than mid-execution changes)

