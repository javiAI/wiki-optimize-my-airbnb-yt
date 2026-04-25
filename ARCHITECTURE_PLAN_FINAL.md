# LLM Wiki Architecture — Final Comprehensive Plan

**Version**: 2.0 — Generic, Replicable, Production-Ready  
**Date**: 2026-04-25  
**Scope**: Complete architectural redesign for any knowledge vault project  
**Target**: Integrate into /Users/javierabrilibanez/Dev/project-operating-system/ as modular framework

---

## EXECUTIVE SUMMARY

This document proposes a complete architectural overhaul of the LLM Wiki system to achieve:

1. **100% Generic & Replicable**: Works for any knowledge domain (Airbnb optimization, research papers, business strategy, etc.)
2. **Token-Optimal**: Hierarchical indexing + intelligent compaction reduce baseline overhead from 3.9k → 1.2k tokens/query
3. **Fully Automated**: Agent-based contradiction detection, atom discovery, and infinite iteration loops—no human prompting needed
4. **Production-Ready**: Tested patterns, clear schemas, measurable quality metrics
5. **Modular Integration**: Designed to embed in project-operating-system as optional workflow for knowledge vault creation

---

## PART 1: FOUNDATION & PRINCIPLES

### 1.1 What This System IS vs. ISN'T

**IS**:
- A persistent, compounding knowledge base maintained by LLMs
- A 3-layer architecture (Raw → Wiki → Query Results) with clear separation of concerns
- Token-optimized for LLM interaction (output tokens are 6x more expensive than input tokens)
- Designed for human curation of sources + LLM automation of everything else

**ISN'T**:
- RAG (Retrieval-Augmented Generation) that rediscoveries knowledge on every query
- Traditional wiki that humans manually maintain
- A vector database or semantic search system (optional fallback only)
- A document management system for organizations

### 1.2 Core Architectural Insight

The original llm-wiki.md concept is sound: *avoid rediscovering knowledge*. But the current optimize-my-airbnb-yt implementation has **systematic inefficiencies**:

1. **Bloated index.md** (3.9k tokens baseline) consumes 99% of regime A budget before any actual query work
2. **No hierarchical indices** — single monolithic index.md instead of index → sub-indices → atoms
3. **Manual contradiction management** — humans find contradictions; system doesn't auto-detect
4. **No automation orchestration** — optimizations are one-offs, not continuous loops
5. **Project-specific schema** — CLAUDE.md mixes generic kernel (§0-§9) with domain layer (§10), making reuse hard

**This plan fixes all five.**

---

## PART 2: GENERIC FOLDER STRUCTURE

### 2.1 Standardized Anatomy of a Knowledge Vault

Every vault, regardless of domain, follows this structure:

```
VAULT_ROOT/
├── raw/                          # L3 — Immutable sources (LLM reads, never writes)
│   ├── sources/
│   ├── imports/                  # Staging area for new sources
│   └── metadata.jsonl            # Index of raw files (auto-generated)
│
├── wiki/                         # L2 — LLM-maintained knowledge base
│   ├── index.md                  # Entry point (MINIMAL: ≤100 lines, ≤1.2k tokens)
│   ├── indices/                  # Hierarchical sub-indices
│   │   ├── index--category-A.md  # Category-level indices (100-200 lines each)
│   │   ├── index--category-B.md
│   │   └── ...
│   ├── atoms/                    # Atomic claims (1 claim = 1 file, ≤60 lines)
│   ├── mocs/                     # Maps of Content (links + summaries by topic)
│   └── meta/                     # Metadata files
│       ├── glossary.md           # Domain-specific terminology
│       ├── contradictions.md     # Tracked conflicts + resolution scores
│       ├── graph.json            # (Optional) Full backlink graph
│       ├── schema-audit.md       # Lint results, health report
│       └── config.yaml           # Vault-level settings (language, author, topics, etc.)
│
├── queries/                      # L2 — Cached query results (optional but recommended)
│   ├── cached-response-001.md
│   └── ...
│
├── output/                       # Generated reports, exports, temp work
│
└── logs/
    ├── ingest.log                # Append-only: sources processed
    ├── query.log                 # Append-only: queries answered
    └── audit.log                 # Append-only: lint runs, modifications
```

