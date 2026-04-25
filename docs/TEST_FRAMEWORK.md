# Test Framework — Deterministic Optimization Evaluation

**Purpose**: Establish rigorous, deterministic testing to measure if each optimization improves the system.

**Principle**: Test limpio = identical conditions, same queries, zero cache, zero context, identical instructions (except the optimization itself).

---

## 1. Baseline Setup

### 1.1 Test Environment

A "clean" test means:
- **Zero cache**: No `queries/` cache, no session context
- **Zero context**: Agent starts fresh, reads CLAUDE.md only (never reads prior session data)
- **Identical instructions**: Same CLAUDE.md kernel §0-§9 + domain §10 (except when optimization changes instructions)
- **Identical queries**: Always the same 10 benchmark queries (see §2)
- **Identical agent config**: Same model, same temperature, same constraints

### 1.2 Test Directory Structure

```
vault/meta/tests/
├── config.yaml              # Benchmark queries + expected patterns
├── baseline-PRE.json        # Results before any optimizations
├── O1-PRE.json             # Results before O1
├── O1-POST.json            # Results after O1
├── O2-PRE.json             # Results before O2
├── O2-POST.json            # Results after O2
├── comparison-O1.json       # Diff: O1-POST vs O1-PRE
├── comparison-O2.json       # Diff: O2-POST vs O2-PRE
└── master-report.md         # Timeline of all optimizations + results
```

### 1.3 Cleaning Script

**`scripts/clean-test-env.sh`** — Executed before every test run:

```bash
#!/bin/bash
# Purpose: Reset vault to clean state for testing

set -e

VAULT_PATH="${VAULT_PATH:-$(grep VAULT_PATH scripts/config.sh | cut -d= -f2 | tr -d \"')}"

echo "🧹 Cleaning test environment..."

# 1. Clear cache
rm -rf "$VAULT_PATH/queries/*.md" 2>/dev/null || true

# 2. Clear test artifacts (but keep config.yaml)
rm -rf "$VAULT_PATH/meta/tests/"*.json 2>/dev/null || true

# 3. Verify sources intact (never delete)
if [ ! -d "$VAULT_PATH/sources" ]; then
  echo "❌ ERROR: sources/ missing. Aborting."
  exit 1
fi

# 4. Verify notes intact (never delete)
if [ ! -d "$VAULT_PATH/notes" ]; then
  echo "❌ ERROR: notes/ missing. Aborting."
  exit 1
fi

# 5. Reset CLAUDE.md to known state
# (Only update automation.current_phase and phase_status if needed; never change kernel §0-§9)
echo "✅ Test environment clean. Ready for test run."
```

---

## 2. Benchmark Queries

**10 standard queries**, language-agnostic, covering all major topics:

```yaml
benchmark_queries:
  Q1:
    question: "¿Cuál es la mejor estrategia de precio para noche huérfana en temporada alta?"
    topic: [pricing, orphan-nights]
    regime: B  # Tactical multi-step
    
  Q2:
    question: "¿Qué ratio de ocupación es aceptable para una propiedad de Airbnb?"
    topic: [occupancy, metrics]
    regime: A  # Factual
    
  Q3:
    question: "¿Cómo mejoro mi rating si estoy en 4.8?"
    topic: [reviews, quality]
    regime: B  # Tactical
    
  Q4:
    question: "¿Debe cobrar diferente por limpieza vs pernoctación?"
    topic: [pricing, cleaning]
    regime: B  # Decision-making
    
  Q5:
    question: "¿Qué regiones tienen mejor mercado ahora?"
    topic: [market-selection, trends]
    regime: B  # Analysis
    
  Q6:
    question: "¿Cuántas fotos necesito en mi listing?"
    topic: [listing-optimization]
    regime: A  # Factual
    
  Q7:
    question: "¿Cómo manejo las cancelaciones de último minuto?"
    topic: [guest-management, operations]
    regime: B  # Tactical
    
  Q8:
    question: "¿Es mejor Direct Booking o Airbnb?"
    topic: [direct-booking, platform-strategy]
    regime: C  # Taxonomic comparison
    
  Q9:
    question: "¿Qué roles tiene el equipo de limpieza?"
    topic: [cleaning-ops, team]
    regime: B  # Procedural
    
  Q10:
    question: "¿Cuándo debo cambiar de precio dinámico a precio fijo?"
    topic: [pricing, tools-tech]
    regime: B  # Decision tree
```

