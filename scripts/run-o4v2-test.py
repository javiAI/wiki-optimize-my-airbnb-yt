#!/usr/bin/env python3
"""
O4v2 Custom Test Orchestrator

Custom test for O4v2 (smart contradiction resolver). Distinct from the standard
run-test-suite.py because:
  - Custom 15-question battery at tests/prompts/O4v2/questions.yaml
  - Custom agent template at tests/prompts/O4v2/_custom_agent_template.md
  - Custom evaluator with 6-dim rubric at _custom_evaluator_template.md
  - Pre/post comparison: O4v2-pre (current O4-simple state) vs O4v2-post (after upgrade)

Usage:
  python3 scripts/run-o4v2-test.py --prepare --label O4v2-pre [--run N]
  python3 scripts/run-o4v2-test.py --prepare-evaluator --label O4v2-pre [--run N]
  python3 scripts/run-o4v2-test.py --compare --pre O4v2-pre --post O4v2-post

The orchestrator (Claude) launches the 15 agents in parallel after --prepare.
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
PROMPTS_DIR = TESTS_DIR / "prompts" / "O4v2"
RAW_DIR = TESTS_DIR / "raw-responses"
COMPARISONS_DIR = TESTS_DIR / "comparisons"

QUESTIONS_FILE = PROMPTS_DIR / "questions.yaml"
AGENT_TEMPLATE = PROMPTS_DIR / "_custom_agent_template.md"
EVALUATOR_TEMPLATE = PROMPTS_DIR / "_custom_evaluator_template.md"
META_FILE = PROMPTS_DIR / "meta.yaml"

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    "/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt"
)

RUBRIC_WEIGHTS = {
    "conflict_detection": 0.20,
    "resolution_clarity": 0.25,
    "temporal_narrative": 0.20,
    "context_awareness": 0.15,
    "proposed_contradiction_quality": 0.15,
    "tone_format": 0.05,
}


def _ensure_under_tests(p: Path) -> Path:
    p = p.resolve()
    if not str(p).startswith(str(TESTS_DIR.resolve())):
        raise RuntimeError(f"Refusing to write outside tests/: {p}")
    return p


def next_run_num(label: str) -> int:
    label_dir = RAW_DIR / label
    if not label_dir.exists():
        return 1
    existing = [int(d.name.split("-")[1]) for d in label_dir.iterdir()
                if d.is_dir() and d.name.startswith("run-")]
    return (max(existing) + 1) if existing else 1


def load_questions():
    return yaml.safe_load(QUESTIONS_FILE.read_text(encoding="utf-8"))["questions"]


def render_template(template: str, **kwargs) -> str:
    out = template
    for k, v in kwargs.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def cmd_prepare(label: str, run: int):
    if run is None:
        run = next_run_num(label)
    run_dir = RAW_DIR / label / f"run-{run}"
    prompts_dir = PROMPTS_DIR / "runs" / label / f"run-{run}"
    _ensure_under_tests(run_dir)
    _ensure_under_tests(prompts_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    template = AGENT_TEMPLATE.read_text(encoding="utf-8")
    questions = load_questions()
    for q in questions:
        prompt = render_template(
            template,
            REPO=str(REPO_ROOT),
            VAULT=VAULT_PATH,
            LABEL=label,
            N=run,
            QID=q["id"],
            QUESTION=q["question"],
            CATEGORY=q["category"],
        )
        out_path = prompts_dir / f"{q['id']}.md"
        out_path.write_text(prompt, encoding="utf-8")

    print(json.dumps({
        "label": label,
        "run": run,
        "prompts_dir": str(prompts_dir),
        "raw_dir": str(run_dir),
        "n_questions": len(questions),
        "questions": [q["id"] for q in questions],
    }, indent=2))


def cmd_prepare_evaluator(label: str, run: int):
    if run is None:
        run = next_run_num(label) - 1  # use latest existing run
        if run < 1:
            print(f"ERROR: no run dir found for {label}", file=sys.stderr)
            sys.exit(1)
    run_dir = RAW_DIR / label / f"run-{run}"
    if not run_dir.exists():
        print(f"ERROR: run dir not found: {run_dir}", file=sys.stderr)
        sys.exit(1)

    eval_prompt_dir = PROMPTS_DIR / "runs" / label / f"run-{run}"
    eval_prompt_dir.mkdir(parents=True, exist_ok=True)
    template = EVALUATOR_TEMPLATE.read_text(encoding="utf-8")
    rendered = render_template(
        template,
        REPO=str(REPO_ROOT),
        VAULT=VAULT_PATH,
        LABEL=label,
        N=run,
    )
    out_path = eval_prompt_dir / "_evaluator.md"
    out_path.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "label": label,
        "run": run,
        "evaluator_prompt": str(out_path),
        "raw_dir": str(run_dir),
    }, indent=2))


def cmd_compare(pre_label: str, post_label: str):
    def latest_eval(label: str):
        label_dir = RAW_DIR / label
        runs = sorted([d for d in label_dir.iterdir() if d.is_dir() and d.name.startswith("run-")],
                      key=lambda d: int(d.name.split("-")[1]))
        if not runs:
            raise RuntimeError(f"No runs for {label}")
        eval_path = runs[-1] / "evaluation.json"
        return json.loads(eval_path.read_text(encoding="utf-8")), runs[-1].name

    pre, pre_run = latest_eval(pre_label)
    post, post_run = latest_eval(post_label)

    pre_agg = pre["aggregate"]
    post_agg = post["aggregate"]
    deltas = {dim: round(post_agg[dim] - pre_agg[dim], 3) for dim in RUBRIC_WEIGHTS}
    weighted_pre = pre_agg["weighted_avg"]
    weighted_post = post_agg["weighted_avg"]
    weighted_delta = round(weighted_post - weighted_pre, 3)

    meta = yaml.safe_load(META_FILE.read_text(encoding="utf-8"))
    impl_thresh = meta["decision_logic"]["implement_threshold"]
    iterate_thresh = meta["decision_logic"]["iterate_threshold"]

    floor_breach = []
    if deltas["conflict_detection"] <= -0.5:
        floor_breach.append("conflict_detection abs drop ≥ 0.5")
    if deltas["resolution_clarity"] <= -0.5:
        floor_breach.append("resolution_clarity abs drop ≥ 0.5")

    if floor_breach:
        decision = "REVERT"
        reason = "hard_floor_breached: " + "; ".join(floor_breach)
    elif weighted_delta >= impl_thresh:
        decision = "IMPLEMENT"
        reason = f"weighted_avg delta {weighted_delta:+.3f} ≥ {impl_thresh}"
    elif weighted_delta >= iterate_thresh:
        decision = "ITERATE"
        reason = f"weighted_avg delta {weighted_delta:+.3f} in [{iterate_thresh}, {impl_thresh})"
    else:
        decision = "REVERT"
        reason = f"weighted_avg delta {weighted_delta:+.3f} < {iterate_thresh}"

    out = {
        "comparison": f"{post_label}-vs-{pre_label}",
        "rubric_version": pre.get("rubric_version", "custom-o4v2-1.0"),
        "pre": {"label": pre_label, "run": pre_run, "aggregate": pre_agg},
        "post": {"label": post_label, "run": post_run, "aggregate": post_agg},
        "deltas": deltas,
        "weighted_delta": weighted_delta,
        "decision": decision,
        "reason": reason,
        "thresholds": {
            "implement": impl_thresh,
            "iterate": iterate_thresh,
            "floor_drop_per_target_dim": 0.5,
        },
    }

    COMPARISONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = COMPARISONS_DIR / f"{post_label}-vs-{pre_label}.json"
    _ensure_under_tests(out_path)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--prepare-evaluator", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--label")
    ap.add_argument("--run", type=int, default=None)
    ap.add_argument("--pre")
    ap.add_argument("--post")
    args = ap.parse_args()

    if args.prepare:
        if not args.label:
            ap.error("--prepare requires --label")
        cmd_prepare(args.label, args.run)
    elif args.prepare_evaluator:
        if not args.label:
            ap.error("--prepare-evaluator requires --label")
        cmd_prepare_evaluator(args.label, args.run)
    elif args.compare:
        if not (args.pre and args.post):
            ap.error("--compare requires --pre and --post")
        cmd_compare(args.pre, args.post)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
