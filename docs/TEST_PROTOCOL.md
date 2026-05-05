# Test Protocol — How Claude Executes Parallel Tests (v2)

**This is the operational protocol for Claude.** Read this before running any test.

**All test artifacts live INSIDE THIS REPO** under `vaults/{name}/tests/` (per-vault bundle). The Obsidian vault is read-only context for agents (CLAUDE.md, vault/index.md, vault/notes/, vault/MOC/, vault/sources/). **Agents must NEVER write to the vault.** The orchestrator script enforces this with a hard safety guard (`_ensure_under_tests`).

**Decision version**: 2.0 — composite cost-quality score + targeted dim analysis + statistical repetition. See "Decision logic" below.

---

## Directory Layout

```
.claude/templates/tests/
├── _agent_template.md                  # generic — common preamble for test agents
├── _evaluator_template.md              # generic — common preamble for evaluator
└── _refiner_template.md                # generic — refinement pass

vaults/{name}/tests/                    # per-vault bundle
├── questions.yaml                          # immutable questions (source of truth, vault-specific)
├── prompts/
│   └── <LABEL>/
│       └── meta.yaml                       # target_dims / at_risk_dims / predicted_deltas (REQUIRED for any new OX)
├── raw-responses/
│   └── <LABEL>/
│       └── run-N/                          # one folder per repetition
│           ├── prompts/                    # ephemeral, regenerable from templates
│           │   ├── Q1.md … Q20.md
│           │   └── evaluator.md
│           ├── Q1.json … Q20.json          # agent outputs
│           ├── tokens.json                 # manifest written by orchestrator
│           └── evaluation.json             # written by evaluator agent
├── results/<LABEL>.json                    # aggregated across all runs (mean + SE)
├── comparisons/<TO>-vs-<FROM>.json         # extended diff with composite + decision
└── history.md                              # append-only timeline
```

There is no per-question prompt file under `vaults/{name}/tests/prompts/<LABEL>/` — those are regenerated per run inside `raw-responses/<LABEL>/run-N/prompts/`. The only persistent per-label file in `vaults/{name}/tests/prompts/<LABEL>/` is `meta.yaml`.

---

## When to Run a Test

1. **Initial baseline** (once, before any optimization): establish reference.
2. **Post-optimization** (after each O1, O2, …, O12): measure impact.
3. **Repetition runs** (when triggered by `repetition_advice.should_repeat`): up to 3 total runs per label.
4. **On-demand** (manual `Test now`): verify current state.

---

## meta.yaml — required for any new OX

Before launching tests for `<LABEL>`, create `vaults/{name}/tests/prompts/<LABEL>/meta.yaml`:

```yaml
label: O4
description: "Contradiction Detection L1 (caveat injection at query time)"
optimization_type: quality_lift   # or cost_reduction | hygiene | reference

# Which dims this OX is DESIGNED to improve. Decision is sensitive to these:
# any regression on a target_dim is a hard floor breach (force REVERT).
target_dims: [accuracy]

# Dims that may degrade as a side effect of the change. Tolerated within bounds.
at_risk_dims: [format_compliance]

# Dims expected to be unaffected (variance here is treated as noise).
neutral_dims: [completeness, spanish_purity, tone]

# Quantitative predictions. Used to compute "delivery_pct" in the comparison.
# Cost in % (negative = saving). Quality dims in absolute 0-10 delta.
predicted_deltas:
  cost: +5.0          # caveat injection adds ~5% tokens
  accuracy: +0.5      # primary win
  format_compliance: -0.2

predictions_justification: |
  Why these numbers? E.g., "caveat injection adds ~80 tokens per query × 20% of
  queries = +5% avg; accuracy lift expected because prior runs showed Q4 had
  factual issue caused by missing conflict marker."

# If true, the script may auto-advise repetition when delta is in noise zone.
allow_repetition: true
```

**No meta.yaml = legacy mode**: target_dims = [] and the system falls back to using `weighted_avg` only. Discouraged for new OX.

---

## The 6-Step Protocol (per run)

### Step 1: Prepare run N

```bash
python3 scripts/run-test-suite.py --prepare --label <LABEL> [--run N]
```

