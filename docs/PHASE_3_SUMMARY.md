# Phase 3: Automation

**Objective**: Reduce manual effort in vault maintenance through intelligent orchestration and caching.

Phase 3 builds on Phases 1-2's structural and quality improvements by automating the repetitive parts: finding related atoms, linking new content, caching common queries.

---

## What Phase 3 Accomplishes

- **O7 (Agent Orchestration)**: Claude Code agent that runs lint passes, detects gaps, and proposes ingests autonomously on a schedule
- **O8 (Auto-Linking System)**: Automatically insert cross-references in atoms when new related atoms are created
- **O9 (Query Caching)**: Store frequently answered questions in `queries/` to reduce re-derivation cost

**Effort**: ~18 hours total  
**Quality Impact**: Quality score 9.3 → 9.6  
**Unlock**: Phase 4 (Integration) requires Phase 3 automation layer

---

## Optimizations

### O7: Agent Orchestration (8 hours)

**What it does**: Schedule Claude Code to run vault maintenance tasks (lint, gap detection, topic suggestions) autonomously.

**Current state**: Lint is manual (§4.3), run on request. No scheduled health checks.

**Target state**: 
- Every 3 days: Run lint sweep, flag stale claims, detect orphans, report gaps
- On-demand: Generate ingest recommendations based on corpus gaps
- Integrated: Updates `log.md` with findings + recommendations

**Why**: Proactive maintenance prevents vault decay. User sees problems before they cause bad answers.

**Implementation**: Create `scripts/vault-agent.py` that reads vault state, runs audits, outputs structured findings.

---

### O8: Auto-Linking System (4 hours)

**What it does**: When a new atom is created, automatically scan the vault and insert backlinks in related atoms.

**Current state**: Cross-references added manually during INGEST.

**Target state**: 
- New atom created with `topics: [pricing, orphan-nights]`
- System scans MOC/pricing.md and MOC/orphan-nights.md
- Finds atoms already discussing the same topics
- Inserts: `[[new-atom]] — <claim summary>` in relevant MOCs
- Optionally inserts "See also: [[new-atom]]" in related atoms' bodies

**Why**: Prevents orphaned atoms. Faster navigation. Readers discover related claims.

**Implementation**: Add post-ingest script `scripts/auto-link.py` invoked after atom creation.

---

### O9: Query Caching (6 hours)

**What it does**: Automatically cache common queries so repeated questions cost ~0 tokens.

**Current state**: Some queries are manually saved; no systematic caching strategy.

**Target state**: 
- Track which queries are answered most (from `log.md`)
- For top 20% queries: auto-regenerate cached version weekly
- Implement query-similarity detection: if new question similar to cached query, return cached answer with caveats
- Add `meta/query-cache-stats.md`: tracks hits vs misses

**Why**: Repeated advice (pricing, guest management) should be instant. Compound returns.

**Implementation**: Add `scripts/cache-optimizer.py` that profiles query patterns and refreshes stale caches.

---

## Next Steps

1. Approve Phase 3
2. Execute O7 (create vault-agent.py)
3. Execute O8 (create auto-link.py)
4. Execute O9 (create cache-optimizer.py + integrate)
5. Test autonomous maintenance
6. Move to Phase 4
