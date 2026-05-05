#!/usr/bin/env python3
"""
Test Suite Orchestrator (multi-run + composite + targeted analysis)

Runs the 6-step protocol per docs/TEST_PROTOCOL.md, with:
- Per-run isolation under vaults/{name}/tests/raw-responses/<LABEL>/run-N/
- Common prompt templates at .claude/templates/tests/_agent_template.md and
  _evaluator_template.md (no per-question prompt duplication)
- Per-label metadata at vaults/{name}/tests/prompts/<LABEL>/meta.yaml declaring
  target_dims / at_risk_dims / predicted_deltas
- Composite cost-quality decision metric (alpha-weighted)
- Hard floors that override composite (REVERT immediately)
- Statistical aggregation across runs (mean + standard error)
- Repetition trigger when deltas are within noise threshold

ALL test artifacts live INSIDE THIS REPO under vaults/{name}/tests/. The Obsidian
vault is read-only context for agents; agents NEVER write to the vault.

Usage:
  # Prepare run N for a label (composes prompts from templates + questions.yaml)
  python3 scripts/run-test-suite.py --prepare --label OX [--run N]

  # Prepare evaluator for run N
  python3 scripts/run-test-suite.py --prepare-evaluator --label OX [--run N]

  # Consolidate ALL runs of a label (aggregates with statistical metrics)
  python3 scripts/run-test-suite.py --consolidate --label OX

  # Compare with new logic (uses meta.yaml of TO label)
  python3 scripts/run-test-suite.py --compare --from FROM --to TO

  # Check if repetition is warranted (returns exit 0=no, 1=yes)
  python3 scripts/run-test-suite.py --check-repetition --from FROM --to TO

If --run is omitted in --prepare/--prepare-evaluator, the next available run
number is used. The orchestrator (Claude) launches the agents.
"""

import argparse
import json
import math
import os
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / ".claude" / "scripts"))
from config import VaultConfig  # noqa: E402

# Lazy-initialized directory structure (resolved after VaultConfig())
_cfg: VaultConfig = None
TESTS_DIR: Path = None
PROMPTS_DIR: Path = None
RAW_DIR: Path = None
RESULTS_DIR: Path = None
COMPARISONS_DIR: Path = None
QUESTIONS_FILE: Path = None
VAULT_PATH: str = None

TEMPLATES_DIR = REPO_ROOT / ".claude" / "templates" / "tests"
AGENT_TEMPLATE_FILE = TEMPLATES_DIR / "_agent_template.md"
EVALUATOR_TEMPLATE_FILE = TEMPLATES_DIR / "_evaluator_template.md"
REFINER_TEMPLATE_FILE = TEMPLATES_DIR / "_refiner_template.md"

REFINE_DIM_THRESHOLD = 7   # any rubric dim score < this triggers refinement


def _init_vault_config(vault_arg: str = None):
    """Initialize VaultConfig and set up directory paths. Call this once from main()."""
    global _cfg, TESTS_DIR, PROMPTS_DIR, RAW_DIR, RESULTS_DIR, COMPARISONS_DIR
    global QUESTIONS_FILE, VAULT_PATH

    _cfg = VaultConfig(vault_arg or None)

    TESTS_DIR = REPO_ROOT / "vaults" / _cfg.name / "tests"
    PROMPTS_DIR = TESTS_DIR / "prompts"
    RAW_DIR = TESTS_DIR / "raw-responses"
    RESULTS_DIR = TESTS_DIR / "results"
    COMPARISONS_DIR = TESTS_DIR / "comparisons"
    QUESTIONS_FILE = TESTS_DIR / "questions.yaml"
    VAULT_PATH = os.environ.get("VAULT_PATH", str(_cfg.vault_path))

OUTPUT_TOKEN_WEIGHT = 6
SPANISH_CHARS_PER_TOKEN = 4.0

RUBRIC_VERSION = "1.0"
RUBRIC = {
    "completeness":      {"weight": 0.25, "label": "Cobertura"},
    "accuracy":          {"weight": 0.25, "label": "Exactitud"},
    "spanish_purity":    {"weight": 0.15, "label": "Pureza español"},
    "tone":              {"weight": 0.15, "label": "Tono"},
    "format_compliance": {"weight": 0.20, "label": "Format §10.7"},
}

# === Decision parameters ===
DECISION_VERSION = "2.0"

# Composite formula: composite = ALPHA * quality_delta_norm + (1 - ALPHA) * cost_delta_norm
# quality_delta_norm = (q_after - q_before) / 10  (absolute change in 0-1 scale)
# cost_delta_norm    = (c_before - c_after) / c_before  (positive = saved)
# ALPHA = 0.85 -> 1 quality point ≈ 57% cost savings to break even.
ALPHA = 0.85

