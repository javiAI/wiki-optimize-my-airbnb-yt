#!/usr/bin/env python3
"""
Test Suite Orchestrator

Prepares and consolidates parallel test execution. Designed to be invoked by
Claude Code, which uses Agent tool to launch 20 parallel agents.

Usage:
  # Step 1: Prepare test prompts (creates 20 prompt files)
  python3 scripts/run-test-suite.py --prepare --label baseline

  # Step 2: Claude launches 20 Agent calls in parallel (one per question)
  # Each agent reads its prompt file, answers, writes response to:
  # $VAULT_PATH/meta/tests/raw-responses/{label}-Q{N}.json

  # Step 3: Consolidate results into single file
  # REQUIRES --tokens-file: JSON with {"Q1": {"total_tokens": N, "duration_ms": M}, ...}
  # Claude (orchestrator) writes this from observed Agent tool usage data BEFORE consolidate.
  python3 scripts/run-test-suite.py --consolidate --label baseline \\
      --tokens-file $VAULT_PATH/meta/tests/raw-responses/baseline-tokens.json

  # Step 4: Compare with previous (e.g., baseline vs O1)
  python3 scripts/run-test-suite.py --compare --from baseline --to O1
"""

import argparse
import json
import os
import shutil
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    "/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt"
)
TESTS_DIR = Path(VAULT_PATH) / "meta" / "tests"
RAW_DIR = TESTS_DIR / "raw-responses"
OPT_DIR = TESTS_DIR / "optimizations"

# Repo mirror: results are also copied here for visibility outside the vault
REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_RESULTS_DIR = REPO_ROOT / "test-results"

# Cost weighting: output tokens are 6x more expensive than input
OUTPUT_TOKEN_WEIGHT = 6

# Spanish chars per token (empirical avg for tactical/strategic responses)
SPANISH_CHARS_PER_TOKEN = 4.0


def load_questions():
    """Load 20 baseline questions from YAML"""
    with open(TESTS_DIR / "baseline-questions.yaml") as f:
        return yaml.safe_load(f)


def prepare_prompts(label):
    """
    Generate 20 isolated agent prompts.
    Each prompt contains:
    - Strict instructions to NOT access cache (vault/queries/)
    - Strict instructions to NOT use prior context
    - The question to answer
    - Expected output format
    """
    questions = load_questions()
    prompts_dir = TESTS_DIR / "prompts" / label
    prompts_dir.mkdir(parents=True, exist_ok=True)

    instructions = """Eres un agente de testing. Sigue estas instrucciones AL PIE DE LA LETRA:

REGLAS ABSOLUTAS:
1. NO accedas a vault/queries/ (caché de respuestas previas) — está PROHIBIDO
2. NO uses contexto de sesiones anteriores
3. NO leas otros archivos de prompts o respuestas
4. SOLO usa: CLAUDE.md, vault/index.md, vault/notes/, vault/MOC/, vault/sources/
5. Responde en ESPAÑOL como un consultor profesional
6. Sigue el response contract del CLAUDE.md §10.7

TU TAREA:
Responde la siguiente pregunta de un host de Airbnb/Booking:

PREGUNTA: {question}

OUTPUT FORMAT (JSON):
{{
  "question_id": "{qid}",
  "question": "{question}",
  "level": {level},
  "response": "<tu respuesta completa>",
  "atoms_cited": ["[[atom1]]", "[[atom2]]"],
  "sources_cited": ["[[source1]]", "[[source2]]"],
  "self_assessment": {{
    "confidence": "high|medium|low",
    "completeness": 1-10,
    "accuracy": 1-10
  }}
}}

Guarda el JSON en: {output_path}
"""

    for qid, qdata in questions["questions"].items():
        output_path = RAW_DIR / f"{label}-{qid}.json"
        prompt = instructions.format(
            qid=qid,
            question=qdata["text"],
            level=qdata["level"],
            output_path=str(output_path)
        )

        prompt_file = prompts_dir / f"{qid}.md"
        prompt_file.write_text(prompt)

    print(f"✅ Prepared 20 prompts in {prompts_dir}/")
    print(f"   Each prompt is isolated, no cache access, fresh context")
    print(f"\nNext: Claude must launch 20 Agent calls in parallel,")
    print(f"      one per question, reading each prompt file.")
    print(f"\nResults will be saved to: {RAW_DIR}/{label}-Q*.json")


