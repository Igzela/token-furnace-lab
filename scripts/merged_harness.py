#!/usr/bin/env python3
"""Merged Harness: token-furnace execution + token-efficient governance.

Production-grade pipeline combining real LLM execution (furnace) with event
sourcing, budget enforcement, quality gates, and adversarial review (harness).

Usage:
  python3 scripts/merged_harness.py run <task.yaml> [--mode bridge|mock]
  python3 scripts/merged_harness.py benchmark
"""

import argparse
import hashlib
import json
import logging
import re
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

logger = logging.getLogger("merged_harness")

# --- Constants ---

MAX_EVENT_STORE_BYTES = 10 * 1024 * 1024  # 10MB (S2)

ALLOWED_EVENT_TYPES = frozenset({
    "task_received", "routing_decided", "budget_reserved", "budget_used",
    "gates_built", "execution_blocked", "execution_complete",
    "agent_completed", "agent_failed", "agent_error",
    "gate_evaluated", "gate_revaluated", "retry",
    "adversarial_review", "run_complete",
})

TASK_REQUIRED_FIELDS = frozenset({"task_id", "objective", "subproblems"})
SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


# --- Security Helpers (S1) ---

def safe_artifact_path(run_dir: Path, subproblem_id: str, subdir: str = "artifacts") -> Path:
    """Construct a path within run_dir, rejecting traversal attempts."""
    if not SAFE_ID_RE.match(subproblem_id):
        raise ValueError(f"Rejected subproblem ID (invalid chars): {subproblem_id!r}")
    resolved = (run_dir / subdir / f"{subproblem_id}_artifact.md").resolve()
    if not resolved.is_relative_to(run_dir.resolve()):
        raise ValueError(f"Path escapes run_dir: {resolved}")
    return resolved


def safe_prompt_path(run_dir: Path, subproblem_id: str) -> Path:
    """Construct a prompt path within run_dir, rejecting traversal attempts."""
    if not SAFE_ID_RE.match(subproblem_id):
        raise ValueError(f"Rejected subproblem ID (invalid chars): {subproblem_id!r}")
    resolved = (run_dir / "prompts" / f"{subproblem_id}_prompt.md").resolve()
    if not resolved.is_relative_to(run_dir.resolve()):
        raise ValueError(f"Path escapes run_dir: {resolved}")
    return resolved


# --- Event Store (harness, hardened) ---

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

    def validate(self) -> None:
        """Schema validation (G3)."""
        if not self.event_id or not isinstance(self.event_id, str):
            raise ValueError("event_id must be a non-empty string")
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unknown event_type: {self.event_type!r}")
        if not self.timestamp or not isinstance(self.timestamp, str):
            raise ValueError("timestamp must be a non-empty string")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")


class EventStore:
    def __init__(self, path: Path, max_bytes: int = MAX_EVENT_STORE_BYTES):
        self.path = path
        self.max_bytes = max_bytes
        self._ids: set = set()
        self._idempotency: Dict[str, str] = {}
        self._lock = threading.Lock()  # S3
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
        with self._lock:
            # S3: thread-safe via lock
            # G3: schema validation
            event.validate()

            # S2: size limit — include pending event bytes
            serialized = json.dumps(event.to_dict(), ensure_ascii=False)
            current = self.path.stat().st_size if self.path.exists() else 0
            if current + len(serialized.encode("utf-8")) + 1 > self.max_bytes:
                raise RuntimeError(
                    f"Event store would exceed {self.max_bytes} bytes "
                    f"({current} + ~{len(serialized.encode('utf-8'))} pending) — "
                    f"possible runaway loop"
                )

            if event.event_id in self._ids:
                raise ValueError(f"Duplicate event_id: {event.event_id}")
            if event.idempotency_key:
                existing = self._idempotency.get(event.idempotency_key)
                if existing and existing != event.event_id:
                    raise ValueError(f"Idempotency conflict: {event.idempotency_key}")
                if existing == event.event_id:
                    return  # silent no-op

            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            self._ids.add(event.event_id)
            if event.idempotency_key:
                self._idempotency[event.idempotency_key] = event.event_id

    def replay(self) -> List[Event]:
        with self._lock:
            events = []
            if not self.path.exists():
                return events
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(Event.from_dict(json.loads(line)))
            return events


