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


def extract_json_blocks(text: str) -> list[dict]:
    """Extract JSON code blocks from markdown."""
    import json as _json
    blocks = []
    for match in re.finditer(r"```json\s*\n(.*?)```", text, re.DOTALL):
        try:
            blocks.append(_json.loads(match.group(1).strip()))
        except _json.JSONDecodeError:
            continue
    return blocks


def validate_review(review_path: Path) -> tuple[bool, list[str]]:
    """Run all validations on a review artifact."""
    content = review_path.read_text(encoding="utf-8")
    errors = []

    # Try to extract structured data from JSON blocks first
    json_blocks = extract_json_blocks(content)
    json_data = json_blocks[0] if json_blocks else {}

    # Check score — try JSON first, then markdown regex
    score = None
    if "score" in json_data:
        score = json_data["score"]
    else:
        score_match = re.search(r"Score\s*[:*]*\s*(\d{1,3})", content)
        if score_match:
            score = int(score_match.group(1))

    if score is None:
        errors.append("CRITICAL: No score found in review")
    elif score < 0 or score > 100:
        errors.append(f"CRITICAL: Score {score} out of range 0-100")

    # Check verdict — try JSON first, then markdown regex
    verdict = None
    if "verdict" in json_data:
        verdict = json_data["verdict"]
    else:
        verdict_match = re.search(r"Verdict\s*[:*]*\s*(PASS_WITH_NOTES|PASS|FAIL)", content)
        if verdict_match:
            verdict = verdict_match.group(1)

    if verdict is None:
        errors.append("CRITICAL: No valid verdict found (expected PASS, PASS_WITH_NOTES, or FAIL)")
    elif verdict not in ("PASS", "PASS_WITH_NOTES", "FAIL"):
        errors.append(f"CRITICAL: Invalid verdict '{verdict}' (expected PASS, PASS_WITH_NOTES, or FAIL)")

    # Check confidence — try JSON first, then markdown regex
    confidence = None
    if "confidence" in json_data:
        confidence = json_data["confidence"]
    else:
        conf_match = re.search(r"Confidence\s*[:*]*\s*(HIGH|MEDIUM|LOW)", content)
        if conf_match:
            confidence = conf_match.group(1)

    if confidence is None:
        errors.append("MEDIUM: No confidence level found")

    # Check findings — try JSON first, then markdown
    findings = json_data.get("findings", [])
    if findings:
        # Check for blocking findings in JSON
        blocking_findings = [f for f in findings if f.get("blocking")]
        for f in blocking_findings:
            fid = f.get("id", "?")
            ev = f.get("evidence_path")
            if not ev:
                errors.append(f"HIGH: Blocking finding {fid} has no evidence_path")
            elif not Path(ev).exists():
                # Check relative to repo root too
                repo_ev = Path(__file__).resolve().parent.parent / ev
                if not repo_ev.exists():
                    errors.append(f"HIGH: Blocking finding {fid} evidence_path not found: {ev}")
    else:
        # Markdown fallback
        if "Findings" not in content and "findings" not in content.lower():
            errors.append("MEDIUM: No findings section found")

        # Check for blocking findings in markdown
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

    # Check for Final Recommendation — try JSON first
    if "final_recommendation" in json_data:
        rec = json_data["final_recommendation"]
        if rec not in ("ACCEPT", "REPAIR", "ESCALATE", "REJECT"):
            errors.append(f"HIGH: Invalid final_recommendation '{rec}'")
    elif "Final Recommendation" not in content and "recommendation" not in content.lower():
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
