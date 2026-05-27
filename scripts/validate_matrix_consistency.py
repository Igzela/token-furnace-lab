#!/usr/bin/env python3
"""Validate matrix YAML consistency.

Checks:
1. summary.total_cases == actual cases count
2. summary.by_status totals == actual case statuses
3. every P0 fail has follow_up.required=true
4. every PASS case has evidence_path and evidence_type
5. no PASS case relies only on model_inference
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)


def load_matrix(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def count_cases(groups: list) -> tuple[int, dict]:
    """Count total cases and by status."""
    total = 0
    by_status = {}
    for group in groups:
        for case in group.get("cases", []):
            total += 1
            status = case.get("status", "untested")
            by_status[status] = by_status.get(status, 0) + 1
    return total, by_status


def check_p0_fail_followup(groups: list) -> list[str]:
    """Check every P0 fail has follow_up.required=true."""
    errors = []
    for group in groups:
        for case in group.get("cases", []):
            if case.get("severity") == "P0" and case.get("status") == "fail":
                follow_up = case.get("follow_up")
                if not follow_up or not follow_up.get("required"):
                    errors.append(f"P0 fail without follow_up: {case.get('id')}")
    return errors


def check_pass_evidence(groups: list) -> list[str]:
    """Check every PASS case has evidence_path and evidence_type."""
    errors = []
    for group in groups:
        for case in group.get("cases", []):
            if case.get("status") == "pass":
                if not case.get("evidence") and not case.get("evidence_path"):
                    errors.append(f"PASS without evidence: {case.get('id')}")
    return errors


def check_no_model_inference_only(groups: list) -> list[str]:
    """Check no PASS case relies only on model_inference."""
    errors = []
    for group in groups:
        for case in group.get("cases", []):
            if case.get("status") == "pass":
                evidence_type = case.get("evidence_type", "")
                if evidence_type == "model_inference":
                    errors.append(f"PASS with model_inference only: {case.get('id')}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate matrix consistency")
    parser.add_argument("matrix_path", help="Path to matrix YAML file")
    args = parser.parse_args()

    matrix_path = Path(args.matrix_path)
    if not matrix_path.exists():
        print(f"FAIL: Matrix file not found: {matrix_path}")
        sys.exit(1)

    matrix = load_matrix(matrix_path)
    groups = matrix.get("groups", [])
    summary = matrix.get("summary", {})

    errors = []

    # Check 1: total_cases matches actual count
    actual_total, actual_by_status = count_cases(groups)
    expected_total = summary.get("total_cases", 0)
    if actual_total != expected_total:
        errors.append(f"total_cases mismatch: summary={expected_total}, actual={actual_total}")

    # Check 2: by_status matches actual statuses
    expected_by_status = summary.get("by_status", {})
    for status, expected_count in expected_by_status.items():
        actual_count = actual_by_status.get(status, 0)
        if actual_count != expected_count:
            errors.append(f"by_status mismatch for {status}: summary={expected_count}, actual={actual_count}")

    # Check 3: P0 fail requires follow-up
    p0_errors = check_p0_fail_followup(groups)
    errors.extend(p0_errors)

    # Check 4: PASS case has evidence
    evidence_errors = check_pass_evidence(groups)
    errors.extend(evidence_errors)

    # Check 5: No model_inference only
    inference_errors = check_no_model_inference_only(groups)
    errors.extend(inference_errors)

    # Report
    print(f"=== Matrix Validation: {matrix_path.name} ===")
    print(f"Total cases: {actual_total} (expected: {expected_total})")
    print(f"By status: {actual_by_status}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(f"  FAIL: {e}")
        print("\nResult: FAIL")
        sys.exit(1)
    else:
        print("\nResult: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
