# cloud.md — Dynamic Configuration & Navigation Hub

**What is this?**: Central configuration file + navigation guide for LLM Wiki implementation  
**Why?**: Never lose context, even across sessions  
**When to read?**: Every time you start work on this project

---

## 🧭 ENTER HERE → IMPLEMENTATION_INDEX.md

**You are here**: `cloud.md` (this file)  
**Go here next**: [`IMPLEMENTATION_INDEX.md`](IMPLEMENTATION_INDEX.md) ← Click this, read sections in order

**Time investment**: 5-10 minutes → know exactly what to do next

---

## 📊 PROJECT STATE AT A GLANCE

```yaml
# Current Status (2026-04-25)
project:
  name: "LLM Wiki Framework — Generic, Replicable, Production-Ready"
  phase: "Phase 0 COMPLETE — Architecture Design Delivered"
  phase_status: "⏳ Awaiting approval for Phase 1"
  
architecture:
  status: "✅ COMPLETE"
  output_files: 
    - "ARCHITECTURE_PLAN_FINAL.md" (450+ lines)
    - "ARCHITECTURE_ANALYSIS_SUMMARY.md"
    - "IMPLEMENTATION_INDEX.md" ← YOU ARE HERE
  
optimization:
  total_identified: 16
  tier_1_pending: 2 (O1 + O2, ~4.5 hours)
  status: "Ready to implement"

vault_status:
  optimize_my_airbnb_yt:
    atoms: 156
    mocs: 12
    sources: 173
    quality_score: 8.52/10
    baseline_tokens: 3,956/query
```

---

## 🚀 QUICK START — DO THIS NOW

### For First Time on This Project:

```
1. Read this file (cloud.md) — 2 min
   └─ YOU ARE HERE
   
2. Open IMPLEMENTATION_INDEX.md — 10 min
   └─ Read "QUICK ORIENTATION" section
   └─ Check "CURRENT PROJECT STATE" table
   
3. Check "Phase 1 Checklist" in IMPLEMENTATION_INDEX.md
   └─ User approves O1 + O2
   └─ Begin Task 1 (Hierarchical Indices)
```

### For Returning to Project:

```
1. Open IMPLEMENTATION_INDEX.md
   └─ Jump to: "CURRENT PROJECT STATE"
   └─ Where are we? (check table)
   
2. Jump to: "[Phase X Status](#phase-x-status)"
   └─ What's incomplete?
   
3. Jump to: "Phase X Checklist"
   └─ Resume from last incomplete task [ ]
```

---

## 🗺️ DOCUMENT MAP (Know Where Everything Is)

| Document | Purpose | When to Read | Line Range |
|----------|---------|--------------|-----------|
| **ARCHITECTURE_PLAN_FINAL.md** | Complete architectural design | To understand the "why" and "how" | 1-450+ |
| **IMPLEMENTATION_INDEX.md** | Execution guide (phases, checklists, trackers) | To know what to do next | 1-700+ |
| **This file (cloud.md)** | Navigation hub + project state | To orient yourself | You are here |
| **meta/cloud.md** (in vault) | Vault-specific config (language, tone, agents) | For vault customization | See below |

---

## 🎯 WHAT WE'RE BUILDING (Why This Matters)

**Problem**: The current optimize-my-airbnb-yt vault works, but:
- ❌ Index.md bloats to 3.9k tokens (99% of budget)
- ❌ Contradictions found manually (Q4 took deep reading)
- ❌ Can't replicate to other knowledge domains
- ❌ No automation (vault stagnates without manual work)

**Solution**: Generic LLM Wiki Framework that:
- ✅ Reduces baseline from 3.9k → 1.2k tokens (69% savings)
- ✅ Auto-detects contradictions (3 layers)
- ✅ Works for ANY domain (research, business, learning, etc.)
- ✅ Fully autonomous agents (ingest → link → audit → cache)

**Target**: Quality 9.8/10, token savings 40-50% on repeat queries, 100% automation

---

## 📋 CURRENT PHASE DETAILS

### Phase 0: Architecture Design ✅ COMPLETE

**What was done**:
- Analyzed 32 historical optimizations
- Identified 5 core problems
- Designed 12-part architecture
- Created implementation roadmap
- Designed agent orchestration framework

**Output**:
- ✅ ARCHITECTURE_PLAN_FINAL.md
- ✅ ARCHITECTURE_ANALYSIS_SUMMARY.md
- ✅ IMPLEMENTATION_INDEX.md

**Status**: DELIVERED. User can review and approve.

---

### Phase 1: Critical Path ⏳ PENDING APPROVAL

**Estimated Duration**: 4.5 hours  
**What Will Happen**:
1. O1: Implement hierarchical indices (4h)
   - Root index: 375 → 100 lines
   - Create 12 category indices
   - Result: baseline tokens 3.9k → 1.2k (-69%)

2. O2: Fix Q4 contradiction (0.5h)
   - Resolve "2-3 veces/año vs 2-3 meses" conflict
   - Update meta/contradictions.md

**Expected Result**: D9 = 8.52 → 9.0