# Hard floors (override composite, force REVERT)
FLOOR_WEIGHTED_AVG_ABS = 7.0       # weighted_avg must stay >= 7.0
FLOOR_ACCURACY_ABS = 8.0           # accuracy must stay >= 8.0
FLOOR_ANY_DIM_DROP_ABS = 1.0       # no dim may drop > 1.0 absolute (10% of scale)
TARGET_DIM_DROP_TOLERANCE = 0.0    # any drop on a target_dim is failure

# Decision thresholds on composite delta
COMPOSITE_IMPLEMENT = 0.005        # >= +0.005 -> IMPLEMENT
COMPOSITE_REVERT = -0.005          # <= -0.005 -> REVERT/ITERATE
# Between: borderline, prefer ITERATE

# Repetition trigger thresholds
REP_COMPOSITE_NOISE = 0.015        # |composite| < this -> noise-zone, repeat
REP_TARGET_DELIVERY_FRACTION = 0.5 # target_dim must deliver >= 50% of predicted delta
REP_MAX_RUNS = 3                   # max runs per label


# ----------------------------------------------------------------------
# Safety
# ----------------------------------------------------------------------

def _ensure_under_tests(path: Path):
    abs_path = path.resolve()
    tests_resolved = TESTS_DIR.resolve()
    if tests_resolved not in abs_path.parents and abs_path != tests_resolved:
        raise RuntimeError(f"SAFETY: refusing to write outside {TESTS_DIR}: {abs_path}")


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

def load_questions():
    with open(QUESTIONS_FILE) as f:
        return yaml.safe_load(f)


def load_meta(label):
    meta_path = PROMPTS_DIR / label / "meta.yaml"
    if not meta_path.exists():
        # Legacy label without meta — treat as "no targets, no risk", all dims neutral
        return {
            "label": label,
            "description": "(no meta.yaml)",
            "optimization_type": "legacy",
            "target_dims": [],
            "at_risk_dims": [],
            "neutral_dims": list(RUBRIC.keys()),
            "predicted_deltas": {},
            "predictions_justification": "",
            "allow_repetition": True,
        }
    with open(meta_path) as f:
        return yaml.safe_load(f)


def _run_dir(label, run):
    return RAW_DIR / label / f"run-{run}"


def _next_run(label):
    base = RAW_DIR / label
    if not base.exists():
        return 1
    runs = sorted([
        int(p.name.split("-")[1])
        for p in base.iterdir()
        if p.is_dir() and p.name.startswith("run-")
    ])
    return (runs[-1] + 1) if runs else 1


def _existing_runs(label):
    base = RAW_DIR / label
    if not base.exists():
        return []
    return sorted([
        int(p.name.split("-")[1])
        for p in base.iterdir()
        if p.is_dir() and p.name.startswith("run-")
    ])


# ----------------------------------------------------------------------
# Prepare prompts
# ----------------------------------------------------------------------

def prepare_prompts(label, run=None):
    if run is None:
        run = _next_run(label)

    questions = load_questions()
    template = AGENT_TEMPLATE_FILE.read_text()

    run_dir = _run_dir(label, run)
    prompts_subdir = run_dir / "prompts"
    _ensure_under_tests(prompts_subdir)
    prompts_subdir.mkdir(parents=True, exist_ok=True)

    for qid, qdata in questions["questions"].items():
        output_path = run_dir / f"{qid}.json"
        prompt = template.format(
            qid=qid,
            question=qdata["text"],
            level=qdata["level"],
            output_path=str(output_path),
            vault_path=VAULT_PATH,
            repo_path=str(REPO_ROOT),
        )
        (prompts_subdir / f"{qid}.md").write_text(prompt)

    print(f"[OK] Prepared 20 prompts for {label} run-{run}")
    print(f"     Prompts dir: {prompts_subdir}")
    print(f"     Agent outputs will land in: {run_dir}/Q*.json")


def prepare_evaluator(label, run=None):
    if run is None:
        runs = _existing_runs(label)
        if not runs:
            print(f"[ERR] No runs found for {label}; run --prepare first")
            sys.exit(1)
        run = runs[-1]

    template = EVALUATOR_TEMPLATE_FILE.read_text()
    run_dir = _run_dir(label, run)
    if not run_dir.exists():
        print(f"[ERR] Run dir does not exist: {run_dir}")
        sys.exit(1)

    response_paths = "\n".join(
        f"   - {run_dir}/Q{i}.json" for i in range(1, 21)
    )
    output_path = run_dir / "evaluation.json"

    prompt = template.format(
        label=label,
        run=run,
        response_paths=response_paths,
        output_path=str(output_path),
        repo_path=str(REPO_ROOT),
        rubric_version=RUBRIC_VERSION,
    )

    evaluator_file = run_dir / "prompts" / "evaluator.md"
    evaluator_file.parent.mkdir(parents=True, exist_ok=True)
    evaluator_file.write_text(prompt)

    print(f"[OK] Prepared evaluator prompt for {label} run-{run}")
    print(f"     Prompt: {evaluator_file}")
    print(f"     Evaluation will land in: {output_path}")