def _load_tokens_file(tokens_file_path):
    """
    Load tokens manifest written by Claude after Agent tool runs.
    Schema:
      {
        "Q1": {"total_tokens": <int>, "duration_ms": <int>, "tool_uses": <int>},
        "Q2": {...},
        ...
      }
    """
    path = Path(tokens_file_path)
    if not path.exists():
        print(f"❌ Tokens file not found: {path}")
        print(f"   Claude must write this file from Agent tool usage data BEFORE consolidate.")
        print(f"   Schema: {{\"Q1\": {{\"total_tokens\": N, \"duration_ms\": M, \"tool_uses\": K}}, ...}}")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def _estimate_output_tokens(response_text):
    """Estimate output tokens from response chars (stable proxy across runs)"""
    return int(len(response_text) / SPANISH_CHARS_PER_TOKEN)


def consolidate_results(label, tokens_file):
    """
    After all 20 agents finish, consolidate raw-responses/{label}-Q*.json
    into a single results file with metrics.

    Token model (the Agent tool only reports total_tokens, not input/output split):
      - total_tokens: observed from Agent tool result (passed via --tokens-file)
      - output_tokens: estimated from response text length / SPANISH_CHARS_PER_TOKEN
                       (stable proxy — bias cancels across optimization comparisons)
      - input_tokens: max(0, total - output_estimate)
      - weighted_cost: input + 6 × output (matches user pricing requirement)
    """
    tokens_data = _load_tokens_file(tokens_file)
    questions = load_questions()
    results = {
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tokens_file": str(tokens_file),
        "questions": {},
        "aggregated_metrics": {}
    }

    total_input = 0
    total_output = 0
    total_weighted = 0
    total_quality = 0
    total_latency = 0
    count = 0
    missing_tokens = []

    for qid in questions["questions"].keys():
        raw_file = RAW_DIR / f"{label}-{qid}.json"
        if not raw_file.exists():
            print(f"⚠️  Missing response file: {raw_file}")
            continue

        if qid not in tokens_data:
            missing_tokens.append(qid)
            continue

        with open(raw_file) as f:
            response = json.load(f)

        total_tokens = tokens_data[qid].get("total_tokens", 0)
        latency_ms = tokens_data[qid].get("duration_ms", 0)
        tool_uses = tokens_data[qid].get("tool_uses", 0)

        if total_tokens == 0:
            missing_tokens.append(qid)
            continue

        response_text = response.get("response", "")
        output_tokens = _estimate_output_tokens(response_text)
        input_tokens = max(0, total_tokens - output_tokens)
        weighted_cost = input_tokens + (OUTPUT_TOKEN_WEIGHT * output_tokens)

        results["questions"][qid] = {
            "level": response.get("level"),
            "question": response.get("question"),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens_estimated": output_tokens,
            "weighted_cost": weighted_cost,
            "latency_ms": latency_ms,
            "tool_uses": tool_uses,
            "quality_score": response.get("self_assessment", {}).get("completeness", 0),
            "atoms_cited": len(response.get("atoms_cited", [])),
            "sources_cited": len(response.get("sources_cited", [])),
            "confidence": response.get("self_assessment", {}).get("confidence", "unknown"),
            "response_chars": len(response_text),
            "response_preview": response_text[:200]
        }

        total_input += input_tokens
        total_output += output_tokens
        total_weighted += weighted_cost
        total_quality += response.get("self_assessment", {}).get("completeness", 0)
        total_latency += latency_ms
        count += 1

    if missing_tokens:
        print(f"❌ Missing token data for: {', '.join(missing_tokens)}")
        print(f"   Cannot consolidate — token data is required for cost measurement.")
        sys.exit(1)

    if count > 0:
        results["aggregated_metrics"] = {
            "total_questions": count,
            "avg_total_tokens": total_input + total_output,
            "avg_input_tokens": total_input / count,
            "avg_output_tokens": total_output / count,
            "avg_weighted_cost": total_weighted / count,
            "avg_latency_ms": total_latency / count,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_weighted_cost": total_weighted,
            "avg_quality_score": total_quality / count,
            "by_level": _aggregate_by_level(results["questions"])
        }

    output_file = OPT_DIR / f"{label}-results.json" if label != "baseline" else TESTS_DIR / "baseline-results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Mirror to repo for out-of-vault visibility
    _mirror_to_repo(label, output_file, tokens_file)

    print(f"✅ Consolidated {count}/20 results → {output_file}")
    print(f"   Avg total tokens:   {(total_input + total_output) / count:,.0f}")
    print(f"   Avg weighted cost:  {results['aggregated_metrics']['avg_weighted_cost']:,.0f}  (input + 6×output)")
    print(f"   Avg quality score:  {results['aggregated_metrics']['avg_quality_score']:.2f}/10")
    print(f"   Avg latency:        {results['aggregated_metrics']['avg_latency_ms']:,.0f} ms")
    print(f"   Mirror in repo:     test-results/{label}/")


