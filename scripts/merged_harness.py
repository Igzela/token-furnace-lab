#!/usr/bin/env python3
"""Merged Harness: token-furnace execution + token-efficient governance.

Combines real LLM execution (furnace) with event sourcing, budget enforcement,
and quality gates (harness) into a single unified pipeline.

Usage:
  python3 scripts/merged_harness.py run <task.yaml> [--mode bridge|mock]
  python3 scripts/merged_harness.py benchmark
"""

import argparse
import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


# --- Event Store (from harness, simplified) ---

@dataclass
class Event:
    event_id: str
    event_type: str
    timestamp: str
    payload: Dict[str, Any]
    parent_event_id: Optional[str] = None
    idempotency_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class EventStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ids: set = set()
        self._idempotency: Dict[str, str] = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = Event.from_dict(json.loads(line))
            self._ids.add(ev.event_id)
            if ev.idempotency_key:
                self._idempotency[ev.idempotency_key] = ev.event_id

    def append(self, event: Event) -> None:
        if event.event_id in self._ids:
            raise ValueError(f"Duplicate event_id: {event.event_id}")
        if event.idempotency_key:
            existing = self._idempotency.get(event.idempotency_key)
            if existing and existing != event.event_id:
                raise ValueError(f"Idempotency conflict: {event.idempotency_key}")
            if existing == event.event_id:
                return  # silent no-op
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        self._ids.add(event.event_id)
        if event.idempotency_key:
            self._idempotency[event.idempotency_key] = event.event_id

    def replay(self) -> List[Event]:
        events = []
        if not self.path.exists():
            return events
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(Event.from_dict(json.loads(line)))
        return events


# --- Budget Manager (from harness, simplified) ---

@dataclass
class BudgetReservation:
    reservation_id: str
    task_id: str
    tier: str
    max_tokens: int
    used_tokens: int = 0
    status: str = "active"

    @property
    def remaining(self) -> int:
        return self.max_tokens - self.used_tokens

    @property
    def violation(self) -> bool:
        return self.used_tokens > self.max_tokens


TIER_BUDGETS = {
    "cheap_executor": 2000,
    "balanced_worker": 5000,
    "strong_planner": 10000,
    "adaptive": 8000,
    "simple_review": 5000,
    "cross_audit_review": 8000,
    "closed_loop_repair": 7000,
    "parallel_artifact_audit": 6000,
    "implementation_with_validators": 6000,
    "policy_application": 5000,
    "derivation_with_cross_audit": 10000,
}


class BudgetManager:
    def __init__(self, event_store: EventStore):
        self.store = event_store

    def reserve(self, task_id: str, tier: str) -> BudgetReservation:
        max_tokens = TIER_BUDGETS.get(tier, 5000)
        r = BudgetReservation(
            reservation_id=f"res-{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            tier=tier,
            max_tokens=max_tokens,
        )
        self.store.append(Event(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type="budget_reserved",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"reservation_id": r.reservation_id, "tier": tier, "max_tokens": max_tokens},
        ))
        return r

    def record_usage(self, reservation: BudgetReservation, tokens: int) -> None:
        reservation.used_tokens += tokens
        self.store.append(Event(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type="budget_used",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"reservation_id": reservation.reservation_id, "tokens": tokens, "remaining": reservation.remaining},
            parent_event_id=reservation.reservation_id,
        ))


# --- Quality Gate (from harness, adapted) ---

@dataclass
class GateCheck:
    name: str
    passed: bool
    severity: str  # info, warning, block
    reason: str


@dataclass
class QualityGateResult:
    checks: List[GateCheck]
    score: float
    verdict: str  # pass, pass_with_notes, fail_retryable, fail_terminal
    next_status: str  # done, ready, failed, blocked

    @property
    def ok(self) -> bool:
        return self.verdict in ("pass", "pass_with_notes")

    @property
    def has_blocking(self) -> bool:
        return any(not c.passed and c.severity == "block" for c in self.checks)


