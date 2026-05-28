#!/usr/bin/env python3
"""Quality Gate Runner — enforces agent contracts and quality gates.

Validates artifacts against contracts, checks reviews, and determines
next action (ACCEPT / REPAIR / REJECT / ESCALATE).
"""

import json
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class GateStatus(Enum):
    ACCEPT = "ACCEPT"
    REPAIR = "REPAIR"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewFinding:
    severity: str
    category: str
    description: str
    evidence_path: Optional[str] = None
    fixed: bool = False

    @property
    def is_blocking(self) -> bool:
        return self.severity in ("high", "critical") and not self.fixed


@dataclass
class GateResult:
    status: GateStatus
    round: int
    score: Optional[int]
    verdict: Optional[str]
    blocking_findings: list
    scope_violations: list
    budget_status: dict
    next_action: dict
    reason: str


@dataclass
class Contract:
    version: str
    contract_id: str
    run_id: str
    parent_task_id: Optional[str]
    task: dict
    agent: dict
    artifact: dict
    review: dict
    quality_gate: dict
    budget: dict
    escalation: dict


def load_contract(contract_path: str) -> Contract:
    with open(contract_path) as f:
        data = yaml.safe_load(f)
    return Contract(**data)


def check_artifact_exists(contract: Contract, run_dir: Path) -> list[str]:
    errors = []
    artifact_path = run_dir / contract.artifact.get("file_path", "")
    if not artifact_path.exists():
        errors.append(f"Artifact not found: {artifact_path}")
    else:
        required_sections = contract.artifact.get("required_sections", [])
        content = artifact_path.read_text()
        for section in required_sections:
            if section.lower() not in content.lower():
                errors.append(f"Missing required section: {section}")
    return errors


def check_review_exists(contract: Contract, run_dir: Path) -> tuple[Optional[dict], list[str]]:
    errors = []
    review_path = run_dir / contract.review.get("review_output_path", "")
    if not review_path.exists():
        errors.append(f"Review not found: {review_path}")
        return None, errors

    content = review_path.read_text()
    review_data = parse_review(content)
    if review_data is None:
        errors.append("Could not parse review score/verdict")
    return review_data, errors


def parse_review(content: str) -> Optional[dict]:
    result = {}
    for line in content.split("\n"):
        line = line.strip()
        # Handle "## Score: 72/100 — PASS_WITH_NOTES"
        if "score:" in line.lower():
            try:
                score_str = line.split("Score:")[1].strip().split("/")[0].strip()
                result["score"] = int(score_str)
            except (ValueError, IndexError):
                pass
        # Handle "**Verdict**: PASS_WITH_NOTES" or "verdict: PASS"
        if "verdict" in line.lower():
            for v in ["PASS_WITH_NOTES", "PASS", "FAIL"]:
                if v in line:
                    result["verdict"] = v
                    break
    if "score" in result and "verdict" in result:
        return result
    return None


def parse_findings(content: str) -> list[ReviewFinding]:
    findings = []
    current = {}
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- severity:") or line.startswith("severity:"):
            if current:
                findings.append(ReviewFinding(**current))
            current = {"severity": "medium", "category": "general", "description": ""}
            try:
                current["severity"] = line.split(":")[1].strip()
            except IndexError:
                pass
        elif line.startswith("category:"):
            try:
                current["category"] = line.split(":")[1].strip()
            except IndexError:
                pass
        elif line.startswith("description:"):
            try:
                current["description"] = line.split(":", 1)[1].strip()
            except IndexError:
                pass
        elif line.startswith("evidence_path:"):
            try:
                current["evidence_path"] = line.split(":", 1)[1].strip()
            except IndexError:
                pass
        elif line.startswith("fixed:"):
            try:
                current["fixed"] = line.split(":")[1].strip().lower() == "true"
            except IndexError:
                pass
    if current:
        findings.append(ReviewFinding(**current))
    return findings


def check_scope_violations(contract: Contract, run_dir: Path) -> list[str]:
    violations = []
    allowed = contract.task.get("scope", {}).get("allowed_paths", [])
    forbidden = contract.task.get("scope", {}).get("forbidden_paths", [])
    if not allowed and not forbidden:
        return violations

    for path in run_dir.rglob("*"):
        if path.is_dir():
            continue
        rel = str(path.relative_to(run_dir.parent.parent))
        for f in forbidden:
            if rel.startswith(f):
                violations.append(f"Forbidden path changed: {rel}")
    return violations


