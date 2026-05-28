#!/usr/bin/env python3
"""
Review Fusion: merge multiple review artifacts into a single fused gate decision.

Rules (from orchestration-005 spec):
1. Findings union, not average.
2. Any reviewer HIGH/CRITICAL blocking → final gate REPAIR/ESCALATE.
3. Score cannot cancel blocking findings.
4. Reviewer disagreements recorded explicitly.
5. Duplicate findings merged (same claim evidence → keep highest severity).
6. Unmentioned findings not auto-downgraded.
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


@dataclass
class FusedReview:
    scores: Dict[str, int]  # reviewer -> score
    verdicts: Dict[str, str]  # reviewer -> verdict
    merged_findings: List[Finding]  # deduplicated union
    blocking_findings: List[Finding]  # subset that are blocking
    reviewer_disagreements: List[str]  # human-readable disagreement descriptions
    confidence: str  # LOW/MEDIUM/HIGH — derived from reviewer agreement
    final_gate_decision: str  # ACCEPT/REPAIR/ESCALATE
    fusion_reason: str

    @property
    def score_min(self) -> int:
        return min(self.scores.values()) if self.scores else 0

    @property
    def score_max(self) -> int:
        return max(self.scores.values()) if self.scores else 0

    @property
    def score_avg(self) -> float:
        return sum(self.scores.values()) / len(self.scores) if self.scores else 0


def extract_json_blocks(text: str) -> List[Dict]:
    """Extract JSON code blocks from markdown."""
    blocks = []
    for match in re.finditer(r"```json\s*\n(.*?)```", text, re.DOTALL):
        try:
            blocks.append(json.loads(match.group(1).strip()))
        except json.JSONDecodeError:
            continue
    return blocks


def load_review(path: Path) -> Tuple[Review, str]:
    """Load a review from a markdown file. Returns (Review, reviewer_name)."""
    content = path.read_text(encoding="utf-8")
    review = parse_review(content)

    # Extract reviewer name from JSON or markdown
    json_blocks = extract_json_blocks(content)
    reviewer = "unknown"
    if json_blocks and "reviewer_role" in json_blocks[0]:
        reviewer = json_blocks[0]["reviewer_role"]
    else:
        reviewer_match = re.search(r"\*\*Reviewer\*\*\s*:\s*(\S+)", content)
        if reviewer_match:
            reviewer = reviewer_match.group(1)

    return review, reviewer


def _claim_signature(finding: Finding) -> str:
    """Create a signature for deduplication based on claim content."""
    # Normalize claim text for comparison
    claim = finding.claim.lower().strip()
    # Remove common filler words
    for word in ["the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "being", "have", "has", "had", "do", "does", "did", "will",
                 "would", "could", "should", "may", "might", "can", "shall",
                 "that", "this", "these", "those", "it", "its"]:
        claim = re.sub(rf"\b{word}\b", "", claim)
    claim = re.sub(r"\s+", " ", claim).strip()
    # Take first 80 chars as signature
    return claim[:80]


def merge_findings(all_findings: Dict[str, List[Finding]]) -> Tuple[List[Finding], List[str]]:
    """Merge findings from multiple reviewers. Returns (merged_findings, disagreements)."""
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    merged: Dict[str, Finding] = {}  # signature -> Finding
    disagreements: List[str] = []

    for reviewer, findings in all_findings.items():
        for f in findings:
            sig = _claim_signature(f)
            if sig in merged:
                existing = merged[sig]
                # Upgrade severity if new finding is higher
                new_sev = severity_order.get(f.severity, 0)
                old_sev = severity_order.get(existing.severity, 0)
                if new_sev > old_sev:
                    merged[sig] = Finding(
                        id=existing.id,
                        severity=f.severity,
                        blocking=existing.blocking or f.blocking,
                        status=existing.status,
                        evidence_path=existing.evidence_path or f.evidence_path,
                        claim=existing.claim,
                        correction=existing.correction,
                    )
                elif f.blocking and not existing.blocking:
                    merged[sig] = Finding(
                        id=existing.id,
                        severity=existing.severity,
                        blocking=True,
                        status=existing.status,
                        evidence_path=existing.evidence_path,
                        claim=existing.claim,
                        correction=existing.correction,
                    )
            else:
                merged[sig] = Finding(
                    id=f.id,
                    severity=f.severity,
                    blocking=f.blocking,
                    status=f.status,
                    evidence_path=f.evidence_path,
                    claim=f.claim,
                    correction=f.correction,
                )

    # Detect reviewer disagreements — same topic, different severity
    topic_findings: Dict[str, List[Tuple[str, Finding]]] = {}
    for reviewer, findings in all_findings.items():
        for f in findings:
            sig = _claim_signature(f)
            if sig not in topic_findings:
                topic_findings[sig] = []
            topic_findings[sig].append((reviewer, f))

    for sig, reviewer_findings in topic_findings.items():
        if len(reviewer_findings) > 1:
            severities = {r: f.severity for r, f in reviewer_findings}
            blocking_states = {r: f.blocking for r, f in reviewer_findings}
            if len(set(severities.values())) > 1:
                disagreements.append(
                    f"Severity disagreement on '{sig[:60]}...': {severities}"
                )
            if len(set(blocking_states.values())) > 1:
                disagreements.append(
                    f"Blocking disagreement on '{sig[:60]}...': {blocking_states}"
                )

    return list(merged.values()), disagreements


def fuse_reviews(reviews: List[Tuple[Review, str]], score_min: int = 80) -> FusedReview:
    """Fuse multiple reviews into a single gate decision."""
    scores = {}
    verdicts = {}
    all_findings: Dict[str, List[Finding]] = {}

    for review, reviewer in reviews:
        scores[reviewer] = review.score
        verdicts[reviewer] = review.verdict
        all_findings[reviewer] = review.findings

    merged_findings, disagreements = merge_findings(all_findings)
    blocking = [f for f in merged_findings if f.blocking]

    # Determine confidence from reviewer agreement
    verdict_values = list(verdicts.values())
    if len(set(verdict_values)) == 1:
        confidence = "HIGH"
    elif len(set(verdict_values)) <= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # Gate decision — priority: blocking > score > verdict
    reasons = []

    if blocking:
        reasons.append(f"{len(blocking)} blocking findings from merged reviews")
        decision = "REPAIR"
    elif any(s < score_min for s in scores.values()):
        low_scores = [f"{r}={s}" for r, s in scores.items() if s < score_min]
        reasons.append(f"Score below {score_min}: {', '.join(low_scores)}")
        decision = "REPAIR"
    elif any(v not in ("PASS", "PASS_WITH_NOTES") for v in verdicts.values()):
        bad_verdicts = [f"{r}={v}" for r, v in verdicts.items() if v not in ("PASS", "PASS_WITH_NOTES")]
        reasons.append(f"Non-accept verdicts: {', '.join(bad_verdicts)}")
        decision = "REPAIR"
    else:
        reasons.append("All reviewers PASS, no blocking findings")
        decision = "ACCEPT"

    if disagreements:
        reasons.append(f"{len(disagreements)} reviewer disagreements")

    return FusedReview(
        scores=scores,
        verdicts=verdicts,
        merged_findings=merged_findings,
        blocking_findings=blocking,
        reviewer_disagreements=disagreements,
        confidence=confidence,
        final_gate_decision=decision,
        fusion_reason="; ".join(reasons),
    )


def fused_to_yaml(fused: FusedReview) -> str:
    """Serialize fused review to YAML."""
    data = {
        "fused_review": {
            "scores": fused.scores,
            "verdicts": fused.verdicts,
            "score_range": {"min": fused.score_min, "max": fused.score_max, "avg": round(fused.score_avg, 1)},
            "final_gate_decision": fused.final_gate_decision,
            "confidence": fused.confidence,
            "blocking_findings": [
                {"id": f.id, "severity": f.severity, "claim": f.claim[:120]}
                for f in fused.blocking_findings
            ],
            "total_findings": len(fused.merged_findings),
            "reviewer_disagreements": fused.reviewer_disagreements,
            "fusion_reason": fused.fusion_reason,
        }
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def main():
    if len(sys.argv) < 3:
        print("Usage: review_fusion.py <review1.md> <review2.md> [...]")
        print("       review_fusion.py --dir <reviews_dir>")
        sys.exit(1)

    if sys.argv[1] == "--dir":
        reviews_dir = Path(sys.argv[2])
        review_files = sorted(reviews_dir.glob("*.md"))
    else:
        review_files = [Path(f) for f in sys.argv[1:]]

    if not review_files:
        print("No review files found")
        sys.exit(1)

    reviews = []
    for f in review_files:
        if f.exists():
            review, reviewer = load_review(f)
            reviews.append((review, reviewer))
            print(f"Loaded: {f.name} (reviewer={reviewer}, score={review.score}, verdict={review.verdict})")
        else:
            print(f"Warning: {f} not found, skipping")

    if len(reviews) < 2:
        print("Need at least 2 reviews to fuse")
        sys.exit(1)

    fused = fuse_reviews(reviews)
    print(f"\nFused gate decision: {fused.final_gate_decision}")
    print(f"Scores: {fused.scores}")
    print(f"Blocking findings: {len(fused.blocking_findings)}")
    print(f"Disagreements: {len(fused.reviewer_disagreements)}")

    # Write output
    output_path = review_files[0].parent.parent / "gate_results" / "fused_review.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(fused_to_yaml(fused), encoding="utf-8")
    print(f"\nFused review written to: {output_path}")


if __name__ == "__main__":
    main()