---

## 3. Test Execution

### 3.1 Pre-Optimization Test (Baseline or Pre-Optimization)

**Phase**: Before implementing optimization

```bash
# 1. Clean environment
./scripts/clean-test-env.sh

# 2. Verify CLAUDE.md state (document which version)
echo "CLAUDE.md kernel §0-§9 hash: $(md5 CLAUDE.md | head -c 8)" >> meta/tests/test-log.md

# 3. Agent spawns (fresh, no prior context)
# For each Q1-Q10:
#   - Agent reads CLAUDE.md only
#   - Agent answers question
#   - Record: response, tokens_used, latency, quality_score

# 4. Save results
jq -n \
  --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg phase "baseline" \
  --arg clause_md5 "$(md5 CLAUDE.md | head -c 8)" \
  '{timestamp, phase, clause_md5, queries: []}' > meta/tests/baseline-PRE.json
```

**Record format** (for each query):

```json
{
  "Q1": {
    "question": "¿Cuál es la mejor estrategia de precio para noche huérfana en temporada alta?",
    "response_tokens": 248,
    "input_tokens": 1847,
    "total_tokens": 2095,
    "latency_ms": 3420,
    "quality_score": 7.8,
    "atoms_cited": 3,
    "sources_cited": 2,
    "cache_hit": false,
    "confidence": "medium-high"
  }
}
```

### 3.2 Apply Optimization

**Example**: O1 (Hierarchical Indices)

```bash
# 1. Implement O1 (as per PHASE_1_TASKS.md)
#    - Create hierarchical index structure
#    - Update cross-links
#    - Verify in Obsidian

# 2. Update CLAUDE.md
#    - Note: Only §10 (domain) changes if indices reorganized; kernel §0-§9 unchanged
#    - If kernel changes, document why

# 3. Git commit
git commit -m "O1: Hierarchical indices (optimization candidate)"

# 4. Verify setup
./scripts/clean-test-env.sh
```

### 3.3 Post-Optimization Test

**Phase**: After implementing optimization, test again

```bash
# 1. Clean environment (same as Pre)
./scripts/clean-test-env.sh

# 2. Verify CLAUDE.md state
echo "CLAUDE.md kernel §0-§9 hash: $(md5 CLAUDE.md | head -c 8)" >> meta/tests/test-log.md

# 3. Agent spawns (fresh, no prior context)
# For each Q1-Q10 (same queries as Pre):
#    - Identical conditions as Pre test
#    - Agent reads (possibly modified) CLAUDE.md
#    - Record identical metrics

# 4. Save results
jq -n \
  --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg optimization "O1" \
  --arg phase "post" \
  --arg clause_md5 "$(md5 CLAUDE.md | head -c 8)" \
  '{timestamp, optimization, phase, clause_md5, queries: []}' > meta/tests/O1-POST.json
```

---

## 4. Metrics

### 4.1 Measured per Query

- **response_tokens**: Tokens in agent's response (quality indicator)
- **input_tokens**: Tokens in prompt (efficiency indicator)
- **total_tokens**: input + response (cost indicator)
- **latency_ms**: Time from query to response (speed indicator)
- **quality_score**: 1-10 scale (relevance, accuracy, completeness)
- **atoms_cited**: Number of atoms used in answer
- **sources_cited**: Number of sources (videos/articles) cited
- **cache_hit**: Was this answer fetched from cache?
- **confidence**: self-assessed confidence (high/medium/low)

### 4.2 Aggregated Metrics (across all 10 queries)