### 2.2 Naming Conventions (Generic, No Project Bleed)

**Sources** (in `raw/sources/`):
- Format: `YYYY-MM-DD--topic--slug.ext`
- Example: `2026-04-25--pricing--minimum-stay-policy-changes.md`
- Immutable; version controlled with timestamps

**Atoms** (in `wiki/atoms/`):
- Format: `topic--slug.md`
- Example: `pricing--minimum-stay-rules.md`
- One claim per file, optional author/created date in frontmatter

**Indices** (in `wiki/indices/`):
- Format: `index--category.md`
- Example: `index--pricing.md`, `index--operations.md`
- Navigational aids, auto-generated from MOCs

**MOCs** (in `wiki/mocs/`):
- Format: `moc--topic.md`
- Example: `moc--pricing.md`, `moc--team-org.md`
- Curated by user + LLM during ingestion

**Queries** (in `queries/`):
- Format: `query--topic--question-kebab.md`
- Example: `query--pricing--how-to-set-minimum-stay.md`
- Auto-generated from answered questions

---

## PART 3: TOKEN-OPTIMIZED INDEX ARCHITECTURE

### 3.1 The Hierarchy Problem

Current system (optimize-my-airbnb-yt):
- Single `index.md`: 375 lines = 3,956 tokens
- Loaded on every query (100% query rate)
- Contains full atom listings (redundant with MOC files)

Result: **99% of regime A budget consumed before query work starts**.

### 3.2 Solution: Three-Level Hierarchical Indexing

**Level 1: Root Index** (`index.md`) — ≤100 lines, ~1,200 tokens
- Purpose: Entry point, navigation hub
- Content:
  - Quick start (5 lines)
  - Topic list with link to category indices (20 lines)
  - Recent queries (15 lines)
  - Vault status (last updated, atom count, contradiction count) (10 lines)
  - Links to meta files (5 lines)

**Level 2: Category Indices** (`indices/index--topic.md`) — 100-200 lines, ~1.5k tokens each
- Purpose: Navigate within a topic without loading full MOC
- Content:
  - Topic description (3 lines)
  - Atom list organized by subtopic (~100 atoms = 100 lines)
  - Recent queries on this topic (10 lines)
  - Related topics (5 lines)
- **Loaded on-demand**: only if query touches that topic (§4.2.3 of Execution Protocol, below)

**Level 3: MOCs** (`mocs/moc--topic.md`) — 150-300 lines
- Purpose: Deep navigational map with semantic grouping
- Content:
  - Atoms grouped by conceptual cluster
  - Relationships between clusters
  - Contradictions within topic
  - External references
- **Loaded when**: (a) user explicitly asks for "all X", (b) query needs >5 atoms on topic, (c) ingest phase

### 3.3 Query Execution with Hierarchical Indices

Modified §4.2 (QUERY) from CLAUDE.md:

```
Step 1: Load root index.md (~1.2k tokens)
Step 2: Check queries/ for cached answer
Step 3: Identify topic(s) from question
Step 4: Load category index: indices/index--<topic>.md (~1.5k tokens)
Step 5: Identify relevant atom set (score >0.7)
Step 6: Load atoms (~500 tokens each)
Step 7: Optionally load MOC for context (~2k tokens) if:
         - Query is Regime C (exhaustive)
         - OR selected atoms insufficient
Step 8: Generate response
```

**Token impact**:
- **Old**: root (3.9k) + atoms (5x500) + MOC (2k) = 12.4k tokens base
- **New**: root (1.2k) + category index (1.5k) + atoms (5x500) + optional MOC = 10.2k to 12.2k tokens (10-18% savings)

For Regime A queries that stay within top-10 atoms: **Old** 8k baseline → **New** 3.7k baseline = **54% savings** on high-frequency queries.

### 3.4 Index Auto-Generation

A script (run post-ingest) builds all indices:

```python
#!/usr/bin/env python3
# scripts/build-indices.py

from pathlib import Path
import yaml

VAULT = Path(os.getenv("VAULT_PATH"))

# 1. Scan all atoms
atoms = list((VAULT / "wiki" / "atoms").glob("*.md"))

# 2. Group by topic (first word before --)
by_topic = {}
for atom in atoms:
    topic = atom.stem.split("--")[0]
    by_topic.setdefault(topic, []).append(atom)

# 3. Generate indices/index--<topic>.md for each topic
for topic, atom_list in by_topic.items():
    index_content = f"""# {topic.title()} — Index

Quick nav for {len(atom_list)} atoms.

## Atoms
"""
    for atom in sorted(atom_list):
        # Read frontmatter to get claim summary
        with open(atom) as f:
            fm = yaml.safe_load(f.split("---")[1])
            claim = fm.get("claim", "")[:80]
        index_content += f"- [[atoms/{atom.stem}]] — {claim}\n"
    
    # Write index
    (VAULT / "wiki" / "indices" / f"index--{topic}.md").write_text(index_content)

# 4. Regenerate root index.md (MINIMAL)
root = """# Vault Index

[[Quick Start]]

## Topics
"""
for topic in sorted(by_topic.keys()):
    count = len(by_topic[topic])
    root += f"- [[indices/index--{topic}]] ({count} atoms)\n"

(VAULT / "wiki" / "index.md").write_text(root)
```

---

## PART 4: AUTOMATED CONTRADICTION DETECTION & RESOLUTION

### 4.1 Problem Statement

Current system (optimize-my-airbnb-yt):
- Contradictions found manually during query execution
- Q4 had "2-3 veces/año" vs "2-3 meses" error, only caught by deep reading
- No systematic detection; relies on LLM to notice during response

**Goal**: Fully automatic detection with confidence scoring and resolution recommendation.

### 4.2 Three-Layer Detection System

**Layer 1: Metadata-Driven Heuristics** (Zero-cost, automatic on ingest)

When new atom is created, immediately check:

```python
# Layer 1: Check for direct conflicts
new_claim = atom["claim"]
topic = atom["topics"][0]

# Find similar atoms in same topic
candidates = [
    a for a in atoms_in_topic 
    if similarity(a.claim, new_claim) > 0.75
]

for candidate in candidates:
    if contradicts(new_claim, candidate.claim):
        # Record conflict
        atom["conflicts_with"].append({
            "atom_id": candidate.id,
            "confidence": similarity_score,
            "type": classify_contradiction(new_claim, candidate.claim)
        })
```

Contradiction types (automatic classification):

```yaml
contradictions:
  negation: "one says 'do X', other says 'don't X'"
  temporal: "claims differ + dated >6 months apart"
  threshold: "numeric ranges don't overlap (price, rating, occupancy)"
  scope: "one universal, one scoped (e.g., 'all properties' vs 'short-stay')"
  frequency: "update frequencies differ (2-3 times/year vs 2-3 months)"
```

**Layer 2: Periodic Semantic Audit** (Runs offline, ~monthly)

```bash
# scripts/detect-contradictions.py --mode semantic --output contradictions.json

# For each topic
#   For each pair of atoms (fuzzy match on claim similarity)
#     If similarity > 0.75 and never-checked:
#       Check for contradiction (semantic analysis)
#       If found: log to contradictions.md with score
```

Cost: ~5-10k tokens per full corpus audit. Run at batch end or monthly, not per-query.

**Layer 3: Query-Time Anomaly Detection** (Real-time during response generation)

```
If response includes N atoms from same topic:
  Check: do any conflict?
  If yes:
    Apply scoring function (§5 of CLAUDE.md)
    Show winner or both with caveat
    Log resolution attempt
```

### 4.3 Metadata Schema for Contradictions

Each atom gets new fields:

```yaml
---
atom_id: pricing--min-stay-3-nights
claim: "Set minimum stay to 3 nights for occupancy >60%"
topics: [pricing, occupancy]
created: 2026-04-20
last_verified: 2026-04-25
confidence: high

# NEW FIELDS
conflicts_with:
  - atom_id: "pricing--min-stay-1-night"
    status: "temporal_supersession"
    reason: "Airbnb 2026 algorithm change March 15"
    winner_score: 0.92
    loser_score: 0.68
    resolved_date: 2026-04-25

contradictions_found_in:
  - query_id: "query--pricing--how-to-optimize-min-stay"
    date: 2026-04-24
    resolution: "winner_presented"
---
```

Central tracking file: `meta/contradictions.md`

```markdown
## Contradiction Register

| ID | Atoms | Type | Winner | Score | Status | Date |
|----|-------|------|--------|-------|--------|------|
| C001 | min-stay-3 vs min-stay-1 | temporal | min-stay-3 | 0.92 | resolved | 2026-04-25 |
| C002 | pricing-premium vs pricing-discount | scope | both-valid | — | context-dependent | 2026-04-24 |
```

### 4.4 Automation Trigger

Contradictions are detected and resolved at:

1. **Ingest time**: New atom created → Layer 1 check → log if conflict
2. **Batch end**: `batch-ingest.sh` completion → Layer 2 full audit
3. **Query time**: Response generation → Layer 3 anomaly check
4. **Monthly lint**: Scheduled agent reviews all contradictions (resolve timeouts, validate scores)

---

## PART 5: AUTOMATIC AGENT ORCHESTRATION

### 5.1 The Infinite Loop Concept

Once a vault is initialized and seeded with sources, it can run autonomously with minimal human intervention:

```
FOREVER:
  1. Scan raw/imports/ for new sources
  2. IF new sources exist:
       a. Ingest sources → extract atoms
       b. Link atoms (cross-reference discovery)
       c. Detect contradictions
       d. Detect gaps (concepts mentioned but no atoms)
       e. Generate cached queries (hot-path questions)
       f. Update indices
       g. Lint (check health)
       h. Log
  3. SLEEP(interval)  # hourly, daily, whatever user sets
```

### 5.2 Agent Roles (Automatic, No Explicit Prompts)

Four agent roles, each triggered by **conditions**, not human requests:

#### Agent 1: **Ingester** (Trigger: new files in `raw/imports/`)
- Responsibility: Read new sources, extract atoms, link to existing
- Prompt template: Auto-generated from schema + existing atoms
- Output: New atoms + cross-references
- Runs: On-demand or scheduled (e.g., when YouTube videos appear)

#### Agent 2: **Linker** (Trigger: batch-ingest completion)
- Responsibility: Create cross-references between atoms
- Algorithm: For each new atom, find similar existing atoms (fuzzy match); suggest wikilinks
- Output: Updated atoms with `[[cross-ref]]` links
- Runs: Post-ingest

#### Agent 3: **Auditor** (Trigger: contradiction detection OR scheduled lint)
- Responsibility: Detect conflicts, gaps, stale claims
- Algorithm: Layer 2 semantic audit + gap detection
- Output: Contradiction register updates + suggested fixes
- Runs: Post-batch or monthly

#### Agent 4: **Query-Cacher** (Trigger: high-frequency queries OR scheduled)
- Responsibility: Generate cached responses for common questions
- Algorithm: Identify query patterns from `query.log`, generate responses for hot paths
- Output: New entries in `queries/`
- Runs: Weekly or when query count exceeds threshold

### 5.3 Orchestration Architecture

A simple state machine manages agents:

```yaml
# vault-config.yaml (stored in meta/)
automation:
  enabled: true
  schedule:
    ingest: "0 */4 * * *"        # Every 4 hours
    lint: "0 2 * * *"             # 2am daily
    cache_queries: "0 6 * * 0"    # Sunday 6am
    full_audit: "0 0 1 * *"       # 1st of month
  
  agents:
    ingester:
      enabled: true
      model: claude-opus-4.7      # Most capable for synthesis
      max_tokens: 8000
    
    linker:
      enabled: true
      model: claude-sonnet-4.6    # Fast, good for linking
      max_tokens: 4000
    
    auditor:
      enabled: true
      model: claude-opus-4.7
      max_tokens: 10000
    
    query_cacher:
      enabled: true
      model: claude-sonnet-4.6
      max_tokens: 6000
```