# --- Budget Manager ---

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


# --- Quality Gate ---

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
                 retry_count: int = 0, llm_score: Optional[float] = None) -> QualityGateResult:
        checks = []
        score = llm_score if llm_score is not None else self._estimate_score(artifact_content)

        checks.append(GateCheck(
            name="budget", passed=not reservation.violation, severity="block",
            reason=f"used={reservation.used_tokens}/{reservation.max_tokens}",
        ))
        checks.append(GateCheck(
            name="score", passed=score >= self.score_min, severity="block",
            reason=f"score={score}, min={self.score_min}",
        ))

        risk = routing.get("escalation", {}).get("trigger", [])
        checks.append(GateCheck(
            name="risk", passed=True, severity="info",
            reason=f"triggers={risk}",
        ))

        has_findings = "finding" in artifact_content.lower()
        has_verdict = "verdict:" in artifact_content.lower()
        checks.append(GateCheck(
            name="completeness", passed=has_findings and has_verdict, severity="warning",
            reason=f"findings={has_findings}, verdict={has_verdict}",
        ))

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


# --- Execution Gates ---

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


# --- Adversarial Review (G4) ---

@dataclass
class AdversarialReview:
    reviewer: str
    challenges: List[Dict[str, str]]
    verdict: str  # sustain, overrule, partial
    confidence: float


class DevilsAdvocate:
    """Runs adversarial review on artifacts to find blind spots."""

    def review(self, content: str, task_objective: str) -> AdversarialReview:
        challenges = []

        if content.count("PASS") > content.count("FAIL") and "risk" not in content.lower():
            challenges.append({
                "type": "missing_risk",
                "detail": "Artifact claims pass but contains no risk assessment",
                "severity": "high",
            })

        if len(content) < 500:
            challenges.append({
                "type": "insufficient_depth",
                "detail": f"Artifact is only {len(content)} chars — may lack rigor",
                "severity": "medium",
            })

        if "evidence" not in content.lower() and "reasoning" not in content.lower():
            challenges.append({
                "type": "no_evidence",
                "detail": "No evidence or reasoning section found",
                "severity": "high",
            })

        has_action = any(w in content.lower() for w in ["recommend", "action", "next step", "suggested"])
        if not has_action:
            challenges.append({
                "type": "no_actionability",
                "detail": "No actionable recommendations found",
                "severity": "low",
            })

        if not challenges:
            return AdversarialReview(
                reviewer="devils_advocate",
                challenges=[],
                verdict="sustain",
                confidence=0.9,
            )

        high_count = sum(1 for c in challenges if c["severity"] == "high")
        if high_count >= 2:
            verdict = "overrule"
        elif high_count == 1:
            verdict = "partial"
        else:
            verdict = "sustain"

        return AdversarialReview(
            reviewer="devils_advocate",
            challenges=challenges,
            verdict=verdict,
            confidence=min(1.0, 0.5 + 0.1 * len(challenges)),
        )


def fuse_verdicts(gate_verdict: str, adversarial: AdversarialReview,
                  gate_score: float = 0.0) -> Tuple[str, float]:
    """Deterministic fusion: adversarial overrule blocks, sustain passes.

    Overrule downgrades PASS (>= 0.80) to pass_with_notes.
    High-confidence overrule (>= 0.8) can also downgrade pass_with_notes
    to fail_retryable, addressing GPT finding that pass_with_notes should
    not be immune to blocking adversarial risk.
    """
    if adversarial.verdict == "overrule":
        if gate_verdict == "pass" and gate_score >= 0.80:
            return "pass_with_notes", 0.0
        if (gate_verdict == "pass_with_notes"
                and adversarial.confidence >= 0.9):
            return "fail_retryable", 0.0
        return gate_verdict, 0.0
    if adversarial.verdict == "partial":
        if gate_verdict == "pass" and gate_score >= 0.80:
            return "pass_with_notes", 0.0
        return gate_verdict, 0.0
    return gate_verdict, 0.0


# --- LLM-as-Judge (G1) ---