If `--run` is omitted, the next available run number is used. Output: `vaults/{name}/tests/raw-responses/<LABEL>/run-N/prompts/Q1.md` … `Q20.md`. Each is composed from `_agent_template.md` + the question text from `questions.yaml`, isolated (vault read-only, no cache, no prior context, exact output path enforced).

### Step 2: Execute (20 parallel agents)

**Critical**: Claude launches 20 Agent tool calls **in a single tool_use response** (parallel).

```
For each Q1-Q20:
  Agent({
    subagent_type: "general-purpose",
    description: "Test agent for QN run-N",
    prompt: <contents of vaults/{name}/tests/raw-responses/<LABEL>/run-N/prompts/QN.md>
  })
```

Each agent reads the vault read-only (CLAUDE.md, index.md, index/, notes/, MOC/, sources/), MUST NOT read `vault/queries/`, MUST NOT have prior context, responds in Spanish per CLAUDE.md §10.7, and saves to `vaults/{name}/tests/raw-responses/<LABEL>/run-N/QN.json`.

### Step 3: Write tokens manifest

The Agent tool reports `total_tokens`, `tool_uses`, `duration_ms` per agent. Claude writes `vaults/{name}/tests/raw-responses/<LABEL>/run-N/tokens.json`:

```json
{
  "Q1":  {"total_tokens": 47333, "tool_uses": 5,  "duration_ms": 46044},
  "Q2":  {"total_tokens": 51271, "tool_uses": 11, "duration_ms": 69264},
  "...": "...",
  "Q20": {"total_tokens": 56900, "tool_uses": 11, "duration_ms": 97304}
}
```

### Step 4: Prepare evaluator prompt

```bash
python3 scripts/run-test-suite.py --prepare-evaluator --label <LABEL> [--run N]
```

Output: `vaults/{name}/tests/raw-responses/<LABEL>/run-N/prompts/evaluator.md` — composed from `_evaluator_template.md`. Embeds the rubric and the paths of the 20 response files.

### Step 5: Execute evaluator (1 Agent call)

Claude launches 1 Agent with the evaluator prompt as input.

The evaluator reads CLAUDE.md (only for §10.7) + the 20 response JSONs, scores each Q1-Q20 on the 5-dim rubric, and writes `vaults/{name}/tests/raw-responses/<LABEL>/run-N/evaluation.json`.

### Step 6: Consolidate + Compare

```bash
python3 scripts/run-test-suite.py --consolidate --label <LABEL>
python3 scripts/run-test-suite.py --compare --from <PREV_LABEL> --to <LABEL>
```

`--consolidate` aggregates **all runs** of the label into `vaults/{name}/tests/results/<LABEL>.json` (mean + SE per dim, mean + SE for cost).
`--compare` produces the extended diff at `vaults/{name}/tests/comparisons/<LABEL>-vs-<PREV>.json`.

After comparing, check the `repetition_advice` field. If `should_repeat: true` and the run count is below `REP_MAX_RUNS` (default 3):

```bash
# Run another iteration for the same label
python3 scripts/run-test-suite.py --prepare --label <LABEL>          # next run number
# → 20 parallel agents → tokens.json
python3 scripts/run-test-suite.py --prepare-evaluator --label <LABEL>
# → 1 evaluator agent → evaluation.json
python3 scripts/run-test-suite.py --consolidate --label <LABEL>      # aggregates ALL runs
python3 scripts/run-test-suite.py --compare --from <PREV> --to <LABEL>
```

`--consolidate` and `--compare` automatically use all available runs (mean + SE).

---

## Rubric (5 dimensions, weighted)

The evaluator scores each response 0-10 per dimension. Weighted average = quality score per question.

| Dim | Weight | What it measures |
|-----|--------|------------------|
| `completeness` | 25% | Cobertura de la pregunta + caveats relevantes |
| `accuracy` | 25% | Hechos correctos, citas válidas, sin invenciones |
| `spanish_purity` | 15% | Solo inglés para nombres propios (PriceLabs, Airbnb…) y tech estándar (WiFi, PMS, API). Penaliza "host", "guest", "review", "amenity", etc. |
| `tone` | 15% | Humano, profesional, con calidez. Penaliza robótico, filler, corporate-speak |
| `format_compliance` | 20% | Sigue §10.7: numbered steps, una `[[atom]]` cite por step, ≤600/1000 palabras, sin filler |