def _mirror_to_repo(label, results_file, tokens_file):
    """
    Copy consolidated results, tokens manifest, and per-question raw responses
    to the repo at test-results/<label>/ for out-of-vault visibility.
    """
    label_dir = REPO_RESULTS_DIR / label
    responses_dir = label_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(results_file, label_dir / "results.json")
    shutil.copy2(tokens_file, label_dir / "tokens.json")

    questions = load_questions()
    for qid in questions["questions"].keys():
        raw_file = RAW_DIR / f"{label}-{qid}.json"
        if raw_file.exists():
            shutil.copy2(raw_file, responses_dir / f"{qid}.json")


def _aggregate_by_level(questions):
    """Group metrics by difficulty level"""
    by_level = {1: [], 2: [], 3: [], 4: []}
    for qid, qdata in questions.items():
        level = qdata.get("level", 0)
        if level in by_level:
            by_level[level].append(qdata)

    summary = {}
    for level, items in by_level.items():
        if items:
            summary[f"level_{level}"] = {
                "count": len(items),
                "avg_weighted_cost": sum(q["weighted_cost"] for q in items) / len(items),
                "avg_quality": sum(q["quality_score"] for q in items) / len(items)
            }
    return summary


def compare_results(from_label, to_label):
    """Compare two test runs and produce diff + decision"""
    from_file = TESTS_DIR / "baseline-results.json" if from_label == "baseline" else OPT_DIR / f"{from_label}-results.json"
    to_file = OPT_DIR / f"{to_label}-results.json"

    with open(from_file) as f:
        before = json.load(f)
    with open(to_file) as f:
        after = json.load(f)

    before_metrics = before["aggregated_metrics"]
    after_metrics = after["aggregated_metrics"]

    cost_delta_pct = ((after_metrics["avg_weighted_cost"] - before_metrics["avg_weighted_cost"]) / before_metrics["avg_weighted_cost"]) * 100
    quality_delta_pct = ((after_metrics["avg_quality_score"] - before_metrics["avg_quality_score"]) / before_metrics["avg_quality_score"]) * 100 if before_metrics["avg_quality_score"] > 0 else 0

    # Decision logic
    decision = _decide(cost_delta_pct, quality_delta_pct)

    comparison = {
        "from": from_label,
        "to": to_label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "weighted_cost": {
                "before": before_metrics["avg_weighted_cost"],
                "after": after_metrics["avg_weighted_cost"],
                "delta_pct": cost_delta_pct,
                "direction": "improvement" if cost_delta_pct < 0 else "regression"
            },
            "quality_score": {
                "before": before_metrics["avg_quality_score"],
                "after": after_metrics["avg_quality_score"],
                "delta_pct": quality_delta_pct,
                "direction": "improvement" if quality_delta_pct > 0 else "regression"
            },
            "input_tokens_total": {
                "before": before_metrics["total_input_tokens"],
                "after": after_metrics["total_input_tokens"]
            },
            "output_tokens_total": {
                "before": before_metrics["total_output_tokens"],
                "after": after_metrics["total_output_tokens"]
            }
        },
        "decision": decision
    }

    output_file = OPT_DIR / f"{to_label}-comparison.json"
    with open(output_file, "w") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    # Mirror comparison to repo
    repo_label_dir = REPO_RESULTS_DIR / to_label
    repo_label_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_file, repo_label_dir / f"comparison-vs-{from_label}.json")

    print(f"\n📊 Comparison: {from_label} → {to_label}")
    print(f"   Weighted cost: {cost_delta_pct:+.1f}%  ({'✅ better' if cost_delta_pct < 0 else '❌ worse'})")
    print(f"   Quality:       {quality_delta_pct:+.1f}%  ({'✅ better' if quality_delta_pct > 0 else '❌ worse'})")
    print(f"   Decision:      {decision['action']}  ({decision['reason']})")
    print(f"\n   Saved: {output_file}")
    print(f"   Mirror: test-results/{to_label}/comparison-vs-{from_label}.json")


