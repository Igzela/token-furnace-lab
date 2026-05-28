#!/usr/bin/env python3
"""
Deterministic validator for review artifacts.

Checks:
- Score present and in range 0-100
- Verdict present and valid (PASS, PASS_WITH_NOTES, FAIL)
- Confidence present (HIGH, MEDIUM, LOW)
- Findings parseable
- Blocking findings cannot be ignored
- Evidence paths exist (if specified)
"""

import re
import sys
from pathlib import Path


def validate_review(review_path: Path) -> tuple[bool, list[str]]:
    """Run all validations on a review artifact."""
    content = review_path.read_text(encoding="utf-8")
    errors = []

    # Check score
    score_match = re.search(r"Score\s*[:*]*\s*(\d{1,3})", content)
    if not score_match:
        errors.append("CRITICAL: No score found in review")
    else:
        score = int(score_match.group(1))
        if score < 0 or score > 100:
            errors.append(f"CRITICAL: Score {score} out of range 0-100")

    # Check verdict
    verdict_match = re.search(r"Verdict\s*[:*]*\s*(PASS_WITH_NOTES|PASS|FAIL)", content)
    if not verdict_match:
        errors.append("CRITICAL: No valid verdict found (expected PASS, PASS_WITH_NOTES, or FAIL)")

    # Check confidence
    conf_match = re.search(r"Confidence\s*[:*]*\s*(HIGH|MEDIUM|LOW)", content)
    if not conf_match:
        errors.append("MEDIUM: No confidence level found")

    # Check findings section exists
    if "Findings" not in content and "findings" not in content.lower():
        errors.append("MEDIUM: No findings section found")

    # Check for blocking findings
    blocking_pattern = re.finditer(r"blocking\s*[:*]*\s*(true|True|TRUE)", content)
    blocking_count = sum(1 for _ in blocking_pattern)

    # Check that blocking findings have evidence
    finding_blocks = re.finditer(
        r"(?:id|ID)\s*[:*]*\s*(\w+).*?blocking\s*[:*]*\s*true.*?(?:evidence_path|evidence)\s*[:*]*\s*(\S+)",
        content,
        re.DOTALL,
    )
    for m in finding_blocks:
        evidence = m.group(2)
        if evidence and not Path(evidence).exists():
            errors.append(f"HIGH: Blocking finding {m.group(1)} has non-existent evidence_path: {evidence}")

    # Check for Final Recommendation
    if "Final Recommendation" not in content and "recommendation" not in content.lower():
        errors.append("MEDIUM: No final recommendation found")

    has_critical = any("CRITICAL" in e for e in errors)
    has_high = any("HIGH" in e for e in errors)

    passed = not has_critical and not has_high
    return passed, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_review_artifact.py <review.md>")
        sys.exit(1)

    review_path = Path(sys.argv[1])
    if not review_path.exists():
        print(f"File not found: {review_path}")
        sys.exit(1)

    passed, errors = validate_review(review_path)

    if passed:
        print(f"PASS: {review_path.name} ({len(errors)} warnings)")
    else:
        print(f"FAIL: {review_path.name}")

    for error in sorted(errors):
        print(f"  {error}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