def evaluate_gate(
    contract: Contract,
    run_dir: Path,
    round_num: int,
    max_repair_rounds: int,
) -> GateResult:
    gate = contract.quality_gate
    score_min = gate.get("score_min", 70)
    verdict_accept = gate.get("verdict_accept", ["PASS", "PASS_WITH_NOTES"])

    # Check artifact
    artifact_errors = check_artifact_exists(contract, run_dir)
    if artifact_errors:
        return GateResult(
            status=GateStatus.REJECT,
            round=round_num,
            score=None,
            verdict=None,
            blocking_findings=[],
            scope_violations=[],
            budget_status={"tokens_used": 0, "iterations_used": round_num},
            next_action={"type": "escalate", "reason": "missing_artifact"},
            reason="; ".join(artifact_errors),
        )

    # Check review
    review_data, review_errors = check_review_exists(contract, run_dir)
    if review_errors:
        return GateResult(
            status=GateStatus.REJECT,
            round=round_num,
            score=None,
            verdict=None,
            blocking_findings=[],
            scope_violations=[],
            budget_status={"tokens_used": 0, "iterations_used": round_num},
            next_action={"type": "escalate", "reason": "missing_review"},
            reason="; ".join(review_errors),
        )

    # Check scope
    scope_violations = check_scope_violations(contract, run_dir)
    if scope_violations:
        return GateResult(
            status=GateStatus.ESCALATE,
            round=round_num,
            score=review_data.get("score"),
            verdict=review_data.get("verdict"),
            blocking_findings=[],
            scope_violations=scope_violations,
            budget_status={"tokens_used": 0, "iterations_used": round_num},
            next_action={"type": "escalate", "reason": "scope_violation"},
            reason="; ".join(scope_violations),
        )

    # Parse findings
    review_path = run_dir / contract.review.get("review_output_path", "")
    findings = parse_findings(review_path.read_text())
    blocking = [f for f in findings if f.is_blocking]

    score = review_data.get("score", 0)
    verdict = review_data.get("verdict", "FAIL")

    # Decision logic
    if score < score_min:
        if round_num < max_repair_rounds:
            status = GateStatus.REPAIR
            reason = f"Score {score} < {score_min}"
        else:
            status = GateStatus.ESCALATE
            reason = f"Score {score} < {score_min} after {round_num} rounds"
    elif blocking:
        if round_num < max_repair_rounds:
            status = GateStatus.REPAIR
            reason = f"{len(blocking)} blocking findings remain"
        else:
            status = GateStatus.ESCALATE
            reason = f"{len(blocking)} blocking findings after {round_num} rounds"
    elif verdict in verdict_accept:
        status = GateStatus.ACCEPT
        reason = f"Score {score}, verdict {verdict}, no blocking findings"
    else:
        if round_num < max_repair_rounds:
            status = GateStatus.REPAIR
            reason = f"Verdict {verdict} not in {verdict_accept}"
        else:
            status = GateStatus.ESCALATE
            reason = f"Verdict {verdict} not in {verdict_accept} after {round_num} rounds"

    return GateResult(
        status=status,
        round=round_num,
        score=score,
        verdict=verdict,
        blocking_findings=[{"severity": f.severity, "description": f.description} for f in blocking],
        scope_violations=scope_violations,
        budget_status={"tokens_used": 0, "iterations_used": round_num},
        next_action={"type": status.value.lower(), "reason": reason},
        reason=reason,
    )


def gate_result_to_yaml(result: GateResult) -> str:
    data = {
        "status": result.status.value,
        "round": result.round,
        "score": result.score,
        "verdict": result.verdict,
        "blocking_findings": result.blocking_findings,
        "scope_violations": result.scope_violations,
        "budget_status": result.budget_status,
        "next_action": result.next_action,
        "reason": result.reason,
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def main():
    if len(sys.argv) < 3:
        print("Usage: quality_gate_runner.py <contract.yaml> <run_dir> [round_num]")
        sys.exit(1)

    contract_path = sys.argv[1]
    run_dir = Path(sys.argv[2])
    round_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    contract = load_contract(contract_path)
    max_repair = contract.quality_gate.get("max_repair_rounds", 2)

    result = evaluate_gate(contract, run_dir, round_num, max_repair)
    output = gate_result_to_yaml(result)
    print(output)

    # Write to file
    gate_dir = run_dir / "gate_results"
    gate_dir.mkdir(exist_ok=True)
    (gate_dir / f"gate_round_{round_num}.yaml").write_text(output)

    # Write event log
    events_file = run_dir / "events.jsonl"
    event = {
        "round": round_num,
        "status": result.status.value,
        "score": result.score,
        "verdict": result.verdict,
        "reason": result.reason,
    }
    with open(events_file, "a") as f:
        f.write(json.dumps(event) + "\n")

    sys.exit(0 if result.status == GateStatus.ACCEPT else 1)


if __name__ == "__main__":
    main()
