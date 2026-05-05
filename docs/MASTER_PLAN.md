---
name: MASTER_PLAN — Memory Vaults Integration + OMA Optimizations
description: Consolidated strategy for Fase G (pos) integration and 20 OMA vault optimizations, organized for discussion and staged implementation
type: project
originSessionId: 2c34e1a2-f772-4b90-bb0f-06b8be2bc635
---

# MASTER_PLAN — Memory Vaults & Optimizations

**Purpose**: Unified roadmap combining:
1. **Part I**: Complete integration of Memory Vaults (Fase G) into project-operating-system
2. **Part II**: 20 optimizations for Optimize My Airbnb vault (prioritized, staged)

**Status**: Documentation complete. Ready for discussion & phased implementation.

---

# PART I: Memory Vault Integration (Fase G)

## Context

The `project-operating-system` meta-repo generates complete project repos via a questionnaire → profile → Handlebars templates pipeline. It's designed in Phases (A-G), with **Fase G (Knowledge Plane) already documented** in `docs/ARCHITECTURE.md` as an opt-in feature. This plan fills in implementation details using patterns proven in Optimize My Airbnb.

**Key insight**: We're not inventing something new; we're making the documented Fase G concrete.

---

## I.1 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  CONTROL PLANE (meta-repo pos)                      │
│  - questionnaire/schema.yaml (new field)            │
│  - templates/vault/schema.md.hbs (generator)        │
│  - .claude/rules/memory.md (path-scoped)            │
│  - hooks/vault-init.py (post-generation)            │
└──────────────────────┬────────────────────────────┘
                       │ generates
                       ▼
┌─────────────────────────────────────────────────────┐
│  RUNTIME PLANE (repo generado)                      │
│  - CLAUDE.md (§Z Memory Plane reference)            │
│  - .claude/rules/memory.md (vault-specific)         │
│  - vault/ (optional, opt-in)                        │
│    ├── schema.md (configuration)                    │
│    ├── raw/ (immutable sources)                     │
│    └── wiki/ (LLM-synthesized index + atoms)        │
│       ├── MEMORY.md (master index)                  │
│       ├── <topic>_<type>.md (individual atoms)      │
│       └── .gitkeep                                  │
└─────────────────────────────────────────────────────┘
```

**Three-stores model** (adapted from OMA):
- **Raw** (`vault/raw/`): Immutable sources. Never modified after creation.
- **Wiki** (`vault/wiki/`): Synthesized atoms + MOCs + cached queries. LLM-owned.
- **Schema** (`vault/schema.md`): Configuration & conventions. Generated from pos questionnaire.

---

## I.2 Fase G1 — Questionnaire Field

**Scope**: Add memory plane enablement to questionnaire.

**File**: `questionnaire/schema.yaml`

```yaml
sections:
  - id: G
    name: Memory & Knowledge
    description: Gestión de conocimiento acumulativo en el proyecto.
    fields:
      - path: integrations.knowledge_plane.enabled
        type: boolean
        default: false
        description: "Activar vault/ con esquema memory-friendly."
      
      - path: integrations.knowledge_plane.schema_type
        type: enum
        values: ["minimal", "research", "architecture", "team-docs"]
        default: "minimal"
        condition: "integrations.knowledge_plane.enabled == true"
        description: |
          Plantilla de esquema:
          - minimal: user/feedback/project (single-project teams)
          - research: + reference (papers, external resources)
          - architecture: + pattern (code/design decisions)
          - team-docs: + all above + sync points (multi-person teams)
```

**Example profile**:
```yaml
# nextjs-app.yaml
answers:
  "integrations.knowledge_plane.enabled": true
  "integrations.knowledge_plane.schema_type": "team-docs"
