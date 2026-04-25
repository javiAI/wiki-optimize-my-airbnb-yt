# Test Protocol — How Claude Executes Parallel Tests

**This is the operational protocol for Claude.** Read this before running any test.

---

## When to Run a Test

Tests run at these moments:

1. **Initial baseline** (once, before any optimization): Establish reference metrics
2. **Post-optimization** (after each O1, O2, ..., O12): Measure impact
3. **On-demand** (manual `Test now`): Verify current state

---

## The 4-Step Protocol

### Step 1: Prepare (Generate isolated prompts)

```bash
python3 scripts/run-test-suite.py --prepare --label <LABEL>
```

Where `<LABEL>` is one of: `baseline`, `O1`, `O2`, ..., `O12`

**Output**: 20 prompt files at `$VAULT_PATH/meta/tests/prompts/<LABEL>/Q1.md` through `Q20.md`

Each prompt:
- Contains ONE question
- Contains strict instructions (no cache access, no prior context)
- Specifies output path for the agent's response

---

### Step 2: Execute (20 parallel agents)

**This is the critical step.** Claude launches 20 Agent tool calls **in a single message** (parallel execution).

**Pattern**:

```
For each question Q1-Q20:
  Use Agent tool with:
    - subagent_type: "general-purpose"
    - description: "Test agent for QN"
    - prompt: <contents of meta/tests/prompts/<LABEL>/QN.md>
```

**ALL 20 calls must be in the SAME tool_use response** (not sequential).

**Critical constraints for each agent**:
- Must NOT read `vault/queries/` (cache) — explicit prohibition in prompt
- Must NOT have prior conversation context (each Agent is fresh)
- Must respond in Spanish following CLAUDE.md §10.7 contract
- Must save JSON response to `$VAULT_PATH/meta/tests/raw-responses/<LABEL>-QN.json`

---

### Step 3: Consolidate

**Critical**: The Agent tool only reports `total_tokens` per agent — not the input/output split. Claude (orchestrator) MUST capture token usage from each Agent tool result and write a tokens manifest BEFORE consolidating.

**3a. Write tokens manifest** at `$VAULT_PATH/meta/tests/raw-responses/<LABEL>-tokens.json`:

```json
{
  "Q1":  {"total_tokens": 47333, "tool_uses": 5,  "duration_ms": 46044},
  "Q2":  {"total_tokens": 51271, "tool_uses": 11, "duration_ms": 69264},
  ...
  "Q20": {"total_tokens": 56900, "tool_uses": 11, "duration_ms": 97304}
}
```

Each Agent tool result includes a `<usage>` block — copy `total_tokens`, `tool_uses`, `duration_ms` into the manifest.

**3b. Consolidate**:

```bash
python3 scripts/run-test-suite.py --consolidate --label <LABEL>
# Auto-detects tokens file at default path, or pass --tokens-file <path>
```

**Output**:
- `baseline-results.json` (if label=baseline)
- `optimizations/<LABEL>-results.json` (if label=O1, O2, ...)