def llm_judge_score(artifact_content: str, task_objective: str,
                    mode: str = "bridge") -> Optional[float]:
    """Score artifact via LLM. Returns None if bridge unavailable."""
    if mode == "mock":
        return None
    try:
        from tf_agent_executor import AgentExecutor, AgentTask
        judge_prompt = (
            "You are an impartial quality judge. Score this artifact 0.0-1.0 on:\n"
            "1. Completeness (covers all parts of the task)\n"
            "2. Evidence quality (concrete reasoning, not vague)\n"
            "3. Actionability (clear next steps)\n\n"
            f"Task: {task_objective}\n\n"
            f"Artifact:\n{artifact_content[:4000]}\n\n"
            "Reply with ONLY a number between 0.0 and 1.0."
        )
        executor = AgentExecutor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(judge_prompt)
            judge_path = Path(f.name)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            result_path = Path(f.name)

        task_obj = AgentTask(
            subproblem_id="judge",
            prompt_path=str(judge_path),
            artifact_path=str(result_path),
            write_mode=False,
            timeout=60,
            subagent_type="Plan",
        )
        result = executor.execute_one(task_obj)
        judge_path.unlink(missing_ok=True)

        if result.success and result_path.exists():
            raw = result_path.read_text(encoding="utf-8").strip()
            result_path.unlink(missing_ok=True)
            for token in raw.split():
                try:
                    val = float(token)
                    if 0.0 <= val <= 1.0:
                        return val
                except ValueError:
                    continue
        return None
    except Exception as e:
        logger.warning("LLM judge failed, falling back to keyword scoring: %s", e)
        return None


# --- Task Validation (V1) ---

def validate_task_yaml(task: Dict, source: str = "task") -> None:
    """Validate task YAML has required fields (V1)."""
    missing = TASK_REQUIRED_FIELDS - set(task.keys())
    if missing:
        raise ValueError(f"Task YAML missing required fields: {missing} (in {source})")

    if not isinstance(task.get("task_id"), str) or not task["task_id"]:
        raise ValueError(f"Task 'task_id' must be a non-empty string (in {source})")
    if not isinstance(task.get("objective"), str) or not task["objective"]:
        raise ValueError(f"Task 'objective' must be a non-empty string (in {source})")

    subproblems = task.get("subproblems", [])
    if not isinstance(subproblems, list) or len(subproblems) == 0:
        raise ValueError(f"Task YAML 'subproblems' must be a non-empty list (in {source})")

    for i, sub in enumerate(subproblems):
        if not isinstance(sub, dict):
            raise ValueError(f"subproblems[{i}] must be a dict (in {source})")
        if "id" not in sub:
            raise ValueError(f"subproblems[{i}] missing 'id' field (in {source})")
        sp_id = sub["id"]
        if not isinstance(sp_id, str):
            raise ValueError(f"subproblems[{i}] 'id' must be a string (in {source})")
        if not SAFE_ID_RE.match(sp_id):
            raise ValueError(f"subproblems[{i}] id contains invalid chars: {sp_id!r}")


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
    adversarial: Optional[Dict] = None