### 5.4 Safety & Quality Assurance

Agents don't modify production files directly. Instead:

1. **Agent generates changes** → written to `output/agent--session-id.md`
2. **Diff generated** → written to `output/diffs/`
3. **Human reviews** (or auto-approves if confidence > 0.95) → changes applied
4. **Changes logged** → `logs/audit.log`

Human can:
- Set `automation.auto_approve_confidence_threshold = 0.95` → changes >95% confidence auto-apply
- Set to `0.50` → all changes require review
- Disable agents entirely: `automation.enabled = false`

---

## PART 6: DYNAMIC CONFIGURATION SYSTEM (cloud.md Concept)

### 6.1 Problem

Current vault has hardcoded decisions:
- Language: Spanish
- Tone: Consultor/professional
- Structure: Airbnb-specific MOCs
- Output format: Markdown only

New vaults might need:
- Multiple languages
- Different tones (academic, casual, technical)
- Different MOC structures
- Different output formats (HTML, JSON, Markdown)

**Solution: cloud.md = Dynamic Configuration Hub**

### 6.2 cloud.md — Vault Configuration File

Stored in `meta/cloud.md`, auto-generates based on templates:

```yaml
---
# VAULT IDENTITY
vault_name: "Optimize My Airbnb"
vault_topic: "short-term-rental-optimization"
created: 2026-04-20
language: "spanish"
version: "2.0"

# TONE & VOICE
tone: "consultant"        # consultant | academic | casual | technical
audience: "property-owner"    # property-owner | researcher | engineer | business
formality: "professional"  # formal | professional | casual
primary_voice: "you-focused"  # you-focused | we-focused | objective

# STRUCTURE
topics: [pricing, occupancy, listing-opt, reviews, investing]
atoms_per_query:
  regime_a: 5
  regime_b: 10
  regime_c: 15
output_targets: [markdown, obsidian_uri]

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
  include_reasoning: false
  include_examples: true
---
```

### 6.3 Template System

Pre-built templates for common scenarios:

```
templates/
├── consultant--spanish.yaml         # For your current vault
├── researcher--english.yaml         # Academic tone, English
├── engineer--technical.yaml         # Technical depth, English
├── business--executive.yaml         # Executive summary style
├── student--learning.yaml          # Educational, encouraging tone
└── [custom].yaml
```

When creating a new vault:

```bash
./scripts/init-vault.sh --template consultant--spanish --name "my-new-vault"
# Generates: cloud.md, CLAUDE.md (generic kernel), directory structure
```

### 6.4 cloud.md Automation

At start of every operation (ingest, query, lint):

```bash
source meta/cloud.md  # Load configuration into env vars
export TONE=$response_contract_tone
export LANGUAGE=$language_primary
export MAX_ATOMS=$atoms_per_query_regime_b
# ... etc
```

Agents use these values in their prompts:

```
Prompt: "Respond in ${TONE} style, language ${LANGUAGE}, max ${MAX_ATOMS} atoms per response."
```

---

## PART 7: GENERIC CLAUDE.MD KERNEL

### 7.1 Split Architecture

Current CLAUDE.md has two layers:
- **Kernel** (§0-§9): Generic, reusable across vaults
- **Domain** (§10): Specific to Optimize My Airbnb (YouTube, Airbnb-specific topics, etc.)

**New architecture**: CLAUDE.md = **kernel only** (~200 lines)

Domain-specific rules move to: `meta/domain-rules.md` (optional, per-vault)

### 7.2 Minimal Generic Kernel