# ----------------------------------------------------------------------
# Refinement (per-Q retry when any dim < threshold)
# ----------------------------------------------------------------------

def prepare_refinement(label, run=None, threshold=REFINE_DIM_THRESHOLD):
    """Generate refiner prompts for Qs that scored below threshold on any dim.

    Reads evaluation.json, identifies failing Qs, writes refiner prompts to
    run_dir/refine-prompts/Q*.md. The orchestrator (Claude) launches refiner
    agents in parallel; agents back up Q*.json -> Q*.original.json and write
    refined Q*.json. After refinement, re-run --prepare-evaluator and consolidate.
    """
    if run is None:
        runs = _existing_runs(label)
        if not runs:
            print(f"[ERR] No runs found for {label}")
            sys.exit(1)
        run = runs[-1]

    run_dir = _run_dir(label, run)
    eval_file = run_dir / "evaluation.json"
    if not eval_file.exists():
        print(f"[ERR] No evaluation.json at {eval_file}; run --prepare-evaluator first")
        sys.exit(1)

    eval_data = json.loads(eval_file.read_text())
    evaluator_notes = eval_data.get("evaluator_notes", "")

    # Identify failing Qs
    failing = []
    for qid, qeval in eval_data.get("evaluations", {}).items():
        failing_dims = {d: qeval.get(d) for d in RUBRIC if qeval.get(d, 10) < threshold}
        if failing_dims:
            failing.append((qid, qeval, failing_dims))

    if not failing:
        print(f"[OK] No Qs below threshold {threshold} for {label} run-{run} — no refinement needed")
        return

    template = REFINER_TEMPLATE_FILE.read_text()
    refine_dir = run_dir / "refine-prompts"
    _ensure_under_tests(refine_dir)
    refine_dir.mkdir(parents=True, exist_ok=True)

    questions = load_questions()
    prepared = []

    for qid, qeval, failing_dims in failing:
        q_file = run_dir / f"{qid}.json"
        if not q_file.exists():
            print(f"[WARN] {q_file} missing, skipping {qid}")
            continue
        original = json.loads(q_file.read_text())
        qtext = questions["questions"][qid]["text"]
        qlevel = questions["questions"][qid]["level"]

        failing_dims_str = "\n".join(
            f"  - {d}: {score}/10 (umbral: {threshold})"
            for d, score in failing_dims.items()
        )
        violations_str = "\n".join(f"  - {v}" for v in qeval.get("violations", []))

        prompt = template.format(
            qid=qid,
            question=qtext,
            level=qlevel,
            original_response=original.get("response", ""),
            original_atoms=", ".join(original.get("atoms_cited", [])),
            original_sources=", ".join(original.get("sources_cited", [])),
            failing_dims=failing_dims_str,
            violations=violations_str,
            evaluator_notes=qeval.get("notes", evaluator_notes),
            output_path=str(q_file),
            original_path=str(q_file.with_suffix(".original.json")),
            vault_path=VAULT_PATH,
            repo_path=str(REPO_ROOT),
        )

        # Backup original BEFORE refiner overwrites
        backup_path = q_file.with_suffix(".original.json")
        if not backup_path.exists():
            backup_path.write_text(q_file.read_text())

        prompt_path = refine_dir / f"{qid}.md"
        prompt_path.write_text(prompt)
        prepared.append((qid, list(failing_dims.keys())))

    print(f"[OK] Prepared {len(prepared)} refiner prompt(s) for {label} run-{run}")
    print(f"     Prompts dir: {refine_dir}")
    print(f"     Failing Qs:")
    for qid, dims in prepared:
        print(f"       {qid} -> dims to fix: {', '.join(dims)}")
    print()
    print(f"  Backup originals saved as Q*.original.json")
    print(f"  Refiner agents will OVERWRITE Q*.json with refined versions.")
    print()
    print(f"  Next steps:")
    print(f"    1. Launch {len(prepared)} refiner agent(s) in parallel (one per failing Q)")
    print(f"    2. python3 scripts/run-test-suite.py --prepare-evaluator --label {label} --run {run}")
    print(f"    3. Re-launch evaluator agent (re-evaluates all 20 Qs)")
    print(f"    4. python3 scripts/run-test-suite.py --consolidate --label {label}")


# ----------------------------------------------------------------------
# Consolidation (multi-run aware)
# ----------------------------------------------------------------------

def _estimate_output_tokens(response_text):
    return int(len(response_text) / SPANISH_CHARS_PER_TOKEN)


def _weighted_avg(scores):
    return round(sum(scores.get(d, 0) * c["weight"] for d, c in RUBRIC.items()), 3)