class QualityGate:
    def __init__(self, score_min: float = 0.75, retry_max: int = 3):
        self.score_min = score_min
        self.retry_max = retry_max

    def evaluate(self, artifact_content: str, routing: Dict, reservation: BudgetReservation,
                 retry_count: int = 0) -> QualityGateResult:
        checks = []
        score = self._estimate_score(artifact_content)

        # Budget check
        checks.append(GateCheck(
            name="budget", passed=not reservation.violation, severity="block",
            reason=f"used={reservation.used_tokens}/{reservation.max_tokens}",
        ))

        # Score check
        checks.append(GateCheck(
            name="score", passed=score >= self.score_min, severity="block",
            reason=f"score={score}, min={self.score_min}",
        ))

        # Risk check
        risk = routing.get("escalation", {}).get("trigger", [])
        checks.append(GateCheck(
            name="risk", passed=True, severity="info",
            reason=f"triggers={risk}",
        ))

        # Artifact completeness
        has_findings = "finding" in artifact_content.lower()
        has_verdict = "verdict:" in artifact_content.lower()
        checks.append(GateCheck(
            name="completeness", passed=has_findings and has_verdict, severity="warning",
            reason=f"findings={has_findings}, verdict={has_verdict}",
        ))

        # Determine verdict
        has_block = any(not c.passed and c.severity == "block" for c in checks)
        if has_block:
            if score >= 0.40 and retry_count < self.retry_max:
                verdict, next_status = "fail_retryable", "ready"
            else:
                verdict, next_status = "fail_terminal", "failed"
        elif score >= 0.80:
            verdict, next_status = "pass", "done"
        elif score >= 0.60:
            verdict, next_status = "pass_with_notes", "done"
        else:
            verdict, next_status = "fail_retryable", "ready"

        return QualityGateResult(checks=checks, score=score, verdict=verdict, next_status=next_status)

    def _estimate_score(self, content: str) -> float:
        score = 0.60
        if len(content) > 500:
            score += 0.10
        if len(content) > 2000:
            score += 0.05
        lower = content.lower()
        if "score:" in lower:
            score += 0.05
        if "verdict:" in lower:
            score += 0.05
        if "finding" in lower:
            score += 0.05
        if "evidence" in lower:
            score += 0.05
        if "blocking" in lower:
            score += 0.03
        return min(score, 0.95)


# --- Execution Gates (from harness) ---

@dataclass
class ExecutionGate:
    gate_type: str
    severity: str  # info, warning, block
    passed: bool
    reason: str


def build_execution_gates(routing: Dict, reservation: BudgetReservation) -> List[ExecutionGate]:
    gates = []
    risk = routing.get("escalation", {}).get("trigger", [])
    if "budget_violation" in risk:
        gates.append(ExecutionGate("budget", "block", False, "budget exceeded"))
    if reservation.violation:
        gates.append(ExecutionGate("budget", "block", False, f"used {reservation.used_tokens} > max {reservation.max_tokens}"))
    else:
        gates.append(ExecutionGate("budget", "info", True, "within budget"))
    gates.append(ExecutionGate("execution", "info", True, "bridge mode"))
    return gates


# --- Merged Pipeline ---

@dataclass
class MergedResult:
    run_id: str
    task_id: str
    routing: Dict
    gate_result: Dict
    artifacts: List[str]
    events: int
    wall_seconds: float
    retry_count: int