**Token model** (since Agent tool doesn't expose input/output split):
- `total_tokens`: observed from Agent tool (passed via tokens manifest)
- `output_tokens_estimated`: `len(response) / 4.0` (Spanish chars→tokens; stable proxy)
- `input_tokens`: `total_tokens - output_tokens_estimated`
- `weighted_cost`: `input + 6 × output` (matches pricing requirement)

Estimation bias is constant across runs, so optimization deltas remain valid.

**Aggregated metrics**:
- avg/total input/output tokens
- avg/total weighted cost ← primary optimization target
- avg quality score (from agent self-assessment `completeness`)
- avg latency (ms)
- Per-level breakdown (1=basic, 4=expert)

---

### Step 4: Compare & Decide

```bash
python3 scripts/run-test-suite.py --compare --from <PREV_LABEL> --to <CURRENT_LABEL>
```

**Examples**:
- `--from baseline --to O1` (first optimization)
- `--from O1 --to O2` (second optimization, comparing against O1 result)
- `--from O5 --to O6` (sixth optimization)

**Output**: `optimizations/<LABEL>-comparison.json` with:
- Cost delta (%)
- Quality delta (%)
- **Decision**: IMPLEMENT, ITERATE, or REVERT

---

## Decision Logic

| Cost Δ | Quality Δ | Decision | Action |
|--------|-----------|----------|--------|
| ≤ -2% | ≥ -2% | **IMPLEMENT** | Keep commit, move to next optimization |
| ≤ +2% | ≥ -2% | **IMPLEMENT** | Stable cost, quality maintained or up |
| > +2% | > +2% (gain >> cost) | **IMPLEMENT** | Quality worth the cost |
| > +2% | ≈ same | **ITERATE** | Refine optimization, retry |
| any | < -2% | **REVERT** | `git revert HEAD`, mark as failed |

---

## Full Cycle Example

**Goal**: Run baseline test, then test after O1.

```bash
# 1. Baseline (do once at start)
python3 scripts/run-test-suite.py --prepare --label baseline

# 2. Claude launches 20 Agent calls in parallel (single message)
#    Each agent: read prompt → answer → save JSON

# 3. Consolidate baseline
python3 scripts/run-test-suite.py --consolidate --label baseline

# === Now baseline-results.json exists ===

# 4. Implement O1 (per PHASE_1_TASKS.md)
# ... Claude executes O1 changes ...
git commit -m "O1: Hierarchical Indices"

# 5. Test post-O1
python3 scripts/run-test-suite.py --prepare --label O1
# Claude launches 20 parallel Agent calls again
python3 scripts/run-test-suite.py --consolidate --label O1

# 6. Compare baseline → O1
python3 scripts/run-test-suite.py --compare --from baseline --to O1

# 7. Read decision from O1-comparison.json
#    If IMPLEMENT: continue to O2
#    If REVERT: git revert HEAD
#    If ITERATE: refine O1, redo test

# 8. Update CLAUDE.md state and commit
```

---

## Critical Rules (Never Violate)

1. **No cache access**: Agents MUST NOT read `vault/queries/`
2. **No prior context**: Each Agent is fresh (use Agent tool, not nested conversations)
3. **Same questions always**: 20 questions in `baseline-questions.yaml` are immutable
4. **Same instructions always**: Only exception is when optimization itself changes instructions
5. **Parallel execution**: All 20 Agent calls in ONE tool_use response (not sequential)
6. **Weighted cost matters**: Output tokens cost 6x more than input — optimize for `weighted_cost`

---

## File Structure Reference

```
$VAULT_PATH/meta/tests/
├── baseline-questions.yaml        # 20 questions (immutable)
├── baseline-results.json          # Initial reference metrics
├── prompts/                       # Generated per test run
│   ├── baseline/
│   │   ├── Q1.md ... Q20.md
│   ├── O1/
│   │   ├── Q1.md ... Q20.md
│   └── O2/ ...
├── raw-responses/                 # Per-agent outputs
│   ├── baseline-Q1.json ... baseline-Q20.json
│   ├── O1-Q1.json ... O1-Q20.json
│   └── O2-Q*.json ...
├── optimizations/                 # Consolidated + comparisons
│   ├── O1-results.json
│   ├── O1-comparison.json
│   ├── O2-results.json
│   └── O2-comparison.json
└── history.md                     # Timeline (markdown)
```

---

## Why This Design

**Sequential ≠ Parallel**: We need 20 truly fresh agents. Using Claude's Agent tool 20 times in a single response gives us:
- Real isolation (each Agent has no shared context)
- Real parallelism (Claude executes them concurrently)
- Reproducibility (same prompts, same questions = comparable results)

**No redundancy**: O1-results becomes the comparison baseline for O2 (no need to duplicate).

**Append-only history**: Each test run adds new files; old files never modified.