def _decide(cost_delta_pct, quality_delta_pct):
    """
    Decision matrix:
    - cost ↓, quality ↑      → IMPLEMENT
    - cost ↓, quality →      → IMPLEMENT
    - cost →, quality ↑      → IMPLEMENT
    - cost ↑, quality ↑↑     → IMPLEMENT (only if quality gain >> cost)
    - cost ↑, quality →      → ITERATE
    - cost ↑, quality ↓      → REVERT
    - cost →, quality ↓      → REVERT
    """
    cost_better = cost_delta_pct < -2  # >2% cost reduction
    cost_same = abs(cost_delta_pct) <= 2
    cost_worse = cost_delta_pct > 2

    quality_better = quality_delta_pct > 2
    quality_same = abs(quality_delta_pct) <= 2
    quality_worse = quality_delta_pct < -2

    if (cost_better or cost_same) and (quality_better or quality_same):
        return {"action": "IMPLEMENT", "reason": "cost improved or stable, quality maintained or improved"}

    if cost_worse and quality_better and quality_delta_pct > abs(cost_delta_pct) * 2:
        return {"action": "IMPLEMENT", "reason": "quality gain significantly outweighs cost"}

    if cost_worse and quality_same:
        return {"action": "ITERATE", "reason": "cost regressed without quality benefit; refine and retry"}

    if quality_worse:
        return {"action": "REVERT", "reason": "quality regression is unacceptable"}

    return {"action": "ITERATE", "reason": "ambiguous; manual review recommended"}


def main():
    parser = argparse.ArgumentParser(description="Test Suite Orchestrator")
    parser.add_argument("--prepare", action="store_true", help="Generate prompts for parallel test execution")
    parser.add_argument("--consolidate", action="store_true", help="Consolidate raw responses into single results file")
    parser.add_argument("--compare", action="store_true", help="Compare two test runs")
    parser.add_argument("--label", help="Test run label (baseline, O1, O2, ...)")
    parser.add_argument("--tokens-file", dest="tokens_file", help="Path to JSON with per-question token data (required for --consolidate)")
    parser.add_argument("--from", dest="from_label", help="Source label for comparison")
    parser.add_argument("--to", dest="to_label", help="Target label for comparison")
    args = parser.parse_args()

    if args.prepare:
        if not args.label:
            print("❌ --label required (e.g., baseline, O1, O2, ...)")
            sys.exit(1)
        prepare_prompts(args.label)
    elif args.consolidate:
        if not args.label:
            print("❌ --label required")
            sys.exit(1)
        if not args.tokens_file:
            default_path = RAW_DIR / f"{args.label}-tokens.json"
            if default_path.exists():
                args.tokens_file = str(default_path)
            else:
                print(f"❌ --tokens-file required (or place it at {default_path})")
                print(f"   Schema: {{\"Q1\": {{\"total_tokens\": N, \"duration_ms\": M, \"tool_uses\": K}}, ...}}")
                sys.exit(1)
        consolidate_results(args.label, args.tokens_file)
    elif args.compare:
        if not args.from_label or not args.to_label:
            print("❌ --from and --to required")
            sys.exit(1)
        compare_results(args.from_label, args.to_label)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