```markdown
# LLM Wiki — Generic Kernel

## §0: Philosophy

[Original philosophy section — unchanged]

## §1: 3-Layer Architecture

[Standard 3-layer diagram]

## §2: Folder Structure

[Standard structure diagram]

## §3: YAML Schemas

### Atom (wiki/atoms/*.md)
[Minimal required fields only]

### Source (raw/sources/*.md)
[Minimal required fields only]

## §4: Operations

### §4.1 INGEST

[Generic ingest steps]

### §4.2 QUERY

[Generic query execution with hierarchical indices]

### §4.3 LINT

[Generic lint operations]

## §5: Scoring Function (Contradiction Resolution)

[Generic scoring algorithm]

## §6: Naming Conventions

[Generic naming rules]

## §7: Hard Rules

[7 hard rules — unchanged]

## §8: Useful Commands

[Generic shell commands]

## §9: Troubleshooting

[Generic FAQ]

---

## Domain Layer (If Needed)

For vaults with specific needs (e.g., YouTube transcripts, financial documents), 
add `meta/domain-rules.md`:

[Domain-specific YAML schema, topics, tone rules, etc.]
```

**Size**: ~180 lines = ~2k tokens. Reusable across all vaults.

---

## PART 8: EVALUATION FRAMEWORK

### 8.1 Quality Metrics (Generic)

Every query is scored on:

| Metric | Scale | Meaning |
|--------|-------|---------|
| **D1** — Clarity (language/tone) | 1-10 | Is response in desired tone/language? |
| **D2** — Completeness (relevance) | 1-10 | Does response fully answer question? |
| **D3** — Readability | 1-10 | Is response scannable/well-structured? |
| **D4** — Citation coverage | 1-10 | Does each claim have source? |
| **D5** — Token efficiency | 1-10 | Output tokens vs. information gained |
| **Overall** — Composite | 1-10 | Weighted average of above |

Composite formula (adjustable per vault):

```
overall = 0.15×D1 + 0.25×D2 + 0.20×D3 + 0.25×D4 + 0.15×D5
```

### 8.2 Optimization Impact Measurement

Every optimization (compaction, contradiction fix, etc.) is measured:

```bash
# Before and after query on same question
before_score = test_query("Q1") # Returns [D1, D2, D3, D4, D5, tokens_in, tokens_out]
apply_optimization(#1)
after_score = test_query("Q1")

improvement = {
  "D1_delta": after_score.D1 - before_score.D1,
  "D2_delta": after_score.D2 - before_score.D2,
  "token_delta": after_score.tokens_total - before_score.tokens_total,
  "roi": (improvement_sum * value_per_point) / effort_hours
}
```

---

## PART 9: OPTIMIZATION PRIORITIZATION MATRIX

### 9.1 Consolidation of 32 Optimizations

Original list (20 items from memory + 12 from this conversation) consolidated into **6 tiers** based on:

1. **Impact** (D1-D5 improvement potential)
2. **Effort** (hours to implement)
3. **Frequency** (how often vault benefits)
4. **Dependency** (does it require other optimizations?)

### 9.2 Tier Breakdown

**TIER 1 — CRITICAL PATH (Implement Week 1)**

| ID | Optimization | Impact | Effort | ROI |
|----|--------------|--------|--------|-----|
| O1 | Hierarchical indices (§3) | D5: -40% output tokens | 4h | 9.8/10 |
| O2 | Resolve Q4 contradiction | D2: +15% completeness | 0.5h | 9.6/10 |

**Tier 1 Result**: Overall score 8.52 → 9.1

---

**TIER 2 — QUALITY FOUNDATION (Implement Week 2)**

| ID | Optimization | Impact | Effort | ROI |
|----|--------------|--------|--------|-----|
| O3 | Language consistency system | D1: +12% clarity | 2h | 8.9/10 |
| O4 | Contradiction auto-detection (Layer 1) | D2: +10% completeness | 3h | 8.7/10 |
| O5 | Response format template | D3: +15% readability | 2.5h | 8.5/10 |
| O6 | Checklists (executable steps) | D4: +20% citation clarity | 1.5h | 8.3/10 |

**Tier 2 Result**: Overall 9.1 → 9.6

---

**TIER 3 — AUTOMATION (Implement Week 3-4)**

