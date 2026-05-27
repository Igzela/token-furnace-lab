#!/usr/bin/env python3
"""Validate synthesis evidence completeness.

Checks:
1. synthesis.md exists and is non-empty
2. accepted findings contain evidence
3. target_control_verdict exists
4. experiment_verdict exists
5. known gaps listed when matrix has warn/partial/deferred
"""

import argparse
import re
import sys
from pathlib import Path


def check_synthesis_exists(synth_dir: Path) -> list[str]:
    """Check synthesis.md exists and is non-empty."""
    errors = []
    synth_file = synth_dir / "synthesis.md"
    if not synth_file.exists():
        errors.append("Missing synthesis/synthesis.md")
    elif synth_file.stat().st_size == 0:
        errors.append("Empty synthesis/synthesis.md")
    return errors


def check_verdicts(content: str) -> list[str]:
    """Check experiment_verdict and target_control_verdict exist."""
    errors = []
    if "experiment_verdict" not in content:
        errors.append("Missing experiment_verdict")
    if "target_control_verdict" not in content:
        errors.append("Missing target_control_verdict")
    return errors


def check_evidence_in_findings(content: str) -> list[str]:
    """Check accepted findings have evidence."""
    errors = []

    # Look for accepted findings section
    accepted_section = re.search(r"## Accepted Findings.*?(?=##|$)", content, re.DOTALL)
    if not accepted_section:
        return errors

    section_text = accepted_section.group()

    # Check for numbered findings without evidence
    findings = re.findall(r"\d+\.\s+\*\*.*?\*\*", section_text)
    evidence_refs = re.findall(r"evidence|\.md|\.yaml|\.py|line \d+", section_text, re.I)

    if findings and not evidence_refs:
        errors.append("Accepted findings section exists but no evidence references found")

    return errors


def check_known_gaps(content: str, matrix_path: Path = None) -> list[str]:
    """Check known gaps are listed when applicable."""
    errors = []

    # If matrix has warn/partial/deferred, synthesis should have known gaps
    if matrix_path and matrix_path.exists():
        try:
            import yaml
            with open(matrix_path) as f:
                matrix = yaml.safe_load(f)
            summary = matrix.get("summary", {})
            by_status = summary.get("by_status", {})
            has_gaps = any(by_status.get(s, 0) > 0 for s in ["warn", "partial", "deferred", "unknown"])

            if has_gaps and "known" not in content.lower() and "gap" not in content.lower():
                errors.append("Matrix has warn/partial/deferred but synthesis doesn't list known gaps")
        except Exception:
            pass

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate synthesis evidence")
    parser.add_argument("run_dir", help="Path to run directory")
    parser.add_argument("--matrix", help="Path to matrix YAML file (optional)", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"FAIL: Run directory not found: {run_dir}")
        sys.exit(1)

    synth_dir = run_dir / "synthesis"
    errors = []

    # Check synthesis exists
    errors.extend(check_synthesis_exists(synth_dir))

    if errors:
        print(f"=== Synthesis Validation: {run_dir.name} ===")
        for e in errors:
            print(f"  FAIL: {e}")
        print("\nResult: FAIL")
        sys.exit(1)

    # Read synthesis content
    synth_file = synth_dir / "synthesis.md"
    content = synth_file.read_text(errors="ignore")

    # Check verdicts
    errors.extend(check_verdicts(content))

    # Check evidence in findings
    errors.extend(check_evidence_in_findings(content))

    # Check known gaps
    matrix_path = Path(args.matrix) if args.matrix else None
    errors.extend(check_known_gaps(content, matrix_path))

    # Report
    print(f"=== Synthesis Validation: {run_dir.name} ===")
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