def _consolidate_one_run(label, run):
    """Returns per-run aggregate dict, or None if missing files."""
    run_dir = _run_dir(label, run)
    tokens_file = run_dir / "tokens.json"
    eval_file = run_dir / "evaluation.json"

    if not tokens_file.exists():
        return None
    tokens_data = json.loads(tokens_file.read_text())

    eval_data = None
    if eval_file.exists():
        eval_data = json.loads(eval_file.read_text())

    questions = load_questions()
    per_q = {}
    sums = {"input": 0, "output": 0, "weighted": 0, "latency": 0}
    dim_sums = {d: 0.0 for d in RUBRIC}
    wavg_sum = 0.0
    count = 0

    for qid in questions["questions"].keys():
        q_file = run_dir / f"{qid}.json"
        if not q_file.exists():
            continue
        if qid not in tokens_data:
            continue

        response = json.loads(q_file.read_text())
        total_tokens = tokens_data[qid].get("total_tokens", 0)
        latency_ms = tokens_data[qid].get("duration_ms", 0)
        if total_tokens == 0:
            continue

        response_text = response.get("response", "")
        output_tokens = _estimate_output_tokens(response_text)
        input_tokens = max(0, total_tokens - output_tokens)
        weighted_cost = input_tokens + (OUTPUT_TOKEN_WEIGHT * output_tokens)

        if eval_data and qid in eval_data.get("evaluations", {}):
            ev = eval_data["evaluations"][qid]
            scores = {d: float(ev.get(d, 0)) for d in RUBRIC}
            wavg = _weighted_avg(scores)
        else:
            sa = response.get("self_assessment", {})
            fb = float(sa.get("completeness", 0))
            scores = {d: fb for d in RUBRIC}
            wavg = fb

        per_q[qid] = {
            "level": response.get("level"),
            "weighted_cost": weighted_cost,
            "input_tokens": input_tokens,
            "output_tokens_estimated": output_tokens,
            "latency_ms": latency_ms,
            "quality": {**scores, "weighted_avg": wavg},
        }
        sums["input"] += input_tokens
        sums["output"] += output_tokens
        sums["weighted"] += weighted_cost
        sums["latency"] += latency_ms
        for d in RUBRIC:
            dim_sums[d] += scores[d]
        wavg_sum += wavg
        count += 1

    if count == 0:
        return None

    avg_dims = {d: dim_sums[d] / count for d in RUBRIC}
    return {
        "run": run,
        "n_questions": count,
        "evaluation_source": "external_evaluator" if eval_data else "self_assessment_fallback",
        "avg_input_tokens": sums["input"] / count,
        "avg_output_tokens": sums["output"] / count,
        "avg_weighted_cost": sums["weighted"] / count,
        "avg_latency_ms": sums["latency"] / count,
        "total_input_tokens": sums["input"],
        "total_output_tokens": sums["output"],
        "quality_avg": {**avg_dims, "weighted_avg": wavg_sum / count},
        "per_question": per_q,
    }


def _mean_se(values):
    """Returns (mean, standard_error). SE = std / sqrt(N), or 0 if N<2."""
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, 0.0
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    std = math.sqrt(var)
    return mean, std / math.sqrt(len(values))


