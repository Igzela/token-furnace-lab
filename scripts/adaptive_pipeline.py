#!/usr/bin/env python3
"""
Adaptive Pipeline: route → execute → gate → learn

Integration module that chains the existing orchestrator components into
a single adaptive pipeline. Uses adaptive routing to select execution
strategy, real agent execution via bridge, quality gate evaluation,
and automatic post-run learning.

Usage:
  python3 scripts/adaptive_pipeline.py run <task.yaml> [--mode bridge] [--write-mode]
"""

import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from task_profiler import profile_task
from adaptive_router import find_similar_runs, select_strategy, build_routing_decision
from routing_outcome_update import record_outcome
import orchestrator_learn


@dataclass
class PipelineResult:
    run_id: str
    routing_decision: Dict
    agent_results: Dict[str, Dict]
    gate_results: Dict[str, Dict]
    overall_verdict: str
    wall_seconds: float
    lessons: List[str] = field(default_factory=list)


class AdaptivePipeline:
    def __init__(self, mode: str = "bridge", write_mode: bool = False, timeout: int = 300):
        self.mode = mode
        self.write_mode = write_mode
        self.timeout = timeout

    def route(self, task: Dict) -> Dict:
        task_text = task.get("objective", task.get("title", ""))
        for sub in task.get("subproblems", []):
            task_text += " " + sub.get("prompt", "")

        profile = profile_task(task_text)
        similar = find_similar_runs(profile)
        strategy, rationale = select_strategy(profile, similar)
        decision = build_routing_decision(profile, similar, strategy, rationale)
        return decision

    def execute(self, task: Dict, routing: Dict, run_dir: Path) -> Dict[str, Dict]:
        from tf_agent_executor import AgentExecutor, AgentTask

        executor = AgentExecutor()
        results = {}
        agents = routing.get("agents", [])
        parallel = routing.get("execution", {}).get("parallel", False)

        tasks = []
        for sub in task.get("subproblems", []):
            prompt = self._make_prompt(task, sub, run_dir)
            prompt_path = run_dir / "prompts" / f"{sub['id']}_prompt.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(prompt, encoding="utf-8")

            artifact_path = run_dir / sub.get("artifact_path", f"artifacts/{sub['id']}_artifact.md")
            agent_task = AgentTask(
                subproblem_id=sub["id"],
                prompt_path=str(prompt_path),
                artifact_path=str(artifact_path),
                write_mode=self.write_mode,
                timeout=self.timeout,
                subagent_type=sub.get("subagent_type", "Plan"),
            )
            tasks.append(agent_task)

        if parallel and len(tasks) > 1:
            raw_results = executor.execute_parallel(tasks)
        else:
            raw_results = {}
            for t in tasks:
                r = executor.execute_one(t)
                raw_results[t.subproblem_id] = r

        for sp_id, r in raw_results.items():
            results[sp_id] = asdict(r) if hasattr(r, '__dataclass_fields__') else r

        return results

    def gate(self, task: Dict, agent_results: Dict[str, Dict], run_dir: Path) -> Dict[str, Dict]:
        gate_results = {}

        for sub in task.get("subproblems", []):
            sp_id = sub["id"]
            artifact_path = Path(agent_results.get(sp_id, {}).get("artifact_path", ""))
            success = agent_results.get(sp_id, {}).get("success", False)

            if not success or not artifact_path.exists():
                gate_results[sp_id] = {
                    "status": "REJECT",
                    "score": 0,
                    "reason": "artifact_missing or agent_failed",
                }
                continue

            content = artifact_path.read_text(encoding="utf-8")
            score = self._estimate_score(content)
            verdict = "PASS_WITH_NOTES" if score >= 70 else "FAIL"
            status = "ACCEPT" if score >= 80 and verdict in ("PASS", "PASS_WITH_NOTES") else "REPAIR"

            gate_results[sp_id] = {
                "status": status,
                "score": score,
                "verdict": verdict,
                "artifact_path": str(artifact_path),
            }

            gate_path = run_dir / "gate_results" / f"{sp_id}_gate.yaml"
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            with open(gate_path, "w", encoding="utf-8") as f:
                json.dump(gate_results[sp_id], f, indent=2)

        return gate_results

    def learn(self, task: Dict, routing: Dict, gate_results: Dict[str, Dict], run_dir: Path) -> List[str]:
        lessons = []
        statuses = [gr.get("status", "") for gr in gate_results.values()]
        all_accept = all(s == "ACCEPT" for s in statuses)
        any_reject = any(s in ("REJECT", "ESCALATE") for s in statuses)

        if all_accept:
            lessons.append(f"Strategy {routing.get('strategy', 'unknown')} produced all-accept results")
        elif any_reject:
            lessons.append(f"Strategy {routing.get('strategy', 'unknown')} produced reject/escalate results — consider alternative routing")

        for sp_id, gr in gate_results.items():
            if gr.get("score", 0) < 70:
                lessons.append(f"Low score ({gr['score']}) for {sp_id} — may need different agent type or more context")

        outcome = {
            "run_id": run_dir.name,
            "task_id": task.get("task_id", "unknown"),
            "task_type": routing.get("task_profile", {}).get("task_type", "review"),
            "strategy": routing.get("strategy", "unknown"),
            "gate_status": "ACCEPT" if all_accept else "REPAIR" if any_reject else "PARTIAL",
            "wall_seconds": sum(r.get("wall_seconds", 0) for r in agent_results.values()),
        }

        outcome_file = REPO_ROOT / "knowledge" / "orchestrator" / "outcome_memory.jsonl"
        outcome_file.parent.mkdir(parents=True, exist_ok=True)
        with open(outcome_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(outcome) + "\n")

        routing_file = REPO_ROOT / "knowledge" / "orchestrator" / "routing_memory.jsonl"
        with open(routing_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "run_id": run_dir.name,
                "strategy": routing.get("strategy"),
                "predicted_confidence": routing.get("confidence", 0),
                "actual_gate_result": "ACCEPT" if all_accept else "REPAIR",
                "success": all_accept,
            }) + "\n")

        return lessons

    def run(self, task_path: Path) -> PipelineResult:
        import yaml as _yaml
        task = _yaml.safe_load(task_path.read_text(encoding="utf-8"))

        run_id = f"adaptive-{int(time.time())}"
        run_dir = REPO_ROOT / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        print(f"=== Adaptive Pipeline: {run_id} ===")

        print("1. Routing...")
        routing = self.route(task)
        print(f"   Strategy: {routing.get('strategy', 'unknown')}")

        (run_dir / "routing_decision.json").write_text(
            json.dumps(routing, indent=2, default=str), encoding="utf-8"
        )

        print("2. Executing...")
        start = time.monotonic()
        agent_results = self.execute(task, routing, run_dir)
        wall = time.monotonic() - start
        print(f"   Completed in {wall:.1f}s")

        print("3. Gating...")
        gate_results = self.gate(task, agent_results, run_dir)
        all_accept = all(gr.get("status") == "ACCEPT" for gr in gate_results.values())
        overall = "PASS" if all_accept else "NEEDS_WORK"
        print(f"   Verdict: {overall}")

        print("4. Learning...")
        lessons = self.learn(task, routing, gate_results, run_dir)
        for lesson in lessons:
            print(f"   - {lesson}")

        result = PipelineResult(
            run_id=run_id,
            routing_decision=routing,
            agent_results=agent_results,
            gate_results=gate_results,
            overall_verdict=overall,
            wall_seconds=round(wall, 1),
            lessons=lessons,
        )

        (run_dir / "pipeline_result.json").write_text(
            json.dumps(asdict(result), indent=2, default=str), encoding="utf-8"
        )

        print(f"\n=== Result: {overall} ({wall:.1f}s) ===")
        print(f"Run dir: {run_dir}")
        return result

    def _make_prompt(self, task: Dict, sub: Dict, run_dir: Path) -> str:
        return f"""You are an AI agent working on a task.

## Task
{sub.get('prompt', task.get('objective', ''))}

## Scope
Work within: {', '.join(task.get('allowed_paths', ['runs/', 'knowledge/']))}
Do not modify: {', '.join(task.get('forbidden_paths', ['.env', 'secrets/']))}

## Output
Write your artifact to the specified path. Include structured claims with evidence.
"""

    def _estimate_score(self, content: str) -> int:
        score = 60
        if len(content) > 500:
            score += 10
        if len(content) > 2000:
            score += 5
        lower = content.lower()
        if "score:" in lower:
            score += 5
        if "verdict:" in lower:
            score += 5
        if "finding" in lower:
            score += 5
        if "evidence" in lower:
            score += 5
        if "blocking" in lower:
            score += 3
        return min(score, 95)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Adaptive Pipeline")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run adaptive pipeline")
    run_p.add_argument("task_yaml", type=Path)
    run_p.add_argument("--mode", choices=["queue", "mock", "command", "bridge"], default="bridge")
    run_p.add_argument("--write-mode", action="store_true")
    run_p.add_argument("--timeout", type=int, default=300)

    args = parser.parse_args()

    if args.command == "run":
        pipeline = AdaptivePipeline(mode=args.mode, write_mode=args.write_mode, timeout=args.timeout)
        pipeline.run(args.task_yaml)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
