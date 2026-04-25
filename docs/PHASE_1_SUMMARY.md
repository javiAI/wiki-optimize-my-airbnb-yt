# Phase 1: Critical Path

**Objective**: Stabilize vault foundation and unlock higher-quality queries.

This phase focuses on the three highest-leverage optimizations that directly improve query accuracy and vault usability without requiring significant automation infrastructure. After Phase 1, the vault will have better index structure, resolved contradictions, and consistent language.

---

## What Phase 1 Accomplishes

- **O1 (Hierarchical Indices)**: Replace flat `index.md` with tiered index system (L1 overview → L2 category → L3 detailed) reducing per-query read cost from ~4k tokens to ~1.7k tokens
- **O2 (Fix Q4 Contradiction)**: Resolve the orphan-night/pricing contradiction flagged in metadata, updating atoms and establishing ground truth
- **O3 (Language Consistency)**: Standardize atom casing, terminology, and structure across the vault to reduce disambiguation overhead

**Effort**: ~6.5 hours total  
**Quality Impact**: Expected vault quality score improvement from 8.52 → 8.9  
**Unlock**: Phase 2 improvements depend on Phase 1 foundation

---

## Optimizations

### O1: Hierarchical Indices (4 hours)

**What it does**: Replace single `index.md` with a 3-tier index structure.

**Current state**: `index.md` is 344 lines ≈ 4k tokens, flat list of all content.

**Target state**:
- `index.md` (L1): ≤100 lines, overview + category links (≤1k tokens)
- `index/topics.md` (L2): All MOCs with brief descriptions
- `index/atoms.md` (L2): All atoms grouped by topic with one-liner summaries
- `index/queries.md` (L2): Cached queries by topic

**Why**: Smaller L1 footprint → more tokens available for actual content in queries. Self-check in §4.2 step 7 becomes faster.

**Verification**: Run `budget-check.sh --index-read` → should report L1 read ≤1.7k tokens.

---

### O2: Fix Q4 Contradiction (0.5 hours)

**What it does**: Resolve the pricing/orphan-night contradiction blocking Phase 2 quality improvements.

**Current state**: Two conflicting atoms about orphan-night pricing strategy (flagged in `meta/contradictions.md`).

**Target state**: Single authoritative atom with caveats, both source atoms updated with cross-reference, `meta/contradictions.md` entry marked resolved.

**Why**: Unresolved contradictions create cognitive friction in responses. Fixing this one removes a known source of low-confidence answers.

**Verification**: No "conflict" label in any atoms under `topics: [pricing, orphan-nights]`.

---

### O3: Language Consistency (2 hours)

**What it does**: Standardize atom writing across the vault.

**Current state**: Mixed casing ("Orphan Night" vs "orphan night"), inconsistent claim format, varied explanation lengths.

**Target state**: All atoms follow §3.2 YAML format strictly, consistent terminology (use glossary from `meta/glossary.md`), claims 1-2 sentences, explanations ≤5 lines.

**Why**: Consistency reduces parsing overhead when reading atoms. Easier to spot outliers (potential errors).

**Verification**: Random 10-atom sample → all follow same format.

---

## Next Steps

1. **Approve Phase 1**: Message: `Approve Phase 1`
2. **Execute O1**: Create hierarchical index structure (see PHASE_1_TASKS.md)
3. **Execute O2**: Resolve contradiction, update both atoms
4. **Execute O3**: Audit and standardize atom format
5. **Verify**: Run quality check, confirm score improvement
6. **Move to Phase 2**: Phase status → "complete", current_phase → 2, phase_status → "pending_approval"