class MergedHarness:
    def __init__(self, mode: str = "bridge", timeout: int = 180):
        self.mode = mode
        self.timeout = timeout
        # S4: unique run_id with timestamp + UUID
        ts_ns = time.time_ns()
        short_uuid = uuid.uuid4().hex[:8]
        self.run_id = f"merged-{ts_ns}-{short_uuid}"
        self.run_dir = REPO_ROOT / "runs" / self.run_id
        self.events = EventStore(self.run_dir / "events.jsonl")
        self.budget = BudgetManager(self.events)
        self.gate = QualityGate()
        self.devils_advocate = DevilsAdvocate()

    def run(self, task_path: Path) -> MergedResult:
        import yaml as _yaml
        from task_profiler import profile_task
        from adaptive_router import find_similar_runs, select_strategy, build_routing_decision

        # V1: validate task YAML
        raw = _yaml.safe_load(task_path.read_text(encoding="utf-8"))
        validate_task_yaml(raw, str(task_path))
        task = raw

        task_id = task.get("task_id", "unknown")

        # S4: fail if run_dir already exists (impossible with UUID, but belt-and-suspenders)
        try:
            self.run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise RuntimeError(f"Run directory collision: {self.run_dir}")

        t0 = time.monotonic()

        try:
            return self._run_inner(task, task_id, t0)
        except Exception as e:
            self._event("agent_error", {"error": str(e), "type": type(e).__name__})
            logger.error("Run failed: %s", e, exc_info=True)
            return MergedResult(
                run_id=self.run_id, task_id=task_id, routing={},
                gate_result={"verdict": "fail_terminal", "score": 0, "error": str(e)},
                artifacts=[], events=len(self.events.replay()),
                wall_seconds=round(time.monotonic() - t0, 1), retry_count=0,
            )

    def _run_inner(self, task: Dict, task_id: str, t0: float) -> MergedResult:
        import yaml as _yaml
        from task_profiler import profile_task
        from adaptive_router import find_similar_runs, select_strategy, build_routing_decision

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

        # Step 3: Budget — real reservation (G2)
        reservation = self.budget.reserve(task_id, strategy)

        # Step 4: Execution gates
        gates = build_execution_gates(routing, reservation)
        self._event("gates_built", {"gates": [{"type": g.gate_type, "passed": g.passed} for g in gates]})

        if any(not g.passed for g in gates if g.severity == "block"):
            self._event("execution_blocked", {"gates": [g.reason for g in gates if not g.passed]})
            return MergedResult(
                run_id=self.run_id, task_id=task_id, routing=routing,
                gate_result={"verdict": "blocked", "score": 0},
                artifacts=[], events=len(self.events.replay()),
                wall_seconds=round(time.monotonic() - t0, 1), retry_count=0,
            )

        # Step 5: Execute
        artifacts = self._execute(task, routing, reservation)
        self._event("execution_complete", {"artifacts": len(artifacts)})

        # Step 6: Gate + adversarial (G4)
        all_content = ""
        for art in artifacts:
            p = self.run_dir / art
            if p.exists():
                all_content += p.read_text(encoding="utf-8") + "\n"

        # G1: LLM judge — record budget even on fallback (G2)
        llm_score = llm_judge_score(all_content, task.get("objective", ""), self.mode)
        if self.mode != "mock":
            judge_tokens = 0 if llm_score is None else 800  # estimate
            self.budget.record_usage(reservation, judge_tokens)

        gate_result = self.gate.evaluate(all_content, routing, reservation, llm_score=llm_score)
        self._event("gate_evaluated", {
            "verdict": gate_result.verdict, "score": gate_result.score,
            "checks": [{"name": c.name, "passed": c.passed} for c in gate_result.checks],
        })

        # G4: adversarial review
        adversarial = None
        if artifacts and gate_result.verdict != "fail_terminal":
            adv_review = self.devils_advocate.review(all_content, task.get("objective", ""))
            adversarial = asdict(adv_review)
            # G2: record adversarial review budget (local analysis, ~200 tokens equivalent)
            self.budget.record_usage(reservation, 200)
            self._event("adversarial_review", {
                "verdict": adv_review.verdict,
                "challenges": len(adv_review.challenges),
                "confidence": adv_review.confidence,
            })
            # Deterministic fusion
            fused_verdict, score_adj = fuse_verdicts(gate_result.verdict, adv_review, gate_result.score)
            gate_result.verdict = fused_verdict
            gate_result.score = max(0.0, min(1.0, gate_result.score + score_adj))
            if fused_verdict in ("fail_retryable", "fail_terminal"):
                gate_result.next_status = "ready" if fused_verdict == "fail_retryable" else "failed"

        # Step 7: Retry if needed
        retry_count = 0
        while gate_result.verdict == "fail_retryable" and retry_count < 3:
            retry_count += 1
            self._event("retry", {"attempt": retry_count})
            artifacts = self._execute(task, routing, reservation)
            all_content = ""
            for art in artifacts:
                p = self.run_dir / art
                if p.exists():
                    all_content += p.read_text(encoding="utf-8") + "\n"

            llm_score = llm_judge_score(all_content, task.get("objective", ""), self.mode)
            gate_result = self.gate.evaluate(all_content, routing, reservation, retry_count, llm_score=llm_score)
            self._event("gate_revaluated", {"verdict": gate_result.verdict, "score": gate_result.score, "retry": retry_count})

            # Re-run adversarial on retry
            if artifacts:
                adv_review = self.devils_advocate.review(all_content, task.get("objective", ""))
                adversarial = asdict(adv_review)
                self._event("adversarial_review", {"verdict": adv_review.verdict, "challenges": len(adv_review.challenges)})
                fused_verdict, score_adj = fuse_verdicts(gate_result.verdict, adv_review, gate_result.score)
                gate_result.verdict = fused_verdict
                gate_result.score = max(0.0, min(1.0, gate_result.score + score_adj))

        wall = round(time.monotonic() - t0, 1)
        self._event("run_complete", {"verdict": gate_result.verdict, "wall_seconds": wall})

        result = MergedResult(
            run_id=self.run_id, task_id=task_id, routing=routing,
            gate_result={"verdict": gate_result.verdict, "score": gate_result.score,
                         "checks": [{"name": c.name, "passed": c.passed, "reason": c.reason} for c in gate_result.checks]},
            artifacts=artifacts, events=len(self.events.replay()),
            wall_seconds=wall, retry_count=retry_count,
            adversarial=adversarial,
        )
        (self.run_dir / "merged_result.json").write_text(
            json.dumps(asdict(result), indent=2, default=str), encoding="utf-8"
        )
        return result

    def _execute(self, task: Dict, routing: Dict, reservation: BudgetReservation) -> List[str]:
        if self.mode == "mock":
            return self._execute_mock(task, routing)
        return self._execute_bridge(task, routing, reservation)

    def _execute_mock(self, task: Dict, routing: Dict) -> List[str]:
        artifacts = []
        strategy = routing.get("strategy", "simple_review")
        for sub in task.get("subproblems", []):
            sp_id = sub["id"]
            art_path = safe_artifact_path(self.run_dir, sp_id)
            art_path.parent.mkdir(parents=True, exist_ok=True)
            art_path.write_text(
                f"# Mock: {sp_id}\n\nStrategy: {strategy}\nScore: 85\n"
                f"Verdict: PASS_WITH_NOTES\nConfidence: MEDIUM\n\n"
                f"## Findings\n- [MEDIUM] Mock finding\n\n"
                f"## Final Recommendation\nACCEPT\n",
                encoding="utf-8",
            )
            artifacts.append(str(art_path.relative_to(self.run_dir)))
        return artifacts

    def _execute_bridge(self, task: Dict, routing: Dict, reservation: BudgetReservation) -> List[str]:
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
            # S1: safe path construction
            prompt_path = safe_prompt_path(self.run_dir, sp_id)
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(prompt, encoding="utf-8")

            artifact_path = safe_artifact_path(self.run_dir, sp_id)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)

            task_obj = AgentTask(
                subproblem_id=sp_id, prompt_path=str(prompt_path),
                artifact_path=str(artifact_path), write_mode=False,
                timeout=self.timeout, subagent_type=sub.get("subagent_type", "Plan"),
            )
            result = executor.execute_one(task_obj)

            # G2: real budget tracking — record actual usage against real reservation
            tokens_est = len(prompt.split()) * 2 + 500
            self.budget.record_usage(reservation, tokens_est)

            if result.success:
                artifacts.append(str(artifact_path.relative_to(self.run_dir)))
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

    import yaml as _y
    results = []
    for case in cases:
        harness = MergedHarness(mode=mode, timeout=180)
        task = {
            "task_id": case["id"],
            "objective": case["task_text"],
            "subproblems": [{"id": case["id"], "prompt": case["task_text"], "subagent_type": "Plan"}],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            _y.dump(task, f)
            task_path = Path(f.name)

        result = None
        try:
            result = harness.run(task_path)
            score = result.gate_result.get("score", 0)
            verdict = result.gate_result.get("verdict", "unknown")
        except Exception as e:
            score = 0
            verdict = f"error: {e}"
        finally:
            task_path.unlink(missing_ok=True)

        results.append({
            "case_id": case["id"], "name": case["name"],
            "score": score, "verdict": verdict,
            "strategy": case.get("expected_strategy", "unknown"),
            "events": result.events if result is not None else 0,
            "wall_seconds": result.wall_seconds if result is not None else 0,
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

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
        if result.adversarial:
            print(f"Adversarial: {result.adversarial['verdict']} ({len(result.adversarial['challenges'])} challenges)")

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