**Status**: ⏳ **AWAITING USER APPROVAL** (see below)

---

### Phases 2-4: Future

See IMPLEMENTATION_INDEX.md for full roadmap:
- Phase 2: Quality Foundation (Week 2, 9 hours)
- Phase 3: Automation (Week 3-4, 18 hours)
- Phase 4: Documentation & Integration (Week 5+)

---

## ✅ APPROVAL REQUIRED — BEFORE PHASE 1 STARTS

**What needs approval?**

User must approve:
- [ ] O1: Hierarchical Indices (4 hours)
- [ ] O2: Fix Q4 Contradiction (0.5 hours)

**How to approve**:

Reply to Claude with:
```
Approve Tier 1 (O1 + O2) for Phase 1 implementation.
Start immediately.
```

**What happens after approval**:
1. Phase 1 Checklist becomes active
2. Implementation begins (4.5 hour sprint)
3. Test battery validates improvements
4. Move to Phase 2

---

## 📁 HOW TO USE meta/cloud.md (Vault Configuration)

**Location**: Inside vault (once created): `$VAULT_PATH/meta/cloud.md`

**Purpose**: Vault-specific settings (language, tone, automation level, response rules)

**Example** (your current vault):
```yaml
---
# VAULT IDENTITY
vault_name: "Optimize My Airbnb"
vault_topic: "short-term-rental-optimization"
language: "spanish"
tone: "consultant"
audience: "property-owner"

# LANGUAGE RULES
languages:
  primary: spanish
  allow_english_terms: [PriceLabs, Airbnb, WiFi, YouTube]
  translate_other_terms: true

# AUTOMATION
agents_enabled: true
auto_approve_threshold: 0.90
update_frequency: "4_hours"

# RESPONSE RULES
response_contract:
  max_words: {A: 300, B: 600, C: 1000}
  citation_style: "obsidian_wikilinks"
---
```

**For other vaults**: Use templates (e.g., `templates/researcher--english.yaml`)

---

## 🔄 SYSTEM FOR STAYING ORIENTED

### Problem We're Solving:

> "How do I know where I am in the implementation plan?"  
> "Did I do this already?"  
> "What's the next step?"  
> "Where's the documentation for this decision?"

### Solution:

1. **cloud.md** (this file)
   - Quick state summary
   - Links to detailed docs
   - Approval checklist

2. **IMPLEMENTATION_INDEX.md**
   - Detailed state per phase
   - Checklists (what to do)
   - References to ARCHITECTURE_PLAN_FINAL.md
   - Optimization tracker (16 items)
   - Success metrics

3. **ARCHITECTURE_PLAN_FINAL.md**
   - "Why" and "how"
   - Detailed design
   - Line-accurate references
   - Rationale for every decision

### Workflow:

```
Every session:
  1. Open cloud.md (you are here)
  2. Check "PROJECT STATE AT A GLANCE"
  3. Jump to IMPLEMENTATION_INDEX.md
  4. Read "[Current Phase Status](#)" section
  5. Follow Phase X Checklist
  6. Each checklist item references ARCHITECTURE_PLAN_FINAL.md
  7. When done, mark [ ] → [✓] in IMPLEMENTATION_INDEX.md
  8. Move to next item
```

**Result**: Never lost, always know next step, never repeat work

---

## 📖 READING GUIDE (What to Read, When)

### IF you're new to this project:

**Read in order** (takes ~45 minutes):
1. This file (cloud.md) — 5 min
2. IMPLEMENTATION_INDEX.md — QUICK ORIENTATION — 5 min
3. ARCHITECTURE_PLAN_FINAL.md — §1 (Philosophy) — 5 min
4. ARCHITECTURE_PLAN_FINAL.md — §2 (Folder Structure) — 10 min
5. IMPLEMENTATION_INDEX.md — Phase 1 Checklist — 10 min
6. Approve O1 + O2

**Why this order?**
- cloud.md → get oriented
- Philosophy → understand intent
- Folder structure → mental model
- Phase 1 Checklist → know exactly what to do
- Design docs → reference as needed

### IF you're resuming mid-implementation:

**Read in order** (takes ~10 minutes):
1. cloud.md — PROJECT STATE section — 2 min
2. IMPLEMENTATION_INDEX.md — Current Phase Status — 3 min
3. Jump to Phase X Checklist — 5 min
4. Resume from [ ] incomplete item

### IF you need to understand a specific decision:

**Use search + jump**:
- Want to know about hierarchical indices? 
  - Search "Hierarchical" in IMPLEMENTATION_INDEX.md
  - Click "Reference: ARCHITECTURE_PLAN_FINAL.md §3 (line 250)"
  - Opens ARCHITECTURE_PLAN_FINAL.md at that line
  - Return to IMPLEMENTATION_INDEX.md, continue checklist

---

## ⚙️ HOW THIS SYSTEM WORKS (Why It Won't Fail)

### Design Principles:

1. **Redundancy**: Same info in multiple places (cloud.md ↔ IMPLEMENTATION_INDEX.md ↔ ARCHITECTURE_PLAN_FINAL.md)
   - If you forget where you are: cloud.md always shows current state
   - If you want details: IMPLEMENTATION_INDEX.md has full checklist
   - If you want design rationale: ARCHITECTURE_PLAN_FINAL.md has everything

