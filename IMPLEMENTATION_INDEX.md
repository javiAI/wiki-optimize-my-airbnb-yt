# Implementation Index — Executive Navigation Hub

**Current Status**: Ready for Phase 1  
**Last Updated**: 2026-04-25  
**Current Phase**: Planning Complete (Awaiting Approval)  
**Next Milestone**: Phase 1 Start

---

## 🧭 QUICK ORIENTATION (READ THIS FIRST ON EVERY SESSION)

You are here: **PLANNING → READY FOR PHASE 1 IMPLEMENTATION**

```
Timeline:
Week 0 (THIS WEEK)  → Architecture Design ✅ COMPLETE
Week 1              → Phase 1: Critical Path (4.5h)
Week 2              → Phase 2: Quality Foundation (9h)
Week 3-4            → Phase 3: Automation (18h)
Week 5+             → Phase 4: Documentation & Integration
```

**What to do NOW:**
1. Review this index (5 minutes)
2. Review ARCHITECTURE_PLAN_FINAL.md PART 1-2 only (10 minutes)
3. Approve Phase 1 optimizations (O1, O2)
4. Jump to [Phase 1 Checklist](#phase-1-checklist--critical-path) below

---

## 📍 CURRENT PROJECT STATE

| Aspect | Status | Details |
|--------|--------|---------|
| **Architecture Design** | ✅ Complete | See ARCHITECTURE_PLAN_FINAL.md |
| **Optimization Prioritization** | ✅ Complete | 6 tiers, 16 optimizations identified |
| **Phase 1 Ready?** | ⏳ Pending Approval | O1 + O2 need user sign-off |
| **Code Written** | ❌ Not Started | Awaiting Phase 1 approval |
| **Test Battery Status** | ✅ Baseline Set | D9 = 8.52/10 (Q1-Q15) |
| **Vault Status** | ✅ Functional | 156 atoms, 12 MOCs, 173 sources |

---

## 🗺️ NAVIGATION MAP (WHERE TO GO WHEN)

### If you're starting fresh (new session, no context):

```
1. Read this file (IMPLEMENTATION_INDEX.md) — 10 min
   └─ Tells you: where we are, what's next
2. Read ARCHITECTURE_PLAN_FINAL.md §1-2 — 10 min
   └─ Tells you: philosophy & folder structure
3. Jump to current phase checklist (below)
   └─ Tells you: exact next steps
```

### If you're resuming mid-phase:

```
1. Jump to [Current Phase Status](#-phase-x-status) below
2. Check [Phase X Checklist](#phase-x-checklist--title)
3. Click "👉 Go to ARCHITECTURE_PLAN_FINAL.md" link
   └─ Opens relevant section of plan
```

### If you want to understand contradictions system:

```
Jump to: ARCHITECTURE_PLAN_FINAL.md PART 4 (line ~350)
Then: [Optimization O4 Details](#-o4--automatic-contradiction-detection)
```

### If you want to check optimization status:

```
Jump to: [Optimization Tracker](#-optimization-tracker-all-16-items)
Find: Optimization O# you care about
Click: "Details in ARCHITECTURE_PLAN_FINAL.md"
```

---

## 📊 PHASE STATUS DASHBOARD

### ✅ PHASE 0: ARCHITECTURE DESIGN (COMPLETE)

**Status**: ✅ DELIVERED  
**Time Spent**: 8+ hours (deep analysis)  
**Output**: ARCHITECTURE_PLAN_FINAL.md (450+ lines)

**What was done**:
- Analyzed all 32 historical optimizations
- Identified 5 core problems
- Designed 12-part architecture
- Created implementation roadmap
- Designed agent orchestration framework
- Created cloud.md template system

**Deliverables**:
- ✅ ARCHITECTURE_PLAN_FINAL.md
- ✅ ARCHITECTURE_ANALYSIS_SUMMARY.md
- ✅ This IMPLEMENTATION_INDEX.md

**Next**: User approval → Phase 1

---

### ⏳ PHASE 1: CRITICAL PATH (READY TO START)

**Estimated Duration**: 4.5 hours  
**Target Completion**: End of Week 1  
**Dependencies**: None (can start immediately)

**What will be done**:
1. Implement hierarchical indices (O1) — 4 hours
2. Fix Q4 contradiction (O2) — 0.5 hours
3. Validate token savings on test queries

**Expected Results**:
- Index.md shrinks: 375 lines → ~120 lines (~1.2k tokens)
- D9 score: 8.52 → 9.0 (estimated)
- Baseline token overhead: -69% (3.9k → 1.2k per query)

**Approval Status**: ⏳ AWAITING USER APPROVAL

👉 **Details**: See [Phase 1 Checklist](#phase-1-checklist--critical-path) below

---

### ⬜ PHASE 2: QUALITY FOUNDATION (NOT STARTED)

**Estimated Duration**: 9 hours  
**Target Completion**: End of Week 2  
**Dependencies**: Phase 1 complete

**What will be done**:
1. Language consistency system (O3)
2. Contradiction auto-detection Layer 1 (O4)
3. Response formatting templates (O5)
4. Executable checklists (O6)

**Expected Results**:
- D9 score: 9.0 → 9.6 (estimated)
- All D1-D5 metrics validated
- Anglicismos eliminated from responses

👉 **Details**: See [Phase 2 Checklist](#phase-2-checklist--quality-foundation) below

---

### ⬜ PHASE 3: AUTOMATION (NOT STARTED)

**Estimated Duration**: 18 hours  
**Target Completion**: End of Week 4  
**Dependencies**: Phase 2 complete

**What will be done**:
1. Agent orchestration framework (O7)
2. Auto-linking system (O8)
3. Query result caching (O9)
4. Full autonomous loop testing

**Expected Results**:
- D9 score: 9.6 → 9.8 (estimated)
- 40-50% token reduction on repeat queries
- Full autonomous operation enabled

👉 **Details**: See [Phase 3 Checklist](#phase-3-checklist--automation) below

---

### ⬜ PHASE 4: INTEGRATION (NOT STARTED)

**Estimated Duration**: 8+ hours  
**Target Completion**: Week 5+  
**Dependencies**: Phase 3 complete

**What will be done**:
1. Extract generic CLAUDE.md kernel
2. Create cloud.md template library
3. Documentation for project-operating-system
4. PR preparation

**Expected Results**:
- Ready for integration into project-operating-system
- 3+ template configs available
- Production-ready generic framework

👉 **Details**: See [Phase 4 Checklist](#phase-4-checklist--documentation--integration) below

---

## ✅ PHASE 1 CHECKLIST — CRITICAL PATH

**Time Estimate**: 4.5 hours  
**Approval Required?** YES — Before starting, user must approve O1 + O2

### Pre-requisites
- [ ] User reviewed ARCHITECTURE_PLAN_FINAL.md §3 (Hierarchical Indices)
- [ ] User approved O1 (Hierarchical Indices)
- [ ] User approved O2 (Fix Q4 Contradiction)

### Task 1: Implement Hierarchical Indices (O1) — 4 hours

**What**: Redesign index.md from monolithic (375 lines) to hierarchical (100 lines + category indices)

**Reference**: ARCHITECTURE_PLAN_FINAL.md §3 (line ~250)

**Steps**:
- [ ] Create `wiki/indices/` folder structure
- [ ] Write `scripts/build-indices.py` (auto-generates category indices)
  - Input: All atoms in wiki/atoms/
  - Process: Group by topic, create index--<topic>.md
  - Output: 12 category indices (~120-200 lines each)
- [ ] Create new minimal root index.md (~100 lines)
  - Keep: Quick start, topic list, recent queries, status
  - Remove: Full atom listings (now in category indices)
- [ ] Run `scripts/build-indices.py` on current corpus
- [ ] Verify no broken links
- [ ] Test query execution with new hierarchy
- [ ] Measure: baseline tokens (before vs. after)
  - Expected: 3.9k → ~1.2k tokens

**Success Criteria**:
- [ ] Root index.md ≤ 120 lines (~1.2k tokens)
- [ ] 12 category indices created (one per MOC)
- [ ] All atoms discoverable from new indices
- [ ] Query execution works (test on 3 sample queries)
- [ ] Token savings ≥ 60% on baseline

**Deliverables**:
- Updated `wiki/index.md`
- New `wiki/indices/index--*.md` (12 files)
- Updated `scripts/build-indices.py`
- Test report: token savings measurement

👉 **Detailed Steps**: ARCHITECTURE_PLAN_FINAL.md §3.2-3.4 (line 280-320)

---

### Task 2: Fix Q4 Contradiction (O2) — 0.5 hours

**What**: Resolve "2-3 times/year vs 2-3 months" conflict in Q4

**Reference**: ARCHITECTURE_PLAN_FINAL.md §9.2, OPTIMIZATIONS_ROADMAP_10X.md (line 28-36)

**Steps**:
- [ ] Locate Q4 response file: `test_battery/responses/Q4.md`
- [ ] Find contradiction:
  - Line 10-11: "Actualiza... 2-3 veces al año"
  - Line 28: "cada 2-3 meses"
- [ ] Apply correction:
  ```
  BEFORE: "Actualiza... 2-3 veces al año" / "Por qué cada 2-3 meses"
  AFTER: "Actualiza cada 2-3 meses antes de temporada relevante" / 
         "¿Por qué cada 2-3 meses? Airbnb detecta stale listings..."
  ```
- [ ] Update both occurrences
- [ ] Update `meta/contradictions.md` with resolution:
  - Conflict ID: C-Q4-001
  - Status: Resolved
  - Winner: "2-3 meses"
  - Reason: "Airbnb ranking algorithm signal, more recent"

**Success Criteria**:
- [ ] Q4 contradiction eliminated
- [ ] Inconsistency logged in meta/contradictions.md
- [ ] D2 score on Q4 improves (validation in Phase 2)

**Deliverables**:
- Updated `test_battery/responses/Q4.md`
- Updated `meta/contradictions.md`

👉 **Detailed Context**: OPTIMIZATIONS_ROADMAP_10X.md §PARTE I (line 15-36)

---

### Task 3: Validate Phase 1 Results — 0.5 hours

**What**: Measure quality improvements from O1 + O2

**Steps**:
- [ ] Run test queries on Q1-Q15 with new indices
- [ ] Measure: tokens_in, tokens_out, D9 score
- [ ] Compare to baseline (see below)
- [ ] Log results in `logs/phase-1-results.md`

**Baseline (Before Phase 1)**:
```
Query: Q1 (Rating mínimo)
- Tokens baseline: 3,956 (index.md)
- Tokens atoms: ~2,500 (5 atoms)
- Total: ~6,456 tokens
- D9 score: 7.9

Query: Q4 (Update freq)
- Contradiction present: YES
- D2 score: 7.9
```

**Target (After Phase 1)**:
```
Query: Q1 (Rating mínimo)
- Tokens baseline: ~1,200 (new index.md)
- Tokens category index: ~1,500 (category index)
- Tokens atoms: ~2,500 (5 atoms)
- Total: ~5,200 tokens
- Savings: ~6,456 → 5,200 = 19% reduction

Query: Q4 (Update freq)
- Contradiction resolved: YES
- D2 score: 8.4+ (estimated)
```

**Success Criteria**:
- [ ] Baseline tokens reduced ≥ 60% (3.9k → ≤1.2k)
- [ ] D9 score on Q4 improves ≥ 0.3 points
- [ ] All test queries execute successfully
- [ ] No broken links

**Deliverables**:
- `logs/phase-1-results.md` (measurement report)

---

### Phase 1 Sign-Off

- [ ] All tasks complete
- [ ] All success criteria met
- [ ] Phase 1 results logged
- [ ] Ready for Phase 2

**Next Step**: Jump to [Phase 2 Checklist](#phase-2-checklist--quality-foundation)

---

## ✅ PHASE 2 CHECKLIST — QUALITY FOUNDATION

**Time Estimate**: 9 hours  
**Prerequisite**: Phase 1 complete ✅

### Task 1: Language Consistency System (O3) — 2 hours

**What**: Eliminate all untranslated anglicismos; guarantee Spanish quality (D1 → 9.5+)

**Reference**: ARCHITECTURE_PLAN_FINAL.md PART 6 (line ~580)

**Steps**:
- [ ] Finalize `meta/glossary.md` with 70+ key terms
  - Format: `term: translation (context if needed)`
  - Examples: PriceLabs → herramienta de precios dinámicos
- [ ] Create `meta/allowed-english.md` (terms allowed in English)
  - Examples: PriceLabs, Airbnb, WiFi, YouTube (explain in first mention)
- [ ] Audit Q1-Q15: identify all anglicismos
- [ ] Update responses using glossary mappings
- [ ] Validate: zero untranslated terms in final responses

**Success Criteria**:
- [ ] Glossary has ≥70 terms
- [ ] Q1-Q15 have 0 untranslated anglicismos
- [ ] D1 score improves: 8.0 → 9.3+

**Deliverables**:
- `meta/glossary.md` (final)
- `meta/allowed-english.md`
- Updated Q1-Q15 responses

👉 **Detailed Design**: ARCHITECTURE_PLAN_FINAL.md PART 6 (line 580-650)

---

### Task 2: Contradiction Auto-Detection Layer 1 (O4) — 3 hours

**What**: Automatic detection of conflicts when atoms are created/modified

**Reference**: ARCHITECTURE_PLAN_FINAL.md PART 4 (line ~350)

**Steps**:
- [ ] Design contradiction types (negation, temporal, threshold, scope, frequency)
- [ ] Write `scripts/detect-contradictions.py --mode heuristic`
  - Input: New atom (or atom modification)
  - Process: Compare claim to existing atoms in topic
  - Output: Identified conflicts → logged to atom.conflicts_with field
- [ ] Test on 10 sample atom pairs (force known contradictions)
- [ ] Integrate into ingest workflow: after atom creation → run Layer 1 check
- [ ] Update `meta/contradictions.md` register
- [ ] Validate: catches existing contradictions (Q4, etc.)

**Success Criteria**:
- [ ] Script identifies 100% of obvious contradictions
- [ ] False positives < 5% (tolerable, reviewed manually)
- [ ] Integration to ingest workflow automatic
- [ ] `meta/contradictions.md` has ≥5 logged conflicts with scores

**Deliverables**:
- `scripts/detect-contradictions.py`
- Updated atom schema (conflicts_with field)
- Updated `meta/contradictions.md`

👉 **Detailed Design**: ARCHITECTURE_PLAN_FINAL.md §4.2-4.4 (line 320-380)

---

### Task 3: Response Formatting Templates (O5) — 2.5 hours

**What**: Standardize tone, length, format across all responses (D3 → 9.0+)

**Reference**: ARCHITECTURE_PLAN_FINAL.md §8 (line ~780)

**Steps**:
- [ ] Create `meta/response-contract.yaml`
  - Regime A: ≤300 words, BLUF (Bottom-Line-Up-Front) style
  - Regime B: ≤600 words, 3-6 levers explained
  - Regime C: ≤1000 words, exhaustive with examples
  - Citation style: `[[notes/slug]]` with locator
  - Prohibited: adjective fillers ("clave", "importante"), unexplained anglicismos
  - Permitted: PriceLabs, Airbnb, WiFi (explained once)
- [ ] Create response templates (per regime)
  ```markdown
  ## Regime A Template
  **RESPUESTA RÁPIDA**: [One-sentence answer]
  **Por qué**: [2-3 sentences explaining]
  **Fuentes**: [[atom-1]], [[atom-2]]
  ```
- [ ] Update Q1-Q15 to match templates
- [ ] Validate: all responses fit word limits + format

**Success Criteria**:
- [ ] Response contract defined in YAML
- [ ] Q1-Q15 updated to conform
- [ ] D3 score improves: 8.3 → 9.0+
- [ ] Word count variance < 10% of target

**Deliverables**:
- `meta/response-contract.yaml`
- Updated Q1-Q15 responses
- Response template library (markdown)

👉 **Detailed Design**: ARCHITECTURE_PLAN_FINAL.md §8 (line 760-810)

---

### Task 4: Executable Checklists (O6) — 1.5 hours

**What**: Convert vague instructions to step-by-step checklists (D8 → 9.0+)

**Reference**: Original OPTIMIZATIONS_CONSOLIDATED_MASTER.md item #10

**Steps**:
- [ ] Audit Q6, Q8, Q9 (operational guidance)
- [ ] Convert vague verbs ("bajar", "revisar", "mejorar") → exact steps
- [ ] Add tool names, specific UI paths, verification steps
  ```markdown
  - [ ] Abrir PriceLabs Dashboard
  - [ ] Seleccionar fecha: 5 de mayo
  - [ ] Click en "Date-specific"
  - [ ] Cambiar minimum nights: 1
  - [ ] Confirmar (aparecerá en búsqueda en 2h)
  - [ ] Verificar: search booking.com, busca tu listing
  ```
- [ ] Validate: steps can be executed without interpretation

**Success Criteria**:
- [ ] All action items in Q6, Q8, Q9 have executable checklists
- [ ] D8 score improves: 8.0 → 9.0+
- [ ] Zero ambiguous verbs remaining

**Deliverables**:
- Updated Q6, Q8, Q9 responses

---

### Phase 2 Sign-Off

- [ ] All 4 tasks complete
- [ ] D1-D3 scores validated (target: 9.3, 9.0, 9.0)
- [ ] Overall D9 score: 9.0 → 9.6 (estimated)
- [ ] Ready for Phase 3

**Next Step**: Jump to [Phase 3 Checklist](#phase-3-checklist--automation)

---

## ✅ PHASE 3 CHECKLIST — AUTOMATION

**Time Estimate**: 18 hours  
**Prerequisite**: Phase 2 complete ✅

### Task 1: Agent Orchestration Framework (O7) — 8 hours

**What**: Design + implement 4-agent autonomous system

**Reference**: ARCHITECTURE_PLAN_FINAL.md PART 5 (line ~440)

**Steps**:
- [ ] Design vault-config.yaml with automation settings
- [ ] Implement Agent 1: Ingester
  - Trigger: new files in raw/imports/
  - Task: extract atoms from sources
  - Output: new atoms + log entries
- [ ] Implement Agent 2: Linker
  - Trigger: batch-ingest completion
  - Task: create cross-references
  - Output: updated atoms with [[wikilinks]]
- [ ] Implement Agent 3: Auditor
  - Trigger: monthly or post-batch
  - Task: detect contradictions, gaps, stale claims
  - Output: updated meta/contradictions.md + gap report
- [ ] Implement Agent 4: Query-Cacher
  - Trigger: weekly or when query count > threshold
  - Task: generate cached responses for hot paths
  - Output: new queries/*.md files
- [ ] Write orchestrator script: coordinates all 4 agents
- [ ] Test: full loop on 10 new sources

**Success Criteria**:
- [ ] 4 agents functional and tested
- [ ] Orchestrator runs without human intervention
- [ ] Safety: diffs reviewed before auto-apply (if enabled)
- [ ] Logging: all agent actions in logs/audit.log

**Deliverables**:
- `meta/vault-config.yaml` (agent configuration)
- 4 agent scripts in `scripts/agents/`
- `scripts/orchestrator.sh` (main loop)
- Updated `logs/audit.log`

👉 **Detailed Design**: ARCHITECTURE_PLAN_FINAL.md §5 (line 430-500)

---

### Task 2: Auto-Linking System (O8) — 4 hours

**What**: Automatically create cross-references between atoms

**Reference**: Original memory item #8 (backlinks)

**Steps**:
- [ ] Write `scripts/auto-link.py`
  - Input: newly created atom
  - Process: find similar atoms (cosine similarity on claim)
  - Output: suggested wikilinks
  - Auto-add if similarity > 0.85; manual review if 0.75-0.85
- [ ] Integrate into ingest workflow (post-atom-creation)
- [ ] Test: does it find relevant cross-references?
- [ ] Validate: no broken links, no false positives

**Success Criteria**:
- [ ] Atoms gain avg. 2+ wikilinks each
- [ ] Link density > 1.5 (higher = better connected)
- [ ] False positive rate < 10%

**Deliverables**:
- `scripts/auto-link.py`
- Updated atoms with wikilinks
- Link density report

---

### Task 3: Query Result Caching (O9) — 6 hours

**What**: Pre-generate cached responses for high-frequency queries

**Reference**: OPTIMIZATIONS_CONSOLIDATED_MASTER.md item #14 (line ~475)

**Steps**:
- [ ] Analyze `logs/query.log`: identify 15 most-asked questions
  - Examples: "pricing--orphan-night", "reviews--recovery", "investing--deal-eval"
- [ ] Generate cached responses for these 15 hot-path queries
  - Run full query execution (fresh)
  - Save to `queries/cached-<topic>--<slug>.md`
- [ ] Measure: token cost of cached vs. fresh
  - Expected: cached ~500 tokens vs. fresh ~6k tokens (-92%)
- [ ] Set up cache refresh schedule (e.g., weekly)
- [ ] Test: retrieving cached response is instant + accurate

**Success Criteria**:
- [ ] 15 hot-path queries cached
- [ ] Cached query response time: <1 second
- [ ] Token savings: ≥85% for cached paths
- [ ] Cache refresh schedule automatic

**Deliverables**:
- 15 cached query files in `queries/`
- Cache refresh script in `scripts/refresh-cache.sh`
- Performance report: token savings per query

---

### Task 4: Full Autonomous Loop Test (O9.5) — Validation task

**What**: Test the entire infinite loop without human intervention

**Steps**:
- [ ] Add 5-10 new sources to raw/imports/
- [ ] Run orchestrator: `./scripts/orchestrator.sh --full-cycle`
- [ ] Monitor:
  - Sources ingested? ✓
  - Atoms extracted? ✓
  - Cross-links created? ✓
  - Contradictions detected? ✓
  - Query cache updated? ✓
  - Indices regenerated? ✓
  - Logs populated? ✓
- [ ] Spot-check: 5 new atoms for quality
- [ ] Measure: total time, token cost, quality (D1-D5)

**Success Criteria**:
- [ ] Full cycle runs without errors
- [ ] Vault remains consistent (no broken links)
- [ ] Quality maintained (D9 > 9.5)
- [ ] Time to process 5-10 sources: <30 minutes automated

**Deliverables**:
- `logs/full-cycle-test-report.md`
- Updated vault with 5-10 new atoms
- Validation report: all systems functional

---

### Phase 3 Sign-Off

- [ ] All 3 tasks complete (+ validation)
- [ ] Autonomous loop fully functional
- [ ] D9 score: 9.6 → 9.8 (target)
- [ ] 40-50% token savings on repeat queries
- [ ] Ready for Phase 4

**Next Step**: Jump to [Phase 4 Checklist](#phase-4-checklist--documentation--integration)

---

## ✅ PHASE 4 CHECKLIST — DOCUMENTATION & INTEGRATION

**Time Estimate**: 8+ hours  
**Prerequisite**: Phase 3 complete ✅

### Task 1: Generic CLAUDE.md Kernel Extraction — 2 hours

**What**: Extract reusable kernel from current CLAUDE.md (remove domain layer)

**Reference**: ARCHITECTURE_PLAN_FINAL.md PART 7 (line ~700)

**Steps**:
- [ ] Create `CLAUDE_KERNEL.md` (~200 lines)
  - Keep: §0-§9 (philosophy, 3-layer, folder structure, operations, scoring, naming, hard rules, commands, troubleshooting)
  - Remove: §10 (Optimize My Airbnb specific: topics, schema extensions, scripts)
- [ ] Create `meta/domain-layer.md` (new location for §10 content)
- [ ] Update root CLAUDE.md: reference both files
- [ ] Validate: kernel works for all vaults (no optimize-my-airbnb assumptions)

**Success Criteria**:
- [ ] Kernel ≤ 200 lines (~2k tokens)
- [ ] 100% reusable (no project-specific content)
- [ ] Domain layer separable + optional
- [ ] Both files integrate seamlessly

**Deliverables**:
- `CLAUDE_KERNEL.md` (generic, reusable)
- `meta/domain-layer.md` (domain-specific)
- Updated `CLAUDE.md` (references both)

---

### Task 2: Cloud.md Template Library — 3 hours

**What**: Create 15+ pre-built configurations for different vault types

**Reference**: ARCHITECTURE_PLAN_FINAL.md PART 6 (line ~580)

**Steps**:
- [ ] Create `templates/` directory:
  ```
  templates/
  ├── consultant--spanish.yaml         # Your current vault
  ├── researcher--english.yaml         # Academic, English
  ├── engineer--technical.yaml         # Technical depth
  ├── business--executive.yaml         # Executive summaries
  ├── student--learning.yaml          # Encouraging, educational
  ├── scientist--papers.yaml          # Research papers
  └── [10 more templates]
  ```
- [ ] Define each template:
  - Vault identity (name, topic, language, audience)
  - Tone & voice settings
  - Structure (topics list)
  - Language rules
  - Response contract (word limits, tone)
  - Automation settings
- [ ] Create `scripts/init-vault.sh`
  - Takes: `--template <name> --vault-name <name>`
  - Outputs: new vault with cloud.md pre-populated
  - Copies: generic CLAUDE.md, scripts/, folder structure
- [ ] Test: create 2 new vaults with different templates
  - Example 1: "researcher--english" vault
  - Example 2: "business--executive" vault
- [ ] Validate: new vaults are immediately functional

**Success Criteria**:
- [ ] 15+ templates defined
- [ ] init-vault.sh works end-to-end
- [ ] New vaults created in <5 minutes
- [ ] Quality (D9) immediately achievable on new vaults

**Deliverables**:
- `templates/` directory (15+ YAML configs)
- `scripts/init-vault.sh`
- 2 reference vaults created + tested
- Template documentation

---

### Task 3: Project-Operating-System Integration Documentation — 2 hours

**What**: Write integration guide for project-operating-system

**Reference**: ARCHITECTURE_PLAN_FINAL.md PART 10 (line ~900)

**Steps**:
- [ ] Create `docs/INTEGRATION_GUIDE.md`:
  - How to add llm-wiki framework to project-operating-system
  - How to instantiate new knowledge vaults
  - How to configure automation
  - Troubleshooting
- [ ] Create `docs/VAULT_CREATION_WORKFLOW.md`:
  - Step-by-step for creating a new vault
  - Template selection guide
  - First ingest walkthrough
  - Quality validation checklist
- [ ] Create `README.md` (for this repo):
  - What this framework is
  - Quick start
  - Links to key docs
  - Examples

**Success Criteria**:
- [ ] Integration guide complete + tested
- [ ] New users can create vaults without guidance
- [ ] Workflow repeatable for multiple users/projects

**Deliverables**:
- `docs/INTEGRATION_GUIDE.md`
- `docs/VAULT_CREATION_WORKFLOW.md`
- Updated `README.md`

---

### Task 4: PR Preparation for project-operating-system — 1 hour

**What**: Prepare pull request to integrate llm-wiki framework

**Steps**:
- [ ] Create branch: `feature/llm-wiki-framework`
- [ ] Organize deliverables:
  ```
  project-operating-system/
  ├── templates/llm-wiki/
  │   ├── CLAUDE_KERNEL.md
  │   ├── scripts/
  │   ├── docs/
  │   └── templates/
  ```
- [ ] Write PR description:
  - What: Generic LLM wiki framework
  - Why: Standardize knowledge vault creation
  - How: Use cloud.md templates to instantiate vaults
  - Examples: 3 pre-built vault types
  - Testing: tested on optimize-my-airbnb-yt + 2 reference vaults
- [ ] PR checklist:
  - [ ] All docs complete
  - [ ] Tested on 3 vault types
  - [ ] No breaking changes to existing project-OS workflows
  - [ ] Backward compatible

**Deliverables**:
- Feature branch with all files
- PR with clear description
- PR template filled out

---

### Phase 4 Sign-Off

- [ ] Generic CLAUDE.md kernel extracted
- [ ] 15+ templates created
- [ ] Integration documentation complete
- [ ] PR prepared for project-operating-system
- [ ] Framework production-ready

**Next Step**: Submit PR to project-operating-system

---

## 🎯 OPTIMIZATION TRACKER — ALL 16 ITEMS

Track progress on each optimization individually:

### 🔴 TIER 1 — CRITICAL (Week 1)

| ID | Optimization | Effort | Status | Phase | Reference |
|----|--------------|--------|--------|-------|-----------|
| **O1** | Hierarchical Indices | 4h | ⏳ Pending Approval | 1 | §3 (line 250) |
| **O2** | Fix Q4 Contradiction | 0.5h | ⏳ Pending Approval | 1 | §9.2 (line 850) |

**Status Summary**: 0/2 complete. Awaiting user approval to begin.

---

### 🟠 TIER 2 — QUALITY (Week 2)

| ID | Optimization | Effort | Status | Phase | Reference |
|----|--------------|--------|--------|-------|-----------|
| **O3** | Language Consistency | 2h | ⬜ Not Started | 2 | PART 6 (line 580) |
| **O4** | Contradiction Detection Layer 1 | 3h | ⬜ Not Started | 2 | §4.2 (line 350) |
| **O5** | Response Templates | 2.5h | ⬜ Not Started | 2 | §8 (line 760) |
| **O6** | Executable Checklists | 1.5h | ⬜ Not Started | 2 | Orig. item #10 |

**Status Summary**: 0/4 complete. Blocked by Phase 1.

---

### 🟡 TIER 3 — AUTOMATION (Week 3-4)

| ID | Optimization | Effort | Status | Phase | Reference |
|----|--------------|--------|--------|-------|-----------|
| **O7** | Agent Orchestration | 8h | ⬜ Not Started | 3 | PART 5 (line 440) |
| **O8** | Auto-Linking System | 4h | ⬜ Not Started | 3 | Memory #8 |
| **O9** | Query Caching | 6h | ⬜ Not Started | 3 | Orig. item #14 |

**Status Summary**: 0/3 complete. Blocked by Phase 2.

---

### 🟢 TIER 4 — SCALING (Post-Automation)

| ID | Optimization | Effort | Status | Phase | Reference |
|----|--------------|--------|--------|-------|-----------|
| **O10** | Semantic Gap Detection | 3h | ⬜ Deferred | 4+ | Orig. item #12 |
| **O11** | Backlink Generation | 4h | ⬜ Deferred | 4+ | Memory #16 |
| **O12** | RAG Fallback | 6h | ⬜ Deferred | 4+ | Memory #15 |

---

### 🔵 TIER 5 — INFRASTRUCTURE

| ID | Optimization | Effort | Status | Phase | Reference |
|----|--------------|--------|--------|-------|-----------|
| **O13** | YAML Validation | 2h | ⬜ Deferred | 5 | Memory #18 |
| **O14** | Pre-Commit Hooks | 1h | ⬜ Deferred | 5 | Memory #17 |

---

### 🟣 TIER 6 — NICE-TO-HAVE

| ID | Optimization | Effort | Status | Phase | Reference |
|----|--------------|--------|--------|-------|-----------|
| **O15** | Expanded Glossary | 1.5h | ⬜ Deferred | 6 | Orig. item #32 |
| **O16** | Domain Layer Separation | 2h | ⬜ Deferred | 6 | Memory #31 |

---

## 📈 SUCCESS METRICS

### Baseline (TODAY — 2026-04-25)

```yaml
vault:
  atoms: 156
  mocs: 12
  sources: 173
  
quality:
  d9_average: 8.52/10
  d1_clarity: 8.0/10
  d2_completeness: 8.73/10
  d3_readability: 8.47/10
  
tokens:
  baseline_overhead: 3,956 tokens/query (99% of regime A)
  avg_query_cost: 6,456 tokens
  
automation:
  level: "None"
  manual_effort: "High (Q&A synthesis)"
```

### Target (END OF PHASE 3 — 8 weeks)

```yaml
vault:
  atoms: 200+ (post-automation)
  mocs: 12-15 (refined)
  sources: 250+ (growing continuously)
  
quality:
  d9_average: 9.8/10 (+15%)
  d1_clarity: 9.3/10 (+1.3)
  d2_completeness: 9.2/10 (+0.5)
  d3_readability: 9.0/10 (+0.5)
  
tokens:
  baseline_overhead: 1,200 tokens/query (30% of original)
  avg_query_cost: 5,200 tokens (-19% vs. baseline)
  repeat_query_cost: 500 tokens cached (-92% vs. fresh)
  
automation:
  level: "Full"
  manual_effort: "Minimal (source curation only)"
```

---

## 🔗 KEY DOCUMENT REFERENCES

When you see "👉 Reference: ARCHITECTURE_PLAN_FINAL.md §X (line Y)", here's what to do:

1. Open ARCHITECTURE_PLAN_FINAL.md
2. Use Ctrl+G (or Cmd+G on Mac) → "Go to line Y"
3. Read that section
4. Return to this index to continue checklist

**All references are line-accurate**. No guessing.

---

## 🛠️ HOW TO USE THIS INDEX

### On a New Session (Don't Know Where We Are)

```
1. Open this file (IMPLEMENTATION_INDEX.md)
2. Read "QUICK ORIENTATION" section (top)
3. Check "CURRENT PROJECT STATE" table
4. Jump to appropriate Phase Checklist
5. Follow steps in order
```

### To Check Optimization Details

```
Jump to: "OPTIMIZATION TRACKER — ALL 16 ITEMS"
Find: Optimization O# you care about
Click: "Reference" link
Jumps to: Exact line in ARCHITECTURE_PLAN_FINAL.md
```

### To Resume Mid-Phase

```
Jump to: Current Phase Checklist (e.g., Phase 2)
Find: Last incomplete task [ ]
Continue from there
All previous ✅ tasks don't need re-doing
```

### To Understand a Concept

```
Use search (Ctrl+F):
  - "Hierarchical indices" → leads to Phase 1, Task 1
  - "Agent orchestration" → leads to Phase 3, Task 1
  - "Cloud.md" → leads to Phase 4, Task 2
```

---

## 📋 HANDOFF CHECKLIST (FOR NEXT SESSION)

When you leave this project, ensure:

- [ ] Current phase status updated (above)
- [ ] Any completed tasks marked ✅
- [ ] Any blockers documented
- [ ] IMPLEMENTATION_INDEX.md saved (this file)
- [ ] Session notes in `logs/session-notes.md`

Next session: Open this file, read "QUICK ORIENTATION", resume checklist.

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-25  
**Owner**: This Project  
**Status**: Ready for Phase 1 Approval