def consolidate_results(label):
    runs = _existing_runs(label)
    if not runs:
        print(f"[ERR] No runs found for {label} under {RAW_DIR}/{label}/")
        sys.exit(1)

    per_run = []
    for r in runs:
        rd = _consolidate_one_run(label, r)
        if rd:
            per_run.append(rd)

    if not per_run:
        print(f"[ERR] All runs for {label} are incomplete (missing tokens/responses)")
        sys.exit(1)

    cost_vals = [r["avg_weighted_cost"] for r in per_run]
    cost_mean, cost_se = _mean_se(cost_vals)

    dim_means = {}
    dim_ses = {}
    for d in RUBRIC:
        vals = [r["quality_avg"][d] for r in per_run]
        m, se = _mean_se(vals)
        dim_means[d] = m
        dim_ses[d] = se
    wavg_vals = [r["quality_avg"]["weighted_avg"] for r in per_run]
    wavg_mean, wavg_se = _mean_se(wavg_vals)

    eval_sources = list({r["evaluation_source"] for r in per_run})
    overall_source = "external_evaluator" if all(
        r["evaluation_source"] == "external_evaluator" for r in per_run
    ) else "mixed_or_fallback"

    results = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rubric_version": RUBRIC_VERSION,
        "decision_version": DECISION_VERSION,
        "evaluation_source": overall_source,
        "evaluation_sources_per_run": eval_sources,
        "n_runs": len(per_run),
        "runs": per_run,
        "aggregated_metrics": {
            "n_runs": len(per_run),
            "avg_weighted_cost": {"mean": cost_mean, "se": cost_se},
            "quality": {
                **{d: {"mean": dim_means[d], "se": dim_ses[d]} for d in RUBRIC},
                "weighted_avg": {"mean": wavg_mean, "se": wavg_se},
            },
        },
    }

    output_file = RESULTS_DIR / f"{label}.json"
    _ensure_under_tests(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    print(f"[OK] Consolidated {len(per_run)} run(s) for {label} -> {output_file}")
    print(f"     Source: {overall_source}")
    print(f"     N runs: {len(per_run)}")
    print(f"     Cost (weighted, per Q):  {cost_mean:,.0f}  (SE {cost_se:,.0f})")
    print(f"     Quality (0-10):")
    for d, c in RUBRIC.items():
        print(f"       {d:20s} ({c['weight']*100:.0f}%): {dim_means[d]:.2f}  (SE {dim_ses[d]:.3f})")
    print(f"       {'WEIGHTED AVG':20s}      : {wavg_mean:.2f}  (SE {wavg_se:.3f})")


# ----------------------------------------------------------------------
# Comparison + Decision logic
# ----------------------------------------------------------------------

def _delta_pct(before, after):
    if before == 0:
        return 0.0
    return ((after - before) / before) * 100


def _composite(quality_before, quality_after, cost_before, cost_after):
    q_delta_norm = (quality_after - quality_before) / 10.0
    if cost_before == 0:
        c_delta_norm = 0.0
    else:
        c_delta_norm = (cost_before - cost_after) / cost_before
    composite = ALPHA * q_delta_norm + (1 - ALPHA) * c_delta_norm
    return {
        "alpha": ALPHA,
        "quality_delta_norm": round(q_delta_norm, 4),
        "cost_delta_norm": round(c_delta_norm, 4),
        "value": round(composite, 4),
    }


def _check_floors(before_q, after_q, meta):
    """Returns list of floor breaches (empty if all pass)."""
    breaches = []
    if after_q["weighted_avg"]["mean"] < FLOOR_WEIGHTED_AVG_ABS:
        breaches.append({
            "type": "weighted_avg_floor",
            "value": after_q["weighted_avg"]["mean"],
            "floor": FLOOR_WEIGHTED_AVG_ABS,
        })
    if after_q["accuracy"]["mean"] < FLOOR_ACCURACY_ABS:
        breaches.append({
            "type": "accuracy_floor",
            "value": after_q["accuracy"]["mean"],
            "floor": FLOOR_ACCURACY_ABS,
        })
    for d in RUBRIC:
        delta_abs = after_q[d]["mean"] - before_q[d]["mean"]
        if delta_abs < -FLOOR_ANY_DIM_DROP_ABS:
            breaches.append({
                "type": "any_dim_drop",
                "dim": d,
                "delta_abs": round(delta_abs, 3),
                "tolerance": -FLOOR_ANY_DIM_DROP_ABS,
            })
    for d in meta.get("target_dims", []):
        delta_abs = after_q[d]["mean"] - before_q[d]["mean"]
        if delta_abs < -TARGET_DIM_DROP_TOLERANCE:
            breaches.append({
                "type": "target_dim_regression",
                "dim": d,
                "delta_abs": round(delta_abs, 3),
            })
    return breaches


def _significance(delta_abs, se_before, se_after, n_runs):
    """Returns dict with 95% CI on delta and significance flag."""
    pooled_se = math.sqrt(se_before ** 2 + se_after ** 2)
    if pooled_se == 0:
        return {
            "delta_abs": round(delta_abs, 4),
            "pooled_se": 0.0,
            "ci95_low": round(delta_abs, 4),
            "ci95_high": round(delta_abs, 4),
            "significant": n_runs > 1,
            "n_runs": n_runs,
        }
    ci_half = 1.96 * pooled_se
    return {
        "delta_abs": round(delta_abs, 4),
        "pooled_se": round(pooled_se, 4),
        "ci95_low": round(delta_abs - ci_half, 4),
        "ci95_high": round(delta_abs + ci_half, 4),
        "significant": (delta_abs - ci_half > 0) or (delta_abs + ci_half < 0),
        "n_runs": n_runs,
    }


def _classify_deltas(before_q, after_q, meta, n_runs_min):
    """Returns dict with per-dim deltas + categorization (target/at_risk/neutral)."""
    target = set(meta.get("target_dims", []))
    at_risk = set(meta.get("at_risk_dims", []))
    out = {}
    for d in RUBRIC:
        b_mean = before_q[d]["mean"]
        a_mean = after_q[d]["mean"]
        b_se = before_q[d]["se"]
        a_se = after_q[d]["se"]
        delta_abs = a_mean - b_mean
        category = "target" if d in target else ("at_risk" if d in at_risk else "neutral")
        sig = _significance(delta_abs, b_se, a_se, n_runs_min)
        predicted = meta.get("predicted_deltas", {}).get(d)
        delivery_pct = None
        if predicted is not None and predicted != 0:
            delivery_pct = round((delta_abs / predicted) * 100, 1)
        out[d] = {
            "before": round(b_mean, 3),
            "after": round(a_mean, 3),
            "delta_abs": round(delta_abs, 3),
            "delta_pct": round(_delta_pct(b_mean, a_mean), 2),
            "weight": RUBRIC[d]["weight"],
            "category": category,
            "predicted_delta_abs": predicted,
            "predicted_delivery_pct": delivery_pct,
            "significance": sig,
        }
    return out


def _decide(composite, floor_breaches, dim_analysis, meta, cost_delta_pct, cost_significance):
    """Return decision dict with action + reason chain."""
    reasons = []

    if floor_breaches:
        return {
            "action": "REVERT",
            "primary_reason": "hard_floor_breached",
            "reasons": [f"floor: {b['type']}" for b in floor_breaches],
            "composite": composite["value"],
        }

    target_dims = meta.get("target_dims", [])
    target_underperforming = []
    for d in target_dims:
        analysis = dim_analysis[d]
        predicted = analysis.get("predicted_delta_abs")
        if predicted is None or predicted == 0:
            continue
        delivered = analysis["delta_abs"]
        if predicted > 0:
            if delivered < predicted * REP_TARGET_DELIVERY_FRACTION:
                target_underperforming.append({
                    "dim": d,
                    "predicted": predicted,
                    "delivered": delivered,
                })

    if target_underperforming:
        return {
            "action": "ITERATE",
            "primary_reason": "target_dim_underperformed",
            "reasons": [
                f"{t['dim']}: predicted +{t['predicted']:.2f}, delivered {t['delivered']:+.2f}"
                for t in target_underperforming
            ],
            "composite": composite["value"],
        }

    if composite["value"] >= COMPOSITE_IMPLEMENT:
        return {
            "action": "IMPLEMENT",
            "primary_reason": "composite_positive",
            "reasons": [
                f"composite={composite['value']:+.4f} >= +{COMPOSITE_IMPLEMENT}",
                f"cost_delta_pct={cost_delta_pct:+.2f}%",
            ],
            "composite": composite["value"],
        }

    if composite["value"] <= COMPOSITE_REVERT:
        return {
            "action": "REVERT",
            "primary_reason": "composite_negative",
            "reasons": [
                f"composite={composite['value']:+.4f} <= {COMPOSITE_REVERT}",
                f"cost_delta_pct={cost_delta_pct:+.2f}%",
            ],
            "composite": composite["value"],
        }

    return {
        "action": "ITERATE",
        "primary_reason": "composite_borderline",
        "reasons": [
            f"composite={composite['value']:+.4f} in noise zone "
            f"({COMPOSITE_REVERT}, {COMPOSITE_IMPLEMENT})",
            "consider repetition or refining the optimization",
        ],
        "composite": composite["value"],
    }


def _check_repetition_needed(composite, dim_analysis, meta, n_runs, allow_repetition):
    """Decide whether to ask for another run."""
    if not allow_repetition:
        return {"should_repeat": False, "reason": "disabled in meta.yaml"}
    if n_runs >= REP_MAX_RUNS:
        return {"should_repeat": False, "reason": f"max runs ({REP_MAX_RUNS}) reached"}

    if abs(composite["value"]) < REP_COMPOSITE_NOISE:
        return {
            "should_repeat": True,
            "reason": (
                f"composite={composite['value']:+.4f} within noise zone "
                f"(±{REP_COMPOSITE_NOISE}); accumulate runs for statistical mean"
            ),
        }

    for d in meta.get("target_dims", []):
        a = dim_analysis[d]
        sig = a["significance"]
        if not sig["significant"] and n_runs > 1:
            return {
                "should_repeat": True,
                "reason": f"target_dim {d} delta not significant (CI95 includes 0)",
            }
        if abs(a["delta_abs"]) < 0.3 and n_runs == 1:
            return {
                "should_repeat": True,
                "reason": f"target_dim {d} small delta ({a['delta_abs']:+.2f}); needs replication",
            }

    return {"should_repeat": False, "reason": "decision is clear at current N"}


def compare_results(from_label, to_label):
    from_file = RESULTS_DIR / f"{from_label}.json"
    to_file = RESULTS_DIR / f"{to_label}.json"
    if not from_file.exists() or not to_file.exists():
        print(f"[ERR] Missing results for {from_label} or {to_label}")
        sys.exit(1)

    before = json.loads(from_file.read_text())
    after = json.loads(to_file.read_text())
    meta = load_meta(to_label)

    bm = before["aggregated_metrics"]
    am = after["aggregated_metrics"]

    cost_before_mean = bm["avg_weighted_cost"]["mean"]
    cost_after_mean = am["avg_weighted_cost"]["mean"]
    cost_before_se = bm["avg_weighted_cost"]["se"]
    cost_after_se = am["avg_weighted_cost"]["se"]
    cost_delta_pct = _delta_pct(cost_before_mean, cost_after_mean)
    n_runs_min = min(bm["n_runs"], am["n_runs"])

    cost_significance = _significance(
        cost_after_mean - cost_before_mean, cost_before_se, cost_after_se, n_runs_min
    )

    quality_before = bm["quality"]
    quality_after = am["quality"]
    dim_analysis = _classify_deltas(quality_before, quality_after, meta, n_runs_min)

    wavg_before = quality_before["weighted_avg"]["mean"]
    wavg_after = quality_after["weighted_avg"]["mean"]
    wavg_significance = _significance(
        wavg_after - wavg_before,
        quality_before["weighted_avg"]["se"],
        quality_after["weighted_avg"]["se"],
        n_runs_min,
    )

    composite = _composite(wavg_before, wavg_after, cost_before_mean, cost_after_mean)
    floor_breaches = _check_floors(quality_before, quality_after, meta)
    decision = _decide(composite, floor_breaches, dim_analysis, meta, cost_delta_pct, cost_significance)

    repetition = _check_repetition_needed(
        composite, dim_analysis, meta, am["n_runs"], meta.get("allow_repetition", True)
    )

    targeted_summary = []
    for d in meta.get("target_dims", []):
        a = dim_analysis[d]
        targeted_summary.append({
            "dim": d,
            "predicted_delta_abs": a["predicted_delta_abs"],
            "delivered_delta_abs": a["delta_abs"],
            "delivery_pct": a["predicted_delivery_pct"],
            "ci95": [a["significance"]["ci95_low"], a["significance"]["ci95_high"]],
            "significant": a["significance"]["significant"],
        })
    at_risk_summary = []
    for d in meta.get("at_risk_dims", []):
        a = dim_analysis[d]
        at_risk_summary.append({
            "dim": d,
            "delta_abs": a["delta_abs"],
            "delta_pct": a["delta_pct"],
            "predicted_delta_abs": a["predicted_delta_abs"],
            "ci95": [a["significance"]["ci95_low"], a["significance"]["ci95_high"]],
            "significant": a["significance"]["significant"],
        })

    summary_table = []
    summary_table.append({
        "metric": "weighted_cost",
        "before": round(cost_before_mean, 1),
        "after": round(cost_after_mean, 1),
        "delta_pct": round(cost_delta_pct, 2),
        "ci95": [cost_significance["ci95_low"], cost_significance["ci95_high"]],
        "significant": cost_significance["significant"],
    })
    for d in RUBRIC:
        a = dim_analysis[d]
        summary_table.append({
            "metric": f"quality.{d}",
            "category": a["category"],
            "before": a["before"],
            "after": a["after"],
            "delta_pct": a["delta_pct"],
            "delta_abs": a["delta_abs"],
            "predicted": a["predicted_delta_abs"],
            "delivery_pct": a["predicted_delivery_pct"],
            "ci95": [a["significance"]["ci95_low"], a["significance"]["ci95_high"]],
            "significant": a["significance"]["significant"],
        })
    summary_table.append({
        "metric": "quality.weighted_avg",
        "before": round(wavg_before, 3),
        "after": round(wavg_after, 3),
        "delta_pct": round(_delta_pct(wavg_before, wavg_after), 2),
        "delta_abs": round(wavg_after - wavg_before, 3),
        "ci95": [wavg_significance["ci95_low"], wavg_significance["ci95_high"]],
        "significant": wavg_significance["significant"],
    })
    summary_table.append({
        "metric": "composite",
        "value": composite["value"],
        "alpha": composite["alpha"],
        "components": {
            "quality_delta_norm": composite["quality_delta_norm"],
            "cost_delta_norm": composite["cost_delta_norm"],
        },
    })

    comparison = {
        "from": from_label,
        "to": to_label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rubric_version": RUBRIC_VERSION,
        "decision_version": DECISION_VERSION,
        "evaluation_source": after.get("evaluation_source"),
        "n_runs": {"from": bm["n_runs"], "to": am["n_runs"], "min": n_runs_min},
        "meta": {
            "label": meta["label"],
            "description": meta.get("description", ""),
            "optimization_type": meta.get("optimization_type", "legacy"),
            "target_dims": meta.get("target_dims", []),
            "at_risk_dims": meta.get("at_risk_dims", []),
            "neutral_dims": meta.get("neutral_dims", []),
            "predicted_deltas": meta.get("predicted_deltas", {}),
        },
        "metrics": {
            "cost": {
                "weighted_cost": {
                    "before": cost_before_mean,
                    "after": cost_after_mean,
                    "delta_pct": cost_delta_pct,
                    "significance": cost_significance,
                },
                "input_tokens_avg": {
                    "before": bm.get("avg_input_tokens", None),
                    "after": am.get("avg_input_tokens", None),
                },
                "output_tokens_avg": {
                    "before": bm.get("avg_output_tokens", None),
                    "after": am.get("avg_output_tokens", None),
                },
            },
            "quality": {
                **dim_analysis,
                "weighted_avg": {
                    "before": round(wavg_before, 3),
                    "after": round(wavg_after, 3),
                    "delta_abs": round(wavg_after - wavg_before, 3),
                    "delta_pct": round(_delta_pct(wavg_before, wavg_after), 2),
                    "significance": wavg_significance,
                },
            },
            "composite": composite,
        },
        "targeted_analysis": {
            "target_dims": targeted_summary,
            "at_risk_dims": at_risk_summary,
        },
        "floor_breaches": floor_breaches,
        "summary_table": summary_table,
        "decision": decision,
        "repetition_advice": repetition,
    }

    output_file = COMPARISONS_DIR / f"{to_label}-vs-{from_label}.json"
    _ensure_under_tests(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False))

    history_dir = COMPARISONS_DIR / "history"
    _ensure_under_tests(history_dir)
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / f"{to_label}-vs-{from_label}__n{am['n_runs']}.json"
    history_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False))

    print(f"\n[Comparison: {from_label} -> {to_label}]  (decision v{DECISION_VERSION})")
    print(f"  N runs: from={bm['n_runs']}  to={am['n_runs']}  (min for SE: {n_runs_min})")
    print(f"  Cost (weighted_cost):")
    print(f"    {cost_before_mean:,.0f} -> {cost_after_mean:,.0f}  ({cost_delta_pct:+.2f}%)  "
          f"sig={cost_significance['significant']}")
    print(f"  Quality (0-10):")
    for d, c in RUBRIC.items():
        a = dim_analysis[d]
        cat_tag = {"target": "[TARGET]", "at_risk": "[RISK]  ", "neutral": "[NEUT]  "}[a["category"]]
        sig = "*" if a["significance"]["significant"] else " "
        print(f"    {cat_tag} {d:20s} ({c['weight']*100:.0f}%): "
              f"{a['before']:.2f} -> {a['after']:.2f}  ({a['delta_abs']:+.2f}, {a['delta_pct']:+.2f}%) {sig}")
    print(f"            {'WEIGHTED AVG':20s}      : "
          f"{wavg_before:.2f} -> {wavg_after:.2f}  ({wavg_after-wavg_before:+.3f})")
    print(f"  Composite (alpha={ALPHA}): {composite['value']:+.4f}  "
          f"(q_norm {composite['quality_delta_norm']:+.4f} + c_norm {composite['cost_delta_norm']:+.4f})")
    if floor_breaches:
        print(f"  ⚠ FLOOR BREACHES: {len(floor_breaches)}")
        for b in floor_breaches:
            print(f"     - {b}")
    print(f"  Decision: {decision['action']}  ({decision['primary_reason']})")
    for r in decision["reasons"]:
        print(f"     - {r}")
    print(f"  Repetition: {'YES' if repetition['should_repeat'] else 'no'}  ({repetition['reason']})")
    print(f"  Saved: {output_file}")
    print(f"  History snapshot: {history_file}")