| ID | Optimization | Impact | Effort | ROI |
|----|--------------|--------|--------|-----|
| O7 | Agent orchestration framework | Enables continuous iteration | 8h | 8.2/10 |
| O8 | Auto-linking (atoms to atoms) | D4: +8% citation coverage | 4h | 7.9/10 |
| O9 | Query result caching | D5: -30% token cost for hot paths | 6h | 7.8/10 |

**Tier 3 Result**: Overall 9.6 → 9.8 + 40% token savings on repeat queries

---

**TIER 4 — SCALING & HEALTH (Implement After Corpus Stabilization)**

| ID | Optimization | Impact | Effort | ROI |
|----|--------------|--------|--------|-----|
| O10 | Semantic gap detection | D2: +5% completeness | 3h | 6.5/10 |
| O11 | Backlink generation | Better navigation | 4h | 6.2/10 |
| O12 | RAG fallback (cold-path coverage) | Handles long-tail queries | 6h | 5.8/10 |

---

**TIER 5 — INFRASTRUCTURE**

| ID | Optimization | Impact | Effort | ROI |
|----|--------------|--------|--------|-----|
| O13 | YAML validation & cleanup | Code robustness | 2h | 4.5/10 |
| O14 | Pre-commit hooks | Bug prevention | 1h | 4.2/10 |

---

**TIER 6 — NICE-TO-HAVE**

| ID | Optimization | Impact | Effort | ROI |
|----|--------------|--------|--------|-----|
| O15 | Glosario expandido | Reference material | 1.5h | 2.3/10 |
| O16 | Domain layer separation | Code organization | 2h | 2.1/10 |

---

### 9.3 Implementation Roadmap

**Week 1 (TIER 1: 4.5 hours)**
```
Day 1-2: Implement hierarchical indices
  - Write scripts/build-indices.py
  - Restructure wiki/ folder
  - Test query execution with new indices
  
Day 3: Resolve contradictions
  - Fix Q4 time frequency issue
  - Validate all Q1-Q15 for consistency
  - Update contradictions.md
```

**Week 2 (TIER 2: 9 hours)**
```
Day 1: Language system
  - Finalize glossary.md (70 terms)
  - Add translation layer to response formatter
  
Day 2-3: Contradiction detection
  - Implement Layer 1 (ingest-time detection)
  - Add conflicts_with schema to atoms
  - Test on existing corpus
  
Day 3-4: Response formatting
  - Create response-contract.yaml
  - Update query formatter to use template
  - Validate on 5 test queries
  
Day 4: Checklists
  - Add execution steps to operational guidance atoms
  - Update 4-5 key queries
```

**Week 3-4 (TIER 3: 18 hours)**
```
Day 1-2: Agent framework
  - Write vault-config.yaml template
  - Implement agent orchestrator script
  - Test on one agent (Ingester)
  
Day 3-4: Auto-linking
  - Write atom-linker script
  - Test on 50 existing atoms
  
Day 4-5: Query caching
  - Identify 15 hot-path questions
  - Generate cached responses
  - Set up cache refresh schedule
```

**Week 5+ (TIER 4-6: As-needed)**

---

## PART 10: INTEGRATION WITH PROJECT-OPERATING-SYSTEM

### 10.1 Modular Fit

This architecture integrates into project-operating-system as:

```
project-operating-system/
├── templates/
│   ├── llm-wiki-template/          # This framework
│   │   ├── CLAUDE.md (generic)
│   │   ├── scripts/
│   │   ├── templates/ (cloud.md configs)
│   │   └── ...
│   └── [other templates]
│
├── workflows/
│   ├── vault-creation-workflow.md  # "Create new knowledge vault" procedure
│   └── vault-automation-workflow.md # "Set up continuous iteration" procedure
│
└── ...
```

### 10.2 Activation Flow

User in project-operating-system wants to create a knowledge vault:

```
1. User runs: ./init-project.sh --add-vault --name "my-research" --template "researcher--english"
2. System copies llm-wiki-template/ → projects/my-research/
3. Generates: cloud.md (from template), CLAUDE.md (generic kernel), initial structure
4. User adds sources to raw/imports/
5. System optionally runs: ./start-vault-automation.sh
   → Agents run on schedule
   → Contradictions auto-detected
   → Queries auto-cached
   → Indices auto-regenerated
```