class MergedHarness:
    def __init__(self, mode: str = "bridge", timeout: int = 180):
        self.mode = mode
        self.timeout = timeout
        self.run_dir = REPO_ROOT / "runs" / f"merged-{int(time.time())}"
        self.events = EventStore(self.run_dir / "events.jsonl")
        self.budget = BudgetManager(self.events)
        self.gate = QualityGate()

    def run(self, task_path: Path) -> MergedResult:
        import yaml as _yaml
        from task_profiler import profile_task
        from adaptive_router import find_similar_runs, select_strategy, build_routing_decision

        task = _yaml.safe_load(task_path.read_text(encoding="utf-8"))
        task_id = task.get("task_id", "unknown")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.monotonic()

        # Step 1: Analyze
        self._event("task_received", {"task_id": task_id})
        task_text = task.get("objective", "")
        for sub in task.get("subproblems", []):
            task_text += " " + sub.get("prompt", "")
        profile = profile_task(task_text)

        # Step 2: Route
        similar = find_similar_runs(profile)
        strategy, rationale = select_strategy(profile, similar)
        routing = asdict(build_routing_decision(profile, strategy, similar, rationale))
        self._event("routing_decided", {"strategy": strategy, "rationale": rationale})

        # Step 3: Budget
        reservation = self.budget.reserve(task_id, strategy)

        # Step 4: Execution gates
        gates = build_execution_gates(routing, reservation)
        self._event("gates_built", {"gates": [{"type": g.gate_type, "passed": g.passed} for g in gates]})

        if any(not g.passed for g in gates if g.severity == "block"):
            self._event("execution_blocked", {"gates": [g.reason for g in gates if not g.passed]})
            return MergedResult(
                run_id=self.run_dir.name, task_id=task_id, routing=routing,
                gate_result={"verdict": "blocked", "score": 0},
                artifacts=[], events=len(self.events.replay()),
                wall_seconds=round(time.monotonic() - t0, 1), retry_count=0,
            )

        # Step 5: Execute
        artifacts = self._execute(task, routing)
        self._event("execution_complete", {"artifacts": len(artifacts)})

        # Step 6: Gate
        all_content = ""
        for art in artifacts:
            p = self.run_dir / art
            if p.exists():
                all_content += p.read_text(encoding="utf-8") + "\n"

        gate_result = self.gate.evaluate(all_content, routing, reservation)
        self._event("gate_evaluated", {
            "verdict": gate_result.verdict, "score": gate_result.score,
            "checks": [{"name": c.name, "passed": c.passed} for c in gate_result.checks],
        })

        # Step 7: Retry if needed
        retry_count = 0
        while gate_result.verdict == "fail_retryable" and retry_count < 3:
            retry_count += 1
            self._event("retry", {"attempt": retry_count})
            artifacts = self._execute(task, routing)
            all_content = ""
            for art in artifacts:
                p = self.run_dir / art
                if p.exists():
                    all_content += p.read_text(encoding="utf-8") + "\n"
            gate_result = self.gate.evaluate(all_content, routing, reservation, retry_count)
            self._event("gate_revaluated", {"verdict": gate_result.verdict, "score": gate_result.score, "retry": retry_count})

        wall = round(time.monotonic() - t0, 1)
        self._event("run_complete", {"verdict": gate_result.verdict, "wall_seconds": wall})

        # Write summary
        result = MergedResult(
            run_id=self.run_dir.name, task_id=task_id, routing=routing,
            gate_result={"verdict": gate_result.verdict, "score": gate_result.score,
                         "checks": [{"name": c.name, "passed": c.passed, "reason": c.reason} for c in gate_result.checks]},
            artifacts=artifacts, events=len(self.events.replay()),
            wall_seconds=wall, retry_count=retry_count,
        )
        (self.run_dir / "merged_result.json").write_text(
            json.dumps(asdict(result), indent=2, default=str), encoding="utf-8"
        )
        return result

    def _execute(self, task: Dict, routing: Dict) -> List[str]:
        if self.mode == "mock":
            return self._execute_mock(task, routing)
        return self._execute_bridge(task, routing)

    def _execute_mock(self, task: Dict, routing: Dict) -> List[str]:
        artifacts = []
        strategy = routing.get("strategy", "simple_review")
        for sub in task.get("subproblems", []):
            sp_id = sub["id"]
            art_path = f"artifacts/{sp_id}_artifact.md"
            p = self.run_dir / art_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                f"# Mock: {sp_id}\n\nStrategy: {strategy}\nScore: 85\n"
                f"Verdict: PASS_WITH_NOTES\nConfidence: MEDIUM\n\n"
                f"## Findings\n- [MEDIUM] Mock finding\n\n"
                f"## Final Recommendation\nACCEPT\n",
                encoding="utf-8",
            )
            artifacts.append(art_path)
        return artifacts

    def _execute_bridge(self, task: Dict, routing: Dict) -> List[str]:
        from tf_agent_executor import AgentExecutor, AgentTask

        executor = AgentExecutor()
        artifacts = []
        strategy = routing.get("strategy", "simple_review")

        for sub in task.get("subproblems", []):
            sp_id = sub["id"]
            prompt = (
                f"You are an AI agent. Task: {sub.get('prompt', task.get('objective', ''))}\n\n"
                f"## Strategy: {strategy}\n\n"
                f"## Required Format\n"
                f"Score: <0-100>\nVerdict: <PASS | PASS_WITH_NOTES | FAIL>\n"
                f"Confidence: <HIGH | MEDIUM | LOW>\n\n"
                f"## Findings\n- [severity] [description]\n\n"
                f"## Final Recommendation\n<ACCEPT | REPAIR | ESCALATE>\n"
            )
            prompt_path = self.run_dir / "prompts" / f"{sp_id}_prompt.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(prompt, encoding="utf-8")

            art_path = f"artifacts/{sp_id}_artifact.md"
            artifact_path = self.run_dir / art_path
            artifact_path.parent.mkdir(parents=True, exist_ok=True)

            task_obj = AgentTask(
                subproblem_id=sp_id, prompt_path=str(prompt_path),
                artifact_path=str(artifact_path), write_mode=False,
                timeout=self.timeout, subagent_type=sub.get("subagent_type", "Plan"),
            )
            result = executor.execute_one(task_obj)

            tokens_est = len(prompt.split()) * 2 + 500
            self.budget.record_usage(
                BudgetReservation("tmp", "tmp", strategy, 99999, tokens_est),
                tokens_est,
            )

            if result.success:
                artifacts.append(art_path)
                self._event("agent_completed", {"subproblem": sp_id, "wall": result.wall_seconds})
            else:
                self._event("agent_failed", {"subproblem": sp_id, "error": result.error})

        return artifacts

    def _event(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.events.append(Event(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        ))


# --- Self-Evaluation Benchmark ---

def run_benchmark(mode: str = "mock") -> Dict:
    cases_file = REPO_ROOT / "configs" / "self_eval_cases.yaml"
    import yaml as _yaml
    data = _yaml.safe_load(cases_file.read_text(encoding="utf-8"))
    cases = [c for c in data.get("cases", []) if c.get("small_task")]

    results = []
    for case in cases:
        harness = MergedHarness(mode=mode, timeout=180)
        task = {
            "task_id": case["id"],
            "objective": case["task_text"],
            "subproblems": [{"id": case["id"], "prompt": case["task_text"], "subagent_type": "Plan"}],
        }
        task_path = harness.run_dir / "task.yaml"
        harness.run_dir.mkdir(parents=True, exist_ok=True)
        import yaml as _y
        task_path.write_text(_y.dump(task), encoding="utf-8")

        try:
            result = harness.run(task_path)
            score = result.gate_result.get("score", 0)
            verdict = result.gate_result.get("verdict", "unknown")
        except Exception as e:
            score = 0
            verdict = f"error: {e}"

        results.append({
            "case_id": case["id"], "name": case["name"],
            "score": score, "verdict": verdict,
            "strategy": case.get("expected_strategy", "unknown"),
            "events": result.events if 'result' in dir() else 0,
            "wall_seconds": result.wall_seconds if 'result' in dir() else 0,
        })

    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    passed = sum(1 for r in results if r["verdict"] in ("pass", "pass_with_notes"))

    return {
        "total_cases": len(results),
        "avg_score": round(avg_score, 2),
        "passed": passed,
        "pass_rate": round(passed / len(results), 2) if results else 0,
        "per_case": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Merged Harness")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run merged pipeline")
    run_p.add_argument("task_yaml", type=Path)
    run_p.add_argument("--mode", choices=["bridge", "mock"], default="bridge")
    run_p.add_argument("--timeout", type=int, default=180)

    bench_p = sub.add_parser("benchmark", help="Run self-evaluation benchmark")
    bench_p.add_argument("--mode", choices=["bridge", "mock"], default="mock")

    args = parser.parse_args()

    if args.command == "run":
        harness = MergedHarness(mode=args.mode, timeout=args.timeout)
        result = harness.run(args.task_yaml)
        print(f"\n=== Merged Result: {result.gate_result['verdict']} ===")
        print(f"Score: {result.gate_result['score']}")
        print(f"Events: {result.events}")
        print(f"Wall: {result.wall_seconds}s")
        print(f"Retries: {result.retry_count}")
        print(f"Run dir: {harness.run_dir}")

    elif args.command == "benchmark":
        print("=== Merged Harness Benchmark ===\n")
        report = run_benchmark(mode=args.mode)
        for r in report["per_case"]:
            print(f"  {r['case_id']}: score={r['score']}, verdict={r['verdict']}, strategy={r['strategy']}")
        print(f"\n  Avg score: {report['avg_score']}")
        print(f"  Pass rate: {report['pass_rate']:.0%} ({report['passed']}/{report['total_cases']})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