def check_repetition(from_label, to_label):
    """Exits 0 if no repetition needed, 1 if needed."""
    comp_file = COMPARISONS_DIR / f"{to_label}-vs-{from_label}.json"
    if not comp_file.exists():
        print(f"[ERR] No comparison file at {comp_file}; run --compare first")
        sys.exit(2)
    comp = json.loads(comp_file.read_text())
    rep = comp["repetition_advice"]
    if rep["should_repeat"]:
        print(f"REPEAT: {rep['reason']}")
        sys.exit(1)
    print(f"NO_REPEAT: {rep['reason']}")
    sys.exit(0)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Test Suite Orchestrator (multi-run + composite)")
    parser.add_argument("--vault", dest="vault", default=None,
                        help="Vault name or path (default: use config.yaml.active_vault or single bundle)")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--prepare-evaluator", action="store_true", dest="prepare_evaluator")
    parser.add_argument("--refine", action="store_true",
                        help="Generate refiner prompts for Qs with any dim < threshold")
    parser.add_argument("--refine-threshold", type=int, default=REFINE_DIM_THRESHOLD,
                        dest="refine_threshold",
                        help=f"Dim score below which a Q triggers refinement (default: {REFINE_DIM_THRESHOLD})")
    parser.add_argument("--consolidate", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--check-repetition", action="store_true", dest="check_repetition")
    parser.add_argument("--label")
    parser.add_argument("--run", type=int, default=None)
    parser.add_argument("--from", dest="from_label")
    parser.add_argument("--to", dest="to_label")
    args = parser.parse_args()

    # Initialize vault config after argparse so --vault flag is honored
    _init_vault_config(args.vault)

    if args.prepare:
        if not args.label:
            print("[ERR] --label required")
            sys.exit(1)
        prepare_prompts(args.label, args.run)
    elif args.prepare_evaluator:
        if not args.label:
            print("[ERR] --label required")
            sys.exit(1)
        prepare_evaluator(args.label, args.run)
    elif args.refine:
        if not args.label:
            print("[ERR] --label required")
            sys.exit(1)
        prepare_refinement(args.label, args.run, args.refine_threshold)
    elif args.consolidate:
        if not args.label:
            print("[ERR] --label required")
            sys.exit(1)
        consolidate_results(args.label)
    elif args.compare:
        if not args.from_label or not args.to_label:
            print("[ERR] --from and --to required")
            sys.exit(1)
        compare_results(args.from_label, args.to_label)
    elif args.check_repetition:
        if not args.from_label or not args.to_label:
            print("[ERR] --from and --to required")
            sys.exit(1)
        check_repetition(args.from_label, args.to_label)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