```

**Estimate**: 2k tokens | 1 session | Simple schema merge

---

## I.3 Fase G2 — Renderers & Templates

**Scope**: Generate vault structure + rules.

### G2.1 TypeScript Renderer

**File**: `generator/renderers/vault-renderer.ts`

```typescript
export function renderVault(profile: BuiltProfile): FileWrite[] {
  if (!profile.answers["integrations.knowledge_plane.enabled"]) {
    return []; // No vault
  }

  const schemaType = profile.answers["integrations.knowledge_plane.schema_type"] || "minimal";
  
  return [
    {
      path: "vault/schema.md",
      content: render("vault/schema.md.hbs", { 
        schemaType, 
        projectName: profile.identity.name 
      })
    },
    { path: "vault/raw/.gitkeep", content: "" },
    { path: "vault/wiki/.gitkeep", content: "" },
    {
      path: "vault/wiki/MEMORY.md",
      content: render("vault/wiki/MEMORY.md.hbs", { 
        schemaType,
        date: new Date().toISOString().split('T')[0]
      })
    },
    {
      path: ".claude/rules/memory.md",
      content: render(".claude/rules/memory.md.hbs", { 
        schemaType,
        projectType: profile.domain.type  // agent-sdk | library | cli | web
      })
    }
  ];
}
```

**Compose in allRenderers** (index.ts):
```typescript
export const allRenderers = [
  ...coreDocRenderers,
  ...policyAndRulesRenderers,
  ...testHarnessRenderers,
  ...vaultRenderers,  // ← ADD THIS
];
```

### G2.2 Templates

**File**: `templates/vault/schema.md.hbs`

```handlebars
---
name: Memory Configuration
description: Esquema y convenciones del vault de {{projectName}}
type: reference
---

# Vault Configuration — {{projectName}}

> Segundo cerebro acumulativo. Sigue el three-stores model: raw/ (inmutable) + wiki/ (síntesis) + schema.md (este).

## Tipos de memoria soportados