**Quality score per question** = `0.25·completeness + 0.25·accuracy + 0.15·spanish_purity + 0.15·tone + 0.20·format_compliance`.

The full rubric (with grading bands and whitelist) is embedded in `_evaluator_template.md`. Do not modify per-run; if it changes, bump `RUBRIC_VERSION` in `scripts/run-test-suite.py`.

---

## Decision logic (v2.0)

The decision uses three signals, in priority order:

### 1. Hard floors → REVERT

Override everything. If any of these breach, the OX is REVERTed regardless of cost win:

| Floor | Threshold |
|-------|-----------|
| `weighted_avg` absolute | ≥ 7.0 |
| `accuracy` absolute | ≥ 8.0 (no factual regression) |
| Any dim drop absolute | ≤ 1.0 (no dim collapses) |
| Target dim regression | any drop on a declared target_dim |

The "target dim regression" floor codifies your policy: if you declared `target_dims: [X]`, then X dropping means the OX failed at its job — REVERT.

### 2. Target dim delivery → ITERATE if undershoot

For each declared target_dim, the script computes `delivery_pct = (delivered / predicted) * 100`.

- If any target_dim delivers < 50% of its predicted delta → ITERATE (the OX needs refinement).
- If all target_dims deliver ≥ 50% → continue to step 3.

### 3. Composite score → IMPLEMENT / REVERT / ITERATE

```
quality_delta_norm = (q_after − q_before) / 10        # absolute change in 0-1 scale
cost_delta_norm    = (c_before − c_after) / c_before  # positive = saved
composite          = α · quality_delta_norm + (1−α) · cost_delta_norm
```

**α = 0.85** (quality dominant). Rough conversions:

| Cost saved | Quality lost (10-pt scale) | Composite | Decision |
|-----------:|---------------------------:|----------:|----------|
| 50% | 0.0 (none) | +0.075 | IMPLEMENT |
| 25% | 0.1 (1%) | +0.029 | IMPLEMENT (the O1 case) |
| 10% | 0.5 (5%) | −0.027 | REVERT |
| 50% | 1.0 (10%) | −0.010 | REVERT |
| 80% | 1.0 (10%) | +0.035 | IMPLEMENT |

| Composite delta | Decision |
|-----------------|----------|
| ≥ +0.005 | IMPLEMENT |
| ≤ −0.005 | REVERT |
| In ±0.005 | ITERATE (or repeat if `allow_repetition: true`) |

### Repetition trigger

If `composite` falls in ±0.015 (the noise zone) **or** any target_dim has a delta < 0.3 absolute and only 1 run exists, the script advises another run:

```bash
python3 scripts/run-test-suite.py --check-repetition --from <PREV> --to <LABEL>
# exit 0 = no repeat needed
# exit 1 = repeat
```

Max 3 runs per label (`REP_MAX_RUNS`). After 3 runs, decision is final at the current confidence level.

---

## Comparison file format (v2)

`vaults/{name}/tests/comparisons/<TO>-vs-<FROM>.json` schema (highlights):

```json
{
  "from": "baseline", "to": "O1",
  "rubric_version": "1.0",
  "decision_version": "2.0",
  "evaluation_source": "external_evaluator",
  "n_runs": {"from": 1, "to": 1, "min": 1},
  "meta": {
    "target_dims": ["accuracy"],
    "at_risk_dims": ["format_compliance"],
    "predicted_deltas": {"cost": +5, "accuracy": +0.5}
  },
  "metrics": {
    "cost": {"weighted_cost": {"before": ..., "after": ..., "delta_pct": ..., "significance": {"ci95_low": ..., "ci95_high": ..., "significant": true}}},
    "quality": {
      "completeness": {"before": ..., "after": ..., "delta_abs": ..., "category": "neutral", "predicted_delivery_pct": null, "significance": {...}},
      "accuracy": {..., "category": "target", "predicted_delivery_pct": 80.0, ...},
      "weighted_avg": {"before": ..., "after": ..., "significance": {...}}
    },
    "composite": {"alpha": 0.85, "value": +0.0293, "quality_delta_norm": ..., "cost_delta_norm": ...}
  },
  "targeted_analysis": {
    "target_dims": [{"dim": "accuracy", "predicted": +0.5, "delivered": +0.4, "delivery_pct": 80, "ci95": [...], "significant": true}],
    "at_risk_dims": [{"dim": "format_compliance", "delta_abs": -0.2, "ci95": [...], "significant": false}]
  },
  "floor_breaches": [],
  "summary_table": [...],
  "decision": {"action": "IMPLEMENT|ITERATE|REVERT", "primary_reason": "composite_positive|target_dim_regression|...", "reasons": [...], "composite": +0.0293},
  "repetition_advice": {"should_repeat": false, "reason": "decision is clear at current N"}
}
```