```json
{
  "baseline": {
    "avg_total_tokens": 2150,
    "median_total_tokens": 2100,
    "p95_total_tokens": 2400,
    "avg_latency_ms": 3200,
    "avg_quality_score": 7.6,
    "atoms_per_query": 3.2,
    "sources_per_query": 2.1,
    "cache_hits": 0,
    "avg_confidence": "medium-high"
  }
}
```

---

## 5. Comparison & Decision

### 5.1 Diff Format

**`comparison-O1.json`**:

```json
{
  "optimization": "O1",
  "pre": "O1-PRE.json",
  "post": "O1-POST.json",
  "metrics": {
    "avg_total_tokens": {
      "pre": 2150,
      "post": 1847,
      "delta": -303,
      "percent_change": -14.1,
      "direction": "improvement"
    },
    "avg_latency_ms": {
      "pre": 3200,
      "post": 2950,
      "delta": -250,
      "percent_change": -7.8,
      "direction": "improvement"
    },
    "avg_quality_score": {
      "pre": 7.6,
      "post": 7.8,
      "delta": 0.2,
      "percent_change": 2.6,
      "direction": "slight_improvement"
    }
  },
  "decision": {
    "tokens_improvement": true,
    "quality_maintained_or_improved": true,
    "recommend": "IMPLEMENT"
  }
}
```

### 5.2 Decision Logic

**Decision matrix**:

| Scenario | Decision | Action |
|----------|----------|--------|
| Tokens ↓, Quality ↑ | **IMPLEMENT** | Commit, move to next optimization |
| Tokens ↓, Quality → | **IMPLEMENT** | Commit, move to next optimization |
| Tokens →, Quality ↑ | **IMPLEMENT** | Commit, move to next optimization |
| Tokens ↑, Quality ↑ | **IMPLEMENT** | Only if quality gain >> token cost |
| Tokens ↑, Quality → | **ITERATE** | Refine optimization, re-test |
| Tokens ↑, Quality ↓ | **REVERT** | Discard, move to next optimization |
| Tokens →, Quality ↓ | **REVERT** | Discard, move to next optimization |
| Tokens ↓, Quality ↓ | **REVERT** | Never acceptable |

**Example**: O1 above → tokens ↓14%, quality +2.6% → **IMPLEMENT**

### 5.3 Iteration

If decision is **ITERATE**:

1. Analyze which metrics regressed
2. Refine optimization strategy
3. Clean test environment
4. Re-test (go to §3.3 again)
5. Re-compare
6. If still no improvement after 2 iterations: **REVERT** and move to next optimization

---

## 6. Automation: Full Test Cycle

**`scripts/run-optimization-cycle.py`** — Executes full cycle automatically:

```python
#!/usr/bin/env python3
"""
Optimization Testing Cycle

Usage:
  python3 scripts/run-optimization-cycle.py --optimization O1
  
Flow:
  1. Clean environment
  2. Run pre-test (or use existing baseline)
  3. Implement optimization
  4. Clean environment
  5. Run post-test
  6. Compare results
  7. Decide: IMPLEMENT, ITERATE, or REVERT
  8. Update master-report.md
  9. Git commit
"""

import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

def clean_test_env():
    """Run clean-test-env.sh"""
    subprocess.run(["bash", "scripts/clean-test-env.sh"], check=True)

def run_test(optimization_id, phase):
    """Execute test: run all 10 benchmark queries, record metrics"""
    # 1. Load benchmark queries from config.yaml
    # 2. For each query:
    #    - Spawn agent
    #    - Record response + metrics
    # 3. Save results to meta/tests/{optimization_id}-{phase}.json
    pass

def compare_results(optimization_id):
    """Load PRE and POST, compute diffs, decide"""
    # 1. Load {optimization_id}-PRE.json and {optimization_id}-POST.json
    # 2. Compute deltas for all metrics
    # 3. Apply decision logic
    # 4. Return: {"decision": "IMPLEMENT|ITERATE|REVERT", "metrics": {...}}
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimization", required=True, help="O1, O2, O3, etc.")
    args = parser.parse_args()
    
    opt_id = args.optimization
    
    print(f"🧪 Starting optimization cycle for {opt_id}")
    
    # Pre-test
    clean_test_env()
    print(f"  1️⃣  Pre-test...")
    run_test(opt_id, "PRE")
    
    # Implement
    print(f"  2️⃣  Implementing {opt_id}...")
    # (Placeholder; actual implementation follows PHASE_X_TASKS.md)
    
    # Post-test
    clean_test_env()
    print(f"  3️⃣  Post-test...")
    run_test(opt_id, "POST")
    
    # Compare
    print(f"  4️⃣  Comparing results...")
    result = compare_results(opt_id)
    
    # Decide
    decision = result["decision"]
    print(f"  5️⃣  Decision: {decision}")
    
    if decision == "IMPLEMENT":
        print(f"✅ Committing {opt_id}")
        subprocess.run(["git", "commit", "-m", f"{opt_id}: Optimization implemented (test verified improvement)"], check=True)
    elif decision == "ITERATE":
        print(f"⚠️  {opt_id} needs iteration. Modify and re-run.")
    elif decision == "REVERT":
        print(f"❌ {opt_id} caused regression. Reverting...")
        subprocess.run(["git", "revert", "--no-edit", "HEAD"], check=True)
    
    # Update master report
    # (Add entry to meta/tests/master-report.md)
    
    print(f"🏁 Cycle complete: {opt_id} → {decision}")

if __name__ == "__main__":
    main()
```

