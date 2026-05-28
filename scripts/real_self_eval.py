#!/usr/bin/env python3
"""
Real Self-Evaluation Benchmark: compare adaptive vs baseline orchestrator
using actual LLM execution via the agent bridge.

Usage:
  python3 scripts/real_self_eval.py run    # Run real benchmark
"""

import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml as _yaml


@dataclass
class RealCaseResult:
    case_id: str
    name: str
    baseline: Dict
    adaptive: Dict
    delta: Dict


def load_cases() -> List[Dict]:
    cases_file = REPO_ROOT / "configs" / "self_eval_cases.yaml"
    if not cases_file.exists():
        return []
    data = _yaml.safe_load(cases_file.read_text(encoding="utf-8"))
    return [c for c in data.get("cases", []) if c.get("small_task", False)]


def execute_baseline(case: Dict, run_dir: Path) -> Dict:
    from tf_agent_executor import AgentExecutor, AgentTask

    task_text = case.get("task_text", case.get("name", ""))
    prompt = f"""You are reviewing the following task. Produce a structured review.

## Task
{task_text}

## Required Format
Score: <0-100>
Verdict: <PASS | PASS_WITH_NOTES | FAIL>
Confidence: <HIGH | MEDIUM | LOW>

## Findings
- [severity] [description]

## Final Recommendation
<ACCEPT | REPAIR | ESCALATE>
"""
    prompt_path = run_dir / f"{case['id']}_baseline_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    artifact_path = run_dir / f"{case['id']}_baseline_artifact.md"

    executor = AgentExecutor()
    task = AgentTask(
        subproblem_id=f"{case['id']}_baseline",
        prompt_path=str(prompt_path),
        artifact_path=str(artifact_path),
        write_mode=False,
        timeout=180,
    )

    start = time.monotonic()
    result = executor.execute_one(task)
    wall = time.monotonic() - start

    score = 0
    if result.success and artifact_path.exists():
        content = artifact_path.read_text(encoding="utf-8")
        score = _extract_score(content)

    return {
        "success": result.success,
        "score": score,
        "wall_seconds": round(wall, 1),
        "error": result.error,
    }


def execute_adaptive(case: Dict, run_dir: Path) -> Dict:
    from tf_agent_executor import AgentExecutor, AgentTask
    from task_profiler import profile_task
    from adaptive_router import find_similar_runs, select_strategy

    task_text = case.get("task_text", case.get("name", ""))
    profile = profile_task(task_text)
    similar = find_similar_runs(profile)
    strategy, rationale = select_strategy(profile, similar)

    prompt = f"""You are reviewing the following task. Produce a structured review.

## Task
{task_text}

## Strategy Selected: {strategy}
## Rationale: {rationale}

## Required Format
Score: <0-100>
Verdict: <PASS | PASS_WITH_NOTES | FAIL>
Confidence: <HIGH | MEDIUM | LOW>

## Findings
- [severity] [description]

## Final Recommendation
<ACCEPT | REPAIR | ESCALATE>
"""
    prompt_path = run_dir / f"{case['id']}_adaptive_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    artifact_path = run_dir / f"{case['id']}_adaptive_artifact.md"

    executor = AgentExecutor()
    task = AgentTask(
        subproblem_id=f"{case['id']}_adaptive",
        prompt_path=str(prompt_path),
        artifact_path=str(artifact_path),
        write_mode=False,
        timeout=180,
    )

    start = time.monotonic()
    result = executor.execute_one(task)
    wall = time.monotonic() - start

    score = 0
    if result.success and artifact_path.exists():
        content = artifact_path.read_text(encoding="utf-8")
        score = _extract_score(content)

    route_correct = strategy == case.get("expected_strategy", "simple_review")

    return {
        "success": result.success,
        "score": score,
        "wall_seconds": round(wall, 1),
        "strategy": strategy,
        "route_correct": route_correct,
        "error": result.error,
    }


