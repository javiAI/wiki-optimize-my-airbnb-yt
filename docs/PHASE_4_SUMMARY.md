# Phase 4: Integration

**Objective**: Connect this vault to the broader project-operating-system ecosystem and enable advanced knowledge synthesis.

Phase 4 brings the optimized Optimize My Airbnb vault into the Meta System (project-operating-system), making its patterns available as templates for other vaults, and adding advanced synthesis capabilities.

---

## What Phase 4 Accomplishes

- **O10 (Semantic Gap Detection)**: Machine-identified gaps in coverage (topics discussed but without decisive guidance)
- **O11 (Backlink Generation)**: Automatically maintain `meta/backlinks.md` showing what cites what
- **O12 (RAG Fallback)**: Fallback to embedding-based retrieval if atom search fails (hybrid approach)

**Effort**: ~13 hours total  
**Quality Impact**: Quality score 9.6 → 9.8 (target)  
**Unlock**: Completion enables vault to be templated and exported

---

## Optimizations

### O10: Semantic Gap Detection (3 hours)

**What it does**: Identify topics where claims exist but are inconclusive or lack actionable guidance.

**Example**: "How to select market?" has 3 atoms, but none give clear decision criteria. Detected as gap.

**Why**: Directs future ingests toward highest-impact content. Improves coverage completeness.

**Implementation**: Score atoms by actionability; flag topics where average score < threshold.

---

### O11: Backlink Generation (4 hours)

**What it does**: Maintain a master map of what cites what (atom → sources, atom → related atoms, query → atoms).

**Current state**: Cross-references are scattered across atom bodies.

**Target state**: 
- `meta/backlinks.md` auto-generated, showing inbound/outbound links per atom
- Links colored by strength: direct citation (strong) vs mention (weak)
- Used by visualization tools (graph view improvements)

**Why**: Understand influence map. Detect hubs. Find gaps where atoms have no inbound links.

---

### O12: RAG Fallback (6 hours)

**What it does**: If atom-based search fails (shortlist empty despite query relevance), fall back to embedding-based retrieval from `sources/`.

**Current state**: Pure atom-based search; if MOC is empty or atoms don't match, query fails.

**Target state**: 
- Layer 1 (primary): atom search via MOC (fast, ≤10k tokens)
- Layer 2 (fallback): embedding-based RAG over `sources/` if Layer 1 returns empty (cost ~15k tokens)
- Caveat: Layer 2 responses marked as "lower confidence" and saved separately

**Why**: Safety net against coverage gaps. Prevents "I don't know" answers when raw source material exists.

**Implementation**: Integrate minimal vector DB (qmd, Ollama, or simple cosine similarity).

---

## Integration with project-operating-system

After Phase 4, this vault becomes a reference implementation. The `project-operating-system` meta-repo can:
- Use this CLAUDE.md kernel (§0-§9) as default template for new vaults
- Reference this vault's optimizations in Fase G (Knowledge Plane)
- Generate new vaults with pre-built phases and scripts

**Handoff**: MASTER_PLAN.md (existing docs/) details full integration path.

---

## Next Steps

1. Approve Phase 4
2. Execute O10 (semantic gap detection)
3. Execute O11 (backlink generation)
4. Execute O12 (RAG fallback integration)
5. Verify vault reaches quality target (9.8)
6. **Complete**: Vault stable, exportable, reusable as template