---

## 7. Master Report

**`meta/tests/master-report.md`** — Append-only log of all optimization cycles:

```markdown
# Optimization Test Report — Master Timeline

## Baseline
- **Date**: 2026-04-25
- **CLAUDE.md hash**: 8f4c9a2b
- **Vault state**: 156 atoms, 12 MOCs, 173 sources
- **Avg tokens/query**: 2150
- **Avg quality**: 7.6
- **File**: `baseline-PRE.json`

---

## O1 (Hierarchical Indices)
- **Started**: 2026-04-25 10:30 UTC
- **Pre-test tokens**: 2150 → Post-test: 1847 ↓14%
- **Pre-test quality**: 7.6 → Post-test: 7.8 ↑2.6%
- **Decision**: ✅ IMPLEMENT (tokens down, quality up)
- **Committed**: 2026-04-25 11:15 UTC
- **Files**: `O1-PRE.json`, `O1-POST.json`, `comparison-O1.json`

---

## O2 (Fix Q4 Contradiction)
- **Started**: 2026-04-25 11:20 UTC
- **Pre-test tokens**: 1847 → Post-test: 1821 ↓1.4%
- **Pre-test quality**: 7.8 → Post-test: 7.9 ↑1.3%
- **Decision**: ✅ IMPLEMENT (marginal but positive)
- **Committed**: 2026-04-25 11:45 UTC
- **Files**: `O2-PRE.json`, `O2-POST.json`, `comparison-O2.json`

---

(Continues for O3-O12...)
```

---

## 8. Running the Full Automation

**Complete cycle** (test, optimize, test, decide, repeat):

```bash
#!/bin/bash
# scripts/run-all-optimizations.sh

OPTIMIZATIONS=(O1 O2 O3 O4 O5 O6 O7 O8 O9 O10 O11 O12)

for opt in "${OPTIMIZATIONS[@]}"; do
  echo "🔄 Starting cycle: $opt"
  python3 scripts/run-optimization-cycle.py --optimization "$opt"
  
  if [ $? -ne 0 ]; then
    echo "❌ $opt failed. Stopping."
    exit 1
  fi
  
  echo "✅ $opt complete. Moving to next."
done

echo "🎉 All optimizations complete!"
echo "Review: meta/tests/master-report.md"
```

---

## 9. Success Criteria

A test framework is **successful** when:

✅ Same queries always produce comparable results (within 5% variance)  
✅ Changes in metrics clearly correlate with code changes  
✅ Decision logic is unambiguous (no subjective judgment)  
✅ Full cycle (pre-test → implement → post-test → decide) takes <2 hours per optimization  
✅ Results are reproducible (re-run with same code = same metrics)  