def _extract_score(content: str) -> int:
    import re
    match = re.search(r'[Ss]core:\s*(\d+)', content)
    if match:
        return int(match.group(1))
    score = 60
    if len(content) > 500:
        score += 10
    lower = content.lower()
    if "verdict:" in lower:
        score += 5
    if "finding" in lower:
        score += 5
    if "evidence" in lower:
        score += 5
    return min(score, 95)


def run_benchmark() -> List[RealCaseResult]:
    cases = load_cases()
    if not cases:
        print("No small_task cases found in self_eval_cases.yaml")
        return []

    results = []
    run_dir = REPO_ROOT / "runs" / "orchestration-013" / "20260528-real-benchmark"
    run_dir.mkdir(parents=True, exist_ok=True)

    for case in cases:
        print(f"\n--- {case['id']}: {case['name']} ---")
        print("  Running baseline...")
        baseline = execute_baseline(case, run_dir)
        print(f"  Baseline: score={baseline['score']}, success={baseline['success']}")

        print("  Running adaptive...")
        adaptive = execute_adaptive(case, run_dir)
        print(f"  Adaptive: score={adaptive['score']}, success={adaptive['success']}, strategy={adaptive.get('strategy', 'N/A')}")

        delta = {
            "score_delta": adaptive["score"] - baseline["score"],
            "wall_time_delta": baseline["wall_seconds"] - adaptive["wall_seconds"],
        }

        results.append(RealCaseResult(
            case_id=case["id"],
            name=case["name"],
            baseline=baseline,
            adaptive=adaptive,
            delta=delta,
        ))

    return results


def generate_report(results: List[RealCaseResult]) -> Dict:
    if not results:
        return {"verdict": "NO_CASES", "reason": "No cases executed"}

    baseline_scores = [r.baseline["score"] for r in results if r.baseline["success"]]
    adaptive_scores = [r.adaptive["score"] for r in results if r.adaptive["success"]]

    baseline_avg = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0
    adaptive_avg = sum(adaptive_scores) / len(adaptive_scores) if adaptive_scores else 0

    route_correct = sum(1 for r in results if r.adaptive.get("route_correct", False))
    route_accuracy = route_correct / len(results) if results else 0

    adaptive_false = sum(1 for r in results
                         if r.adaptive["success"] and r.baseline["success"]
                         and r.adaptive["score"] >= 80 and r.baseline["score"] < 50)

    pass_criteria = {
        "cases_executed_gte_3": len(results) >= 3,
        "adaptive_score_gte_baseline": adaptive_avg >= baseline_avg,
        "route_accuracy_gte_80": route_accuracy >= 0.80,
        "adaptive_false_accept_0": adaptive_false == 0,
    }

    return {
        "total_cases": len(results),
        "baseline_avg_score": round(baseline_avg, 1),
        "adaptive_avg_score": round(adaptive_avg, 1),
        "score_delta": round(adaptive_avg - baseline_avg, 1),
        "route_accuracy": round(route_accuracy, 2),
        "adaptive_false_accept": adaptive_false,
        "verdict": "PASS" if all(pass_criteria.values()) else "FAIL",
        "pass_criteria": pass_criteria,
        "per_case": [asdict(r) for r in results],
    }


def main(action: str = "run"):
    if not action and len(sys.argv) >= 2:
        action = sys.argv[1]

    if action == "run":
        print("=== Real Self-Evaluation Benchmark ===\n")
        results = run_benchmark()
        report = generate_report(results)

        results_dir = REPO_ROOT / "runs" / "orchestration-013" / "20260528-real-benchmark"
        results_dir.mkdir(parents=True, exist_ok=True)
        (results_dir / "real_benchmark_report.json").write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )

        print("\n=== Summary ===")
        print(f"Cases: {report.get('total_cases', 0)}")
        print(f"Baseline avg: {report.get('baseline_avg_score', 0)}")
        print(f"Adaptive avg: {report.get('adaptive_avg_score', 0)}")
        print(f"Score delta: {report.get('score_delta', 0)}")
        print(f"Route accuracy: {report.get('route_accuracy', 0):.0%}")
        print(f"Verdict: {report.get('verdict', 'UNKNOWN')}")
        print(f"Pass criteria: {report.get('pass_criteria', {})}")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