{{#if (eq schemaType "team-docs")}}
- **user**: Perfil, preferencias, responsabilidades, contexto
- **feedback**: Correcciones de enfoque, validaciones, aprobaciones
- **project**: Estado vivo, roadmap, decisiones, stakeholders
- **reference**: Enlaces a recursos externos (papers, tools, specs)
- **pattern**: Decisiones arquitectónicas reutilizables
{{else if (eq schemaType "architecture")}}
- **user**, **feedback**, **project**, **reference**
- **pattern**: Patrones de código, decisiones arquitectónicas
{{else if (eq schemaType "research")}}
- **user**, **feedback**, **project**, **reference**
{{else}}
- **user**: Perfil, preferencias
- **feedback**: Correcciones de enfoque
- **project**: Estado del proyecto
{{/if}}

## Convenciones de naming

- Atoms: `<topic>_<type>.md` (snake_case)
- Queries: `<topic>_<question>.md` (kebab-slug)
- Frontmatter required: `name`, `description`, `type`, `confidence`
```

**File**: `templates/vault/wiki/MEMORY.md.hbs`

```handlebars
# MEMORY.md — Knowledge Index

> Master catalog of atoms and references. Updated with each ingest/query.
> Last updated: {{date}}

## How to use this vault

1. Read `../schema.md` for conventions first.
2. For ingestion: place raw source in `../raw/`, extract atoms to `wiki/`.
3. For queries: start here, then browse MOC/ or atom links.

## Current inventory

(Will be auto-populated. Format: `- [[wiki/<topic>_<type>]] — one-line summary`)

### By Type

- **User**: (atoms defining team/project knowledge)
- **Feedback**: (validated learnings)
- **Project**: (state, decisions, roadmap)
- **Reference**: (external links)
{{#if (includes schemaType "architecture" "team-docs")}}
- **Pattern**: (reusable decisions)
{{/if}}

## Next steps

1. Create first atom: `wiki/example_feedback.md`
2. Link it here in the appropriate section
3. Ingest 3-5 sources to build initial corpus
```

**File**: `templates/.claude/rules/memory.md.hbs`

```handlebars
# Memory Plane — {{schemaType}} Schema Rules

This vault uses the three-stores model: raw/ (immutable) + wiki/ (synthesis) + schema.md (config).

## Quick query workflow

1. Open `vault/wiki/MEMORY.md` (start here)
2. Find relevant atom by topic
3. Read atom + citations
4. Cite with `[[wiki/atom-slug]]`
5. Save novel query as new atom if useful
6. Update MEMORY.md index

## Atom schema

```yaml
---
name: Brief title (one phrase)
description: One-sentence summary
type: user | feedback | project | reference{{#if (includes schemaType "architecture" "team-docs")}} | pattern{{/if}}
confidence: high | medium | low
sources:
  - reference or quote
---
```

## Hard rules

- ❌ One claim per atom (partition if >1 independent claim)
- ❌ Cite every fact with a `[[source]]`
- ❌ Never invent content; say "insufficient evidence" if needed
- ❌ Modify `raw/` (immutable except initial creation)
- ✅ Extend atoms with new sources instead of duplicating
- ✅ Cross-reference related atoms via `[[wiki/...]]`

## Example atoms

{{#if (eq schemaType "team-docs")}}
- `team_feedback.md` — bias in hiring (collective validation)
- `pipeline_project.md` — Q3 migration timeline
- `aws_pattern.md` — DynamoDB key design for scale
{{else if (eq schemaType "architecture")}}
- `api_pattern.md` — REST versioning strategy
- `testing_feedback.md` — mocks vs integration testing
{{else if (eq schemaType "research")}}
- `benchmarks_reference.md` — curated links to benchmarks
- `metric_project.md` — our KPIs
{{else}}
- `role_user.md` — PM responsibilities in this org
- `scope_feedback.md` — "don't add features, fix bugs"
{{/if}}
```

**Estimate**: 8k tokens | 2-3 sessions | Snapshots are bulk (3 profiles × 4 schema_types = 12 snapshots)

---

## I.4 Fase G3 — Hooks

**Scope**: Post-generation instructions & automation.

**File**: `hooks/vault-init.py`

```python
#!/usr/bin/env python3
# Runs after: generator/run.ts --write

import sys
import os
import json

def main():
    if not os.getenv('POS_PROFILE_ENABLED_MEMORY'):
        return 0  # Skip if memory not enabled
    
    schema_type = os.getenv('POS_PROFILE_SCHEMA_TYPE', 'minimal')
    
    print("[memory] ✅ Vault initialized at vault/")
    print(f"[memory] Schema type: {schema_type}")
    print("[memory] Next: read vault/schema.md for conventions")
    print("[memory] Then: start ingest cycle (raw/ → wiki/ → MEMORY.md)")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

**Estimate**: 1k tokens | <1 session | Minimal hook

---

## I.5 Fase G4 — Skills (Deferred)

**Scope**: Automated raw → wiki pipeline for heavy users.

**Deferred reason**: Iterate with real users first. If demand appears, implement `/pos:memory-add` skill with context: fork to avoid contaminating main session.

**Estimate**: ~5k tokens | 1-2 sessions | Deferred to demand

---

## I.6 Documentation Updates

### MASTER_PLAN.md
Add Fase G section with full breakdown:

```markdown
## Fase G — Knowledge Plane (Memory Vaults)

### Rama G1 — `feat/g1-questionnaire-memory-plane`
**Scope**: Questionnaire field addition
**Timeline**: 2k tokens, 1 session
**Tests**: snapshot test for schema.yaml

### Rama G2 — `feat/g2-vault-renderer`
**Scope**: Renderers + templates + integration
**Timeline**: 8k tokens, 2-3 sessions
**Tests**: 12 snapshots (3 profiles × 4 schema_types)

### Rama G3 — `feat/g3-hooks-vault-init`
**Scope**: Post-gen hook, instructions
**Timeline**: 1k tokens, <1 session
**Tests**: integration test verifies vault/ structure

### Rama G4 — `feat/g4-skill-memory-add` (Deferred)
**Scope**: Ingest automation
**Timeline**: 5k tokens, 1-2 sessions
**Deferred**: Until user demand
```

### docs/ARCHITECTURE.md
Expand **1.1. Knowledge plane (optional)**:
- Three-stores model explanation + examples
- schema_type conditional templates + rationale
- Workflow: how a user maintains vault over time
- Linking strategy (cross-refs, backlinking)

### .claude/rules/generator.md
Add:
```markdown
## Memory Plane (Fase G)

If `integrations.knowledge_plane.enabled = true`:
- Emits `vault/` structure in G2
- Includes `.claude/rules/memory.md` (path-scoped)
- Post-gen hook emits setup instructions (G3)

See docs/ARCHITECTURE.md § 1.1 for details.
```

---

## I.7 Design Decisions & Trade-offs

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Opt-in vs Always-on | **Opt-in (default: false)** | Not all projects need knowledge plane. Small CLIs don't benefit. |
| 4 schema_types | **Yes (minimal/research/architecture/team-docs)** | Different contexts need different atom types. CLI ≠ agent SDK. |
| Backlinks auto-gen | **Deferred to G4** | Complex logic (similar to OMA's build-meta.sh). Iterate with users. |
| Vault persistence | **Persists even if disabled** | Max data safety. Re-enabling doesn't lose history. |
| Path-scoped rules | **Yes (.claude/rules/memory.md)** | Consistent with existing pattern (generator.md, templates.md, etc.). |

---

## I.8 Integration Timeline

| Item | Tokens | Sessions | Blocker | Notes |
|------|--------|----------|---------|-------|
| G1: Questionnaire | 2k | 1 | None | Simple schema addition |
| G2: Renderers | 8k | 2-3 | G1 | Snapshots are bulk |
| G3: Hooks | 1k | <1 | G2 | Minimal script |
| G4: Skills | 5k | 1-2 | None | Deferred to demand |
| Docs updates | 3k | 1 | G3 | Update MASTER_PLAN, ARCHITECTURE, rules |
| **Total Fase G** | **~19k** | **~5-6** | — | Equivalent to 2 medium branches |

---

---

# PART II: OMA Vault Optimizations (20 Items)

## Overview

After 14 batches (100% corpus atomization = 173 videos, 248 atoms), the vault is **corpus-mature** (60%+ saturation). The next phase is optimization: token efficiency, query quality, automation.

**Application strategy**: Items prioritized by ROI (token savings × frequency). Staged in 3 tiers.

---

## 🔴 CRITICAL BLOCKER

### Item #4: Compact index.md

**Current state**: 344 lines ≈ 3956 tokens. Consumes 99% of Regime A ceiling (4k).

**Impact**: Query budget is artificially compressed. Workaround: ceilings raised to 8k/10k/13k (2026-04-24), costing +4k tokens **per query**.

**Solution**: Reduce to ≤150 lines ≈ 1.7k tokens.

**Options**:
1. Factorize into sub-MOCs by primary topic (pricing, listing-optimization, ranking)
2. Move detail to `meta/query-index.md` (cached query catalog)
3. Use category headers instead of full atom listing

**Target**: Complete before next optimization push. ROI: recover ~2.3k tokens/query × sustained query volume = high.

**Status**: Blocked on prioritization decision. Not started.

---

## Tier 1: High-ROI, Short-term (Batches 15-16)

### Item #1: Pre-cache 10-15 queries
**Scope**: Generate responses to predictable host questions
**Candidates**: pricing-season, reviews-recovery, hospitality-flow, investing-deal, ranking-factors, listing-upgrades, cleaning-team, market-selection, direct-booking, tools-stack
**Cost**: ~3k tokens upfront (pre-generation)
**Benefit**: Subsequent similar queries ≈ 0 tokens (cache hit)
**ROI**: Extremely high if these queries are frequently asked
**Status**: Pending user request

### Item #2: Response Contract refinement
**Scope**: Formalize output style for tonal consistency
**Currently in CLAUDE.md**: §10.7 (experimental)
**Test**: 5 tactical + 3 strategic queries, measure token reduction + fidelity
**Objective**: -40-50% output tokens while maintaining coverage
**Metrics**: score 1-10 vs tokens, adjust limits (max words, anglicisms)
**Status**: Active testing mode

### Item #3: Budget escalation by topic-count
**Scope**: Queries touching N topics get N-dependent atom budget
**Current**: flat "5 atoms" regardless of topic count
**Proposal**: single-topic: 5 | 2-topic: 7 | 3-topic: 9 | 4+: 12 (hard cap)
**Alternative**: formulaic `budget = 3 × topic_count + 1` (capped 12)
**Testing**: A/B over cached query set, measure score vs tokens
**Status**: Formula proposed, awaiting calibration

---

## Tier 2: Medium-ROI, Automation (Batches 17-19)

### Item #5: Mandatory lint hook post-batch
**Scope**: Automate §4.3 (LINT operation)
**Trigger**: Post `.claude/scripts/batch-ingest.sh`, run lint sweep automatically
**Coverage**: broken wikilinks, orphans, stale atoms, topic validation
**Cost**: ~0 tokens (shell-based, not LLM)
**Status**: Scripted but not integrated as hook yet

### Item #6: Query index (`meta/query-index.md`)
**Scope**: Table of cached queries + topics + last-validated date
**Use**: Accelerates §4.2 step 2 (find cached query faster)
**Format**: table with columns (query_slug | topics | answered_on | confidence)
**Maintenance**: Auto-update via `scripts/build-meta.sh`
**Status**: Design complete, awaiting implementation

### Item #7: Declare corpus mature
**Trigger**: Next batch with <5 atoms/10 sources (saturation ≥80%)
**Action**: Announce "corpus closed to new atoms; ingest new videos only for extension"
**Implication**: Shift from growth → maintenance mode
**Status**: Monitoring batch saturation; predict batch 9-10

### Item #8: Backlinks in sources/
**Scope**: Auto-append list of atoms citing each source
**Format**: `<!-- BACKLINKS:START --> ... <!-- BACKLINKS:END -->` marker sections
**Benefit**: LLM sees "X cites me" without extra reads; Obsidian grafo connectivity
**Cost**: ~5k lines total | Regen cost ≈ 0 (script-based)
**Trade-off**: +50-200 tokens/read if backlinks are long; benefit if prevents extra Reads
**Status**: Detailed spec complete (opt #8 in optimizations_pending.md), awaiting implementation

### Item #9: Convergence-loop lint
**Scope**: Automated lint with "done when all criteria met"
**Criteria**: (a) <3 findings per run × 2 consecutive, AND (b) avg wikilinks ≥2/atom AND atoms<2-links <5%
**Current state**: avg ✅ 2.28 | <2-links ❌ 37.8% (way off)
**Effort**: Densify ~51 atoms = ~20-40k tokens one-shot
**Status**: Criteria defined; convergence not yet met

---

## Tier 3: Structural Improvements (Batches 20+)

### Item #10: Response Contract section in docs
**Status**: Partially live in CLAUDE.md §10.7 (experimental)
**Pending**: Validation via 5+ queries, then crystallize as canonical rule
**Outcome**: If validates, make this definitive; if not, iterate

### Item #11: Budget by topic-count (calibration)
**See Tier 1 Item #3**

### Item #12: Gap-detector lint
**Scope**: Find concepts in sources/ missing from atoms
**Trigger**: Term appears in ≥5 sources but 0 atoms
**Output**: Candidate atoms to create (e.g., "max price" in 12 sources → create atom)
**Implementation**: `scripts/lint-gaps.py` with stopword filter + whitelist
**Status**: Spec complete, awaiting implementation

### Item #13: Asymmetric ref lint
**Scope**: Detect atom A cites concept B, but B doesn't cite A
**Fix**: Add "Ver también: [[notes/A]]" in B's footer
**Motivation**: Real bug from query-test: adjacency-factor ↔ orphan-night confusion
**Implementation**: `scripts/lint-asym-refs.py`
**Status**: Spec complete; overlaps with item #16 (bidirectional links)

### Item #14: Dual-representation schema (`claim` + `client_line`)
**Scope**: Two fields in atom frontmatter
- `claim`: Technical, internal
- `client_line`: Terse, copy-paste ready for host
**Example**: 
```yaml
claim: PriceLabs >5 customizations interact unpredictably; >5 = unstable pricing.
client_line: "Max 5 customizations in PriceLabs; more interfere."
```
**Benefit**: -20% output tokens via Response Contract
**Cost**: ~90 min migration (174 atoms × 30s each), paralelizable per topic
**Status**: Spec complete; awaiting prioritization

### Item #15: Wiki+RAG hybrid fallback
**Scope**: If atoms insufficient, supplement with RAG over sources/
**Trigger**: §4.2 step 4 returns <N atoms (N tbd, first guess: 3)
**Flow**: Respond with X atoms + RAG chunks; flag if RAG found something new
**Post-response**: Auto-ingest suggested new atom (closes gaps automatically)
**Infrastructure**: Local embeddings (sentence-transformers) + vector store (qdrant/chroma)
**Cost infra**: Negligible (all open-source, ~100MB storage)
**Status**: Architecture designed, awaiting implementation demand

### Item #16: Bidirectional links in atoms
**Scope**: Auto-append "Citado por" section in each atom
**Similar to item #8** (backlinks in sources/), but for notes/
**Benefit**: LLM sees full graph directionality without jumping
**Trade-off**: Clutter (footers on heavily-cited atoms) vs prevention of fusion errors (like orphan-night bug)
**Verdict**: Yes, implement with discipline (markers, max 10 backlinks shown, rest in meta/)
**Status**: Detailed pros/cons documented, awaiting implementation

### Item #17: Lint pre-commit: forbid `.md` in wikilinks
**Scope**: Catch `[[notes/X.md]]` → error (should be `[[notes/X]]`)
**Trigger**: Recurring bug appeared 2× in batch 13
**Implementation**: One-liner rg command as pre-commit hook
**Time**: ~3 min to implement
**ROI**: Zero false-negatives for pure syntax bugs
**Status**: Ready to implement immediately

### Item #18: YAML-strict quoting sweep
**Scope**: Quote atoms with `**bold**` or `: ` in claim field
**Current**: 75% of atoms (181/242) fail strict YAML parsing
**Impact**: Scripts using PyYAML strict fail silently or require ad-hoc tolerant parser
**Fix**: One-shot script wrapping claim values when needed
**ROI**: Allows strict scripts; prevents latent bugs
**Status**: Script design complete, awaiting execution

### Item #19: Phantom topics prevention
**Scope**: Pre-commit validates `topics:` field against canonical list (§10.3)
**Current**: 13 atoms with off-list topics (already fixed 2026-04-24)
**Prevention**: Whitelist check one-liner
**Status**: Preventive; implement post-fix to avoid regression

### Item #20: Secondary-topic MOC back-referencing
**Scope**: Atoms with `topics: [A, B]` appear in MOC/A AND MOC/B
**Current**: ~180 atoms missing secondary references
**Impact**: Queries opening MOC/B miss atoms it covers (high retrieval cost)
**Options**: (a) Auto back-ref all 180 (one-shot, high-effort), or (b) Expensive runtime grep
**Recommendation**: Do (a) once with script; ROI high for cross-topic queries
**Status**: Awaiting decision; script skeleton ready

---

## Optimization Roadmap

### **Phase α** (immediate, <1 session)
- Item #17: Pre-commit wikilink linter (3 min)
- Item #18: YAML quoting sweep (automated, ~20 min)

### **Phase β** (active testing, ongoing)
- Item #2: Response Contract validation (5-8 queries)
- Item #3: Budget calibration A/B testing

### **Phase γ** (after corpus stabilizes, batches 17-19)
- Item #1: Pre-cache 10-15 queries (~3k tokens upfront)
- Item #4: Compact index.md (high-priority blocker)
- Item #5: Lint hook integration
- Item #6: Query index implementation
- Item #8: Backlinks in sources/
- Item #12-14: Gap detection + schema dual-representation

### **Phase δ** (conditional, demand-driven)
- Item #7: Corpus mature declaration
- Item #9: Convergence loop densification (~20-40k tokens)
- Item #15: RAG hybrid fallback
- Item #16: Bidirectional links in atoms
- Item #19-20: Topic validation + secondary MOC backref

---

## Critical Dependencies

| Item | Depends on | Blocks |
|------|-----------|--------|
| #4 (compact index) | None | Query budget ceilings; others' token measurements |
| #5 (lint hook) | None | Reproducible health checks |
| #8 (backlinks sources) | None | #16 (atoms backlinks) |
| #10 (Response Contract) | #2 validation | Output consistency |
| #14 (client_line) | None | #10 crystallization |
| #15 (RAG hybrid) | None | Long-tail query resolution |
| #16 (atoms backlinks) | None | Prevents fusion errors |
| #20 (secondary MOCs) | None | Cross-topic retrieval cost |

---

## Token Impact Summary

| Phase | Item | Upfront | Per-query impact | Total benefit |
|-------|------|---------|-----------------|----------------|
| α | #17-18 | ~1k | ~50 tokens (parser robustness) | High |
| β | #2-3 | 0 | -300-400 (Response Contract validation) | High if validates |
| γ | #1 | 3k | -3.9k (cache hits) | Very high |
| γ | #4 | 1k labor | -2.3k (deficit recovery) | Critical |
| γ | #8 | 1k labor | 0-200 (backlinks overhead vs prevented reads) | Medium |
| δ | #15 | 2k infra | +1-2k (RAG chunks if needed) | Neutral to positive (covers gaps) |
| δ | #16 | 1k labor | +100-200 (backlinks overhead) | Medium (prevents fusion errors) |

**Net impact target**: -4-6k tokens/query sustained (vs current 7-10k with blocker #4).

---

---

# CONSOLIDATED ROADMAP

## Phase Timeline

### **Now (Session N)**
- ✅ Complete CLAUDE.md improvements (Quick Start, Prerequisites, Troubleshooting)
- ✅ Approve pos Fase G design
- ✅ Approve OMA optimization priorities

### **Week 1-2 (Upon user request)**
- Implement Phase α (wikilink lint, YAML quoting)
- Begin Phase β testing (Response Contract, budget calibration)

### **Week 3-4**
- Complete Phase β validation
- Begin Phase γ execution (pending corpus saturation signal)

### **Month 2+**
- Phase γ full implementation (index compact, lint hook, backlinks)
- Phase δ conditional items as demand/capacity allows

---

## Discussion Points for User

Before implementation, clarify:

1. **pos Fase G**: Should we start with G1-G3, defer G4 until demand? Acceptable?

2. **OMA Phase α**: Implement wikilink + YAML quoting linters immediately? (Low-risk, ~1k tokens)

3. **OMA Item #4**: Accept temporary ceiling inflation (8k/10k/13k) while compacting index.md? Or prioritize compact-first?

4. **OMA Dual-representation (#14)**: Worth 90 min migration if validates token savings? Or defer?

5. **RAG hybrid (#15)**: Demand-driven, or proactive implementation when battery allows?

6. **Corpus mature (#7)**: What's the saturation threshold before switching to maintenance mode? (Currently 80%+ predicted batch 9-10)

---

## Success Metrics

**pos Integration**:
- [ ] G1-G3 complete and merged
- [ ] 3 projects generated with memory plane enabled
- [ ] No edge cases found in snapshots

**OMA Optimizations**:
- [ ] Index.md ≤150 lines (recover 2.3k tokens/query)
- [ ] Response Contract validated (token reduction ≥25%)
- [ ] Lint automation 100% pass rate (zero manual work post-batch)
- [ ] Sustained query cost <6.5k tokens (vs current 7-10k with blocker)

---

**END OF MASTER_PLAN**