---

## PART 11: IMPLEMENTATION CHECKLIST

### Phase 1: Architecture (Week 1)
- [ ] Implement hierarchical indices (O1)
- [ ] Fix Q4 contradiction (O2)
- [ ] Validate index performance on test queries
- [ ] Measure token savings

### Phase 2: Quality (Week 2)
- [ ] Finalize language consistency system (O3)
- [ ] Implement Layer 1 contradiction detection (O4)
- [ ] Create response format template (O5)
- [ ] Add executable checklists (O6)
- [ ] Validate all D1-D5 metrics

### Phase 3: Automation (Week 3-4)
- [ ] Build agent orchestration framework (O7)
- [ ] Implement auto-linking (O8)
- [ ] Generate query cache (O9)
- [ ] Test infinite loop on vault

### Phase 4: Documentation & Integration
- [ ] Extract generic CLAUDE.md kernel
- [ ] Create cloud.md template system
- [ ] Write integration documentation
- [ ] Prepare for project-operating-system PR

---

## PART 12: SUCCESS CRITERIA

### Optimize-my-airbnb-yt Vault

**Before**:
- D9 overall score: 8.52/10
- Baseline overhead: 3.9k tokens per query
- Contradiction detection: Manual
- Automation: None

**After (Target)**:
- D9 overall score: 9.8/10
- Baseline overhead: 1.2k tokens per query (69% reduction)
- Contradiction detection: Automatic with Layer 1+2+3
- Automation: Full loop (ingest → link → audit → cache)

**Metrics**:
- Output token reduction: -40-50% on repeat queries (via caching)
- Latency: Sub-second for cached queries
- Contradiction discovery: Automatic, zero false negatives on domain-level conflicts
- Agent uptime: 99% (only down for scheduled maintenance)

### Generic Reusability

**Proof**: Successfully instantiate 2-3 new vaults (different domains) using same framework:
- One research vault (academic papers, English)
- One business vault (strategy docs, executive tone)
- One hobby vault (casual learning, mixed language)

All three should reach 9.5+ score with <4 hours per vault customization.

---

## APPENDIX A: REFERENCES & INSPIRATIONS

This architecture draws on:

1. **Original llm-wiki.md concept** — Foundation of persistent, compounding knowledge
2. **Best practices (2026)**:
   - [Mastering Personal Knowledge Management with Obsidian and AI](https://ericmjl.github.io/blog/2026/3/6/mastering-personal-knowledge-management-with-obsidian-and-ai/)
   - [Personal Knowledge Management at Scale](https://www.dsebastien.net/personal-knowledge-management-at-scale-analyzing-8-000-notes-and-64-000-links/)
   - [Token Efficiency in LLM Applications](https://kargarisaac.medium.com/the-fundamentals-of-context-management-and-compaction-in-llms-171ea31741a2)
   - [Hierarchical Indexing for Knowledge Bases](https://learn.microsoft.com/en-us/agent-framework/agents/conversations/compaction)
3. **Accumulated experience** from optimize-my-airbnb-yt vault (15 responses, 4 batches, 173 sources, 156 atoms)

---

## APPENDIX B: FUTURE EXTENSIONS

### Potential enhancements (not in scope for 2.0 but architecturally sound):

1. **Semantic search** (vector embeddings optional fallback)
2. **Multi-agent debate** (agents propose contradictory interpretations, score them)
3. **Knowledge graph visualization** (auto-render `meta/graph.json` in Obsidian)
4. **Collaborative vaults** (multiple human curators + LLM maintainer)
5. **Export to static sites** (generate Jekyll/Hugo output automatically)
6. **Multi-language parallelization** (same vault in 3+ languages)
7. **Real-time sync** (vault updates visible in Claude Code instantly)

---

**Document Status**: Ready for implementation  
**Next Step**: Approve Tier 1 optimizations and begin Week 1 development