The `targeted_analysis` block is the primary thing a human should read: it tells you whether the OX did what it promised. The `summary_table` flattens everything for human consumption. The `decision` field is the bottom line.

---

## Critical Rules (Never Violate)

1. **Vault is read-only**: agents MUST NOT write under `$VAULT_PATH/`. All writes go to `vaults/{name}/tests/`. Enforced by `_ensure_under_tests`.
2. **No cache access**: agents MUST NOT read `vault/queries/`.
3. **No prior context**: each Agent is fresh.
4. **Same questions always**: 20 questions in `vaults/{name}/tests/questions.yaml` are immutable.
5. **External evaluator required**: don't accept self-assessment as the quality metric. Always run `--prepare-evaluator` + 1 Agent call.
6. **Parallel execution**: all 20 test Agent calls in ONE tool_use response.
7. **meta.yaml required for new OX**: declare `target_dims` / `at_risk_dims` / `predicted_deltas` BEFORE running the test. The A/B/C section in `docs/PHASE_<N>_TASKS.md` and `meta.yaml` must agree.
8. **Respect repetition advice**: if the script says repeat, repeat (up to 3 runs). Do not declare a borderline IMPLEMENT/REVERT on a single run.
9. **Hard floors override composite**: if the script returns REVERT due to a floor breach, do not override without user input.

---

## Full cycle example (with repetition)

```bash
# === Run 1 ===
python3 scripts/run-test-suite.py --prepare --label O4
# Claude launches 20 parallel Agent calls; each writes to vaults/{name}/tests/raw-responses/O4/run-1/Q*.json
# Claude writes vaults/{name}/tests/raw-responses/O4/run-1/tokens.json
python3 scripts/run-test-suite.py --prepare-evaluator --label O4
# Claude launches 1 evaluator Agent; writes vaults/{name}/tests/raw-responses/O4/run-1/evaluation.json
python3 scripts/run-test-suite.py --consolidate --label O4
python3 scripts/run-test-suite.py --compare --from O3 --to O4
# Read vaults/{name}/tests/comparisons/O4-vs-O3.json → check repetition_advice

# If should_repeat: true
python3 scripts/run-test-suite.py --prepare --label O4               # run-2 auto-allocated
# … 20 agents → tokens.json
python3 scripts/run-test-suite.py --prepare-evaluator --label O4
# … 1 evaluator → evaluation.json
python3 scripts/run-test-suite.py --consolidate --label O4           # aggregates run-1 + run-2
python3 scripts/run-test-suite.py --compare --from O3 --to O4

# Continue until repetition_advice.should_repeat = false OR run-3 reached.
# Then act on decision: IMPLEMENT / ITERATE / REVERT.
```

---

## Why this design

**Sequential ≠ parallel**: 20 Agent calls in a single message = real isolation, real parallelism, reproducibility.

**External evaluator over self-assessment**: agents are unreliable graders. A fresh evaluator with a fixed rubric produces deltas comparable across runs.

**5-dim rubric over single quality score**: a single number hides regressions (e.g. tone drops while completeness rises).

**Composite score over independent thresholds**: previously the decision treated cost and quality independently with arbitrary 2% thresholds. Composite makes the trade-off explicit and tunable (`α`).

**Targeted dim analysis**: optimizations are designed to move specific dims; treating all dims equally washes out signal with noise. Declaring target/at_risk/neutral upfront forces the comparison to evaluate against the actual hypothesis.

**Statistical repetition**: a single run on noisy LLM outputs can move the composite by ±0.02 randomly. Three runs let us estimate SE and avoid false IMPLEMENT/REVERT decisions on noise.

**Repo as source of truth**: all test artifacts live here. Vault is content (read-only). Mixing them caused prior loss of test history.
