#!/usr/bin/env python3
"""
Confidence Calibrator: synthetic confidence scoring and escalation reporting.

Computes a weighted confidence score from multiple sources and applies
decision policy rules to determine ACCEPT/REPAIR/ESCALATE/REJECT.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tf_orchestrator import Finding, Review, parse_review


# --- Confidence Score ---

@dataclass
class ConfidenceScore:
    reviewer_confidence: float  # 0-100, from reviewer's stated confidence
    evidence_quality: float  # 0-100, % of findings with valid evidence_path
    validator_agreement: float  # 0-100, validators pass = 100
    cross_reviewer_convergence: float  # 0-100, how much reviewers agree
    repair_history: float  # 0-100, based on repair rounds used
    total: float = 0.0
    level: str = "LOW"  # HIGH/MEDIUM/LOW

    def compute(self) -> "ConfidenceScore":
        weights = {
            "reviewer_confidence": 0.20,
            "evidence_quality": 0.25,
            "validator_agreement": 0.25,
            "cross_reviewer_convergence": 0.15,
            "repair_history": 0.15,
        }
        self.total = (
            self.reviewer_confidence * weights["reviewer_confidence"]
            + self.evidence_quality * weights["evidence_quality"]
            + self.validator_agreement * weights["validator_agreement"]
            + self.cross_reviewer_convergence * weights["cross_reviewer_convergence"]
            + self.repair_history * weights["repair_history"]
        )
        if self.total >= 80:
            self.level = "HIGH"
        elif self.total >= 60:
            self.level = "MEDIUM"
        else:
            self.level = "LOW"
        return self


def compute_confidence(reviews: List[Tuple[Review, str]],
                       validator_pass: bool = True,
                       repair_rounds: int = 0,
                       max_repair_rounds: int = 2) -> ConfidenceScore:
    """Compute synthetic confidence from multiple sources."""
    # Reviewer confidence
    conf_map = {"HIGH": 100, "MEDIUM": 60, "LOW": 30}
    reviewer_confs = [conf_map.get(r.confidence, 30) for r, _ in reviews]
    reviewer_confidence = sum(reviewer_confs) / len(reviewer_confs) if reviewer_confs else 30

    # Evidence quality
    total_findings = sum(len(r.findings) for r, _ in reviews)
    findings_with_evidence = sum(
        1 for r, _ in reviews for f in r.findings if f.evidence_path
    )
    evidence_quality = (findings_with_evidence / total_findings * 100) if total_findings else 100

    # Validator agreement
    validator_agreement = 100.0 if validator_pass else 0.0

    # Cross-reviewer convergence
    verdicts = [r.verdict for r, _ in reviews]
    if len(set(verdicts)) == 1:
        cross_convergence = 100.0
    elif len(set(verdicts)) <= 2:
        cross_convergence = 60.0
    else:
        cross_convergence = 20.0

    # Repair history
    if repair_rounds == 0:
        repair_history = 100.0
    elif repair_rounds < max_repair_rounds:
        repair_history = 70.0
    else:
        repair_history = 30.0

    score = ConfidenceScore(
        reviewer_confidence=reviewer_confidence,
        evidence_quality=evidence_quality,
        validator_agreement=validator_agreement,
        cross_reviewer_convergence=cross_convergence,
        repair_history=repair_history,
    )
    return score.compute()


# --- Decision Policy ---

@dataclass
class Decision:
    verdict: str  # ACCEPT, REPAIR, ESCALATE, REJECT
    reason: str
    confidence_level: str
    conditions_met: List[str]
    conditions_failed: List[str]


def classify_timeout_finding(finding: Finding, model_text: str) -> str:
    """Classify a timeout finding as repair/accept/escalate based on context."""
    claim = finding.claim.lower()

    # Check if the transition has explicit PWM action
    # Handle negations: "without pwm disable" is NOT a pwm disable
    has_pwm_disable = ("pwm disable" in claim or "pwm_disabled" in claim) and "without pwm disable" not in claim
    has_passive_coast = "passive_coast" in claim or "passive coast" in claim
    has_controlled_decel = "controlled_decel" in claim or "controlled decel" in claim

    # Check if source state is PWM-active
    is_pwm_active = ("running" in claim or "active" in claim) and "stopped" not in claim

    if is_pwm_active and not has_passive_coast and not has_controlled_decel and not has_pwm_disable:
        return "REPAIR"  # Implicit unsafe transition
    elif has_passive_coast or has_controlled_decel or has_pwm_disable:
        return "ACCEPT"  # Explicit safe transition
    else:
        return "REVIEW"  # Needs human review — ambiguous or unrecognized pattern


def evaluate_decision_policy(reviews: List[Tuple[Review, str]],
                             fused_findings: List[Finding],
                             validator_pass: bool = True,
                             repair_rounds: int = 0,
                             max_repair_rounds: int = 2,
                             budget_exhausted: bool = False) -> Decision:
    """Apply decision policy rules to determine gate decision."""
    conditions_met = []
    conditions_failed = []

    # Compute confidence
    confidence = compute_confidence(reviews, validator_pass, repair_rounds, max_repair_rounds)

    # Check ACCEPT conditions
    blocking = [f for f in fused_findings if f.blocking]
    all_verdicts_accept = all(
        r.verdict in ("PASS", "PASS_WITH_NOTES") for r, _ in reviews
    )

    if not blocking:
        conditions_met.append("no_blocking_findings")
    else:
        conditions_failed.append(f"{len(blocking)}_blocking_findings")

    if validator_pass:
        conditions_met.append("validators_pass")
    else:
        conditions_failed.append("validators_fail")

    if confidence.level in ("HIGH", "MEDIUM"):
        conditions_met.append(f"confidence_{confidence.level}")
    else:
        conditions_failed.append("confidence_LOW")

    # Check ESCALATE conditions
    if budget_exhausted and blocking:
        conditions_failed.append("budget_exhausted_with_blocking")
        return Decision(
            verdict="ESCALATE",
            reason=f"Budget exhausted with {len(blocking)} blocking findings open",
            confidence_level=confidence.level,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
        )

    # Check for safety-critical ambiguity
    high_findings = [f for f in fused_findings if f.severity in ("HIGH", "CRITICAL")]
    if high_findings and confidence.level == "LOW":
        return Decision(
            verdict="ESCALATE",
            reason=f"Safety-critical findings with LOW confidence",
            confidence_level=confidence.level,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
        )

    # Check for repeated same-class findings
    from collections import Counter
    severity_counts = Counter(f.severity for f in fused_findings)
    if severity_counts.get("LOW", 0) >= 3:
        # Multiple LOW findings may indicate systemic issue
        conditions_failed.append("repeated_low_findings")

    # Final decision
    blocking_conditions = [c for c in conditions_failed if "blocking" in c]
    hard_conditions = [c for c in conditions_failed
                       if c not in ("repeated_low_findings",) and "blocking" not in c]

    if blocking_conditions or hard_conditions:
        if blocking_conditions:
            if repair_rounds < max_repair_rounds:
                verdict = "REPAIR"
                reason = f"{len(blocking)} blocking findings"
            else:
                verdict = "ESCALATE"
                reason = f"{len(blocking)} blocking findings after {repair_rounds} rounds"
        elif "validators_fail" in conditions_failed:
            verdict = "REPAIR"
            reason = "Validator errors"
        elif "confidence_LOW" in conditions_failed and high_findings:
            verdict = "ESCALATE"
            reason = "Safety-critical findings with LOW confidence"
        elif "repeated_low_findings" in conditions_failed and not blocking_conditions:
            verdict = "ACCEPT"
            reason = f"All conditions met, confidence {confidence.level}, repeated LOW findings noted"
        else:
            verdict = "REPAIR"
            reason = "; ".join(conditions_failed)
    else:
        verdict = "ACCEPT"
        reason = f"All conditions met, confidence {confidence.level}"

    return Decision(
        verdict=verdict,
        reason=reason,
        confidence_level=confidence.level,
        conditions_met=conditions_met,
        conditions_failed=conditions_failed,
    )


# --- Escalation Report ---

@dataclass
class EscalationReport:
    reason: str
    unresolved_findings: List[Dict]
    evidence_paths: List[str]
    attempted_repairs: int
    decision_needed_from_human: str
    safe_default: str

    def to_markdown(self) -> str:
        lines = [
            "# Escalation Report",
            "",
            f"**Reason**: {self.reason}",
            f"**Attempted repairs**: {self.attempted_repairs}",
            f"**Safe default**: {self.safe_default}",
            "",
            "## Unresolved Findings",
            "",
        ]
        for f in self.unresolved_findings:
            lines.append(f"- **{f.get('id', '?')}** [{f.get('severity', '?')}]: {f.get('claim', '?')[:120]}")
        lines.extend([
            "",
            "## Evidence Paths",
            "",
        ])
        for p in self.evidence_paths:
            lines.append(f"- {p}")
        lines.extend([
            "",
            "## Decision Needed",
            "",
            self.decision_needed_from_human,
        ])
        return "\n".join(lines)


def generate_escalation_report(decision: Decision,
                               findings: List[Finding],
                               repair_rounds: int) -> EscalationReport:
    """Generate escalation report when gate decision is ESCALATE."""
    blocking = [f for f in findings if f.blocking]
    high = [f for f in findings if f.severity in ("HIGH", "CRITICAL")]

    unresolved = []
    evidence_paths = []
    for f in blocking + high:
        unresolved.append({
            "id": f.id,
            "severity": f.severity,
            "blocking": f.blocking,
            "claim": f.claim,
            "correction": f.correction,
        })
        if f.evidence_path:
            evidence_paths.append(f.evidence_path)

    return EscalationReport(
        reason=decision.reason,
        unresolved_findings=unresolved,
        evidence_paths=list(set(evidence_paths)),
        attempted_repairs=repair_rounds,
        decision_needed_from_human=(
            f"Review {len(unresolved)} unresolved findings and decide: "
            f"(a) accept with documented risk, (b) apply manual repair, "
            f"(c) reject and restart with different approach."
        ),
        safe_default="REJECT — do not accept artifact with unresolved safety-critical findings",
    )


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print("Usage: confidence_calibrator.py <review1.md> [review2.md] [...]")
        print("       confidence_calibrator.py --fused <fused_review.yaml>")
        sys.exit(1)

    if sys.argv[1] == "--fused":
        # Load fused review
        fused_path = Path(sys.argv[2])
        data = yaml.safe_load(fused_path.read_text(encoding="utf-8"))
        fused = data.get("fused_review", data)
        print(f"Fused gate: {fused.get('final_gate_decision')}")
        print(f"Scores: {fused.get('scores')}")
        print(f"Blocking: {fused.get('blocking_findings')}")
        return

    # Load reviews
    reviews = []
    for f in sys.argv[1:]:
        path = Path(f)
        if path.exists():
            review = parse_review(path.read_text(encoding="utf-8"))
            reviewer = "unknown"
            content = path.read_text(encoding="utf-8")
            json_blocks = re.findall(r"```json\s*\n(.*?)```", content, re.DOTALL)
            if json_blocks:
                try:
                    data = json.loads(json_blocks[0])
                    reviewer = data.get("reviewer_role", "unknown")
                except json.JSONDecodeError:
                    pass
            reviews.append((review, reviewer))
            print(f"Loaded: {path.name} (score={review.score}, verdict={review.verdict}, confidence={review.confidence})")

    if not reviews:
        print("No reviews loaded")
        sys.exit(1)

    # Compute confidence
    all_findings = [f for r, _ in reviews for f in r.findings]
    confidence = compute_confidence(reviews)
    decision = evaluate_decision_policy(reviews, all_findings)

    print(f"\n=== Confidence Score ===")
    print(f"Reviewer confidence: {confidence.reviewer_confidence:.0f}")
    print(f"Evidence quality: {confidence.evidence_quality:.0f}")
    print(f"Validator agreement: {confidence.validator_agreement:.0f}")
    print(f"Cross-reviewer convergence: {confidence.cross_reviewer_convergence:.0f}")
    print(f"Repair history: {confidence.repair_history:.0f}")
    print(f"Total: {confidence.total:.1f} ({confidence.level})")

    print(f"\n=== Decision ===")
    print(f"Verdict: {decision.verdict}")
    print(f"Reason: {decision.reason}")
    print(f"Conditions met: {decision.conditions_met}")
    print(f"Conditions failed: {decision.conditions_failed}")

    if decision.verdict == "ESCALATE":
        report = generate_escalation_report(decision, all_findings, 0)
        print(f"\n{report.to_markdown()}")


if __name__ == "__main__":
    main()