2. **Line-Accurate References**: No guessing
   - "See §3.2 (line 280)" → you know exactly where to look
   - No "search for paragraph X" ambiguity
   - Ctrl+G → paste line number → instant navigation

3. **Checklist-Driven**: Every phase has [✓] checkboxes
   - You never wonder "did I do this?"
   - Mark complete, move on
   - Resume always shows last incomplete task

4. **Automated-Ready**: Can become fully automated
   - Right now: manual human checklist marking
   - Future: script reads IMPLEMENTATION_INDEX.md, shows next task
   - YAML structure enables both human + machine reading

### Failure Prevention:

| Risk | Prevention |
|------|-----------|
| "Where are we?" | cloud.md PROJECT STATE always current |
| "Did I do O1?" | IMPLEMENTATION_INDEX.md tracks O1-O16 |
| "What's next?" | Phase X Checklist shows next [ ] item |
| "I forgot the decision" | Reference → line number → find it |
| "New session, lost context" | Read cloud.md, know where we are in 2 min |

---

## 🤖 AUTOMATION-READY STRUCTURE

**Today** (Manual):
- You read IMPLEMENTATION_INDEX.md
- Mark [ ] → [✓] as you complete tasks
- Tell Claude next steps

**Tomorrow** (Automated, if desired):
```python
# Hypothetical future automation
import yaml

# Read IMPLEMENTATION_INDEX.md
state = load_yaml("IMPLEMENTATION_INDEX.md")

# Find next incomplete task
next_task = state["phase_1"]["tasks"] \
  .filter(status == "pending") \
  .first()

# Show user
print(f"Next task: {next_task.name}")
print(f"Description: {next_task.description}")
print(f"Reference: {next_task.reference_line}")

# If user says "done"
mark_complete(next_task)
save_state(state)
show_next_task()
```

**Why this structure works for both**:
- YAML frontmatter = machine-readable
- Markdown content = human-readable
- Checklists + references = both can parse
- No special format needed

---

## 🎯 SUCCESS = NEVER BEING LOST

**This system succeeds if**:

✅ You open this project after 2 weeks away  
✅ Read cloud.md (2 minutes)  
✅ Know exactly: phase, last completed task, next steps  
✅ No rereading, no context loss  
✅ Continuous progress  

---

## 📞 HOW TO GET UNSTUCK

**If you don't know what to do**:

1. Open IMPLEMENTATION_INDEX.md
2. Jump to: "[CURRENT PROJECT STATE](#-current-project-state)"
3. Find: what phase are we in?
4. Jump to: "Phase X Checklist"
5. Find: first [ ] unchecked item
6. Do that task

**If you don't understand a decision**:

1. Click the "Reference" link in that checklist item
2. Opens ARCHITECTURE_PLAN_FINAL.md at exact line
3. Read the rationale
4. Back to checklist

**If something is wrong**:

1. Document the issue in `logs/session-notes.md`
2. Update IMPLEMENTATION_INDEX.md with blocker
3. Mark status: "⚠️ BLOCKED" with reason
4. Next session: Claude reads blocker, helps unblock

---

## 📝 HANDOFF TO NEXT SESSION

When you finish for the day:

1. Update cloud.md PROJECT STATE section (current phase, what's complete)
2. Mark all completed [ ] → [✅] in IMPLEMENTATION_INDEX.md
3. If blocked: document in [Blocker](#) section
4. Save files
5. Next session: Claude opens cloud.md, knows where we are

---

## 🚦 NEXT IMMEDIATE STEPS

**Right now** (before you do anything else):

1. ✅ You've read cloud.md (this file)
2. ⏳ Open IMPLEMENTATION_INDEX.md (next)
3. ⏳ Read "QUICK ORIENTATION" section (5 min)
4. ⏳ Decide: Approve O1 + O2 for Phase 1?

**If you approve**:
- Phase 1 Checklist activates
- 4.5 hour sprint begins
- Hierarchical indices implemented
- Test battery validates

**If you have questions**:
- Ask before approving
- Reference ARCHITECTURE_PLAN_FINAL.md §X (line Y) for details

---

## 📄 DOCUMENT VERSIONS

| File | Version | Last Updated | Status |
|------|---------|--------------|--------|
| cloud.md (this file) | 1.0 | 2026-04-25 | Complete |
| IMPLEMENTATION_INDEX.md | 1.0 | 2026-04-25 | Complete |
| ARCHITECTURE_PLAN_FINAL.md | 2.0 | 2026-04-25 | Complete |

All synchronized. No conflicts.

---

## 🎬 FINAL INSTRUCTION

**Close this file.** Open [`IMPLEMENTATION_INDEX.md`](IMPLEMENTATION_INDEX.md) now.

Read: "QUICK ORIENTATION" section.

Come back with approval or questions.

---

**You are not lost. You know exactly what to do next.**  
**This system exists so you never lose focus or context.**

Welcome to Phase 0 completion. Ready for Phase 1?

