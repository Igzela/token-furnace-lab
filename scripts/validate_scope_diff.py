#!/usr/bin/env python3
"""
Deterministic validator for scope and diff checks.

Checks:
- Changed files within allowed paths
- No secrets or credentials in diff
- No unrelated files modified
- No forbidden paths touched
"""

import subprocess
import sys
from pathlib import Path


def get_changed_files(repo_root: Path) -> list[str]:
    """Get list of changed files from git."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Try staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
    return [f for f in result.stdout.strip().split("\n") if f]


def validate_scope(
    repo_root: Path,
    allowed_paths: list[str],
    forbidden_paths: list[str],
) -> tuple[bool, list[str]]:
    """Run scope validation on changed files."""
    errors = []
    changed_files = get_changed_files(repo_root)

    if not changed_files:
        return True, ["No changed files detected"]

    # Check forbidden paths
    for changed in changed_files:
        for forbidden in forbidden_paths:
            f = forbidden.rstrip("/")
            if changed == f or changed.startswith(f + "/"):
                errors.append(f"CRITICAL: Forbidden path touched: {changed}")

    # Check allowed paths
    if allowed_paths:
        for changed in changed_files:
            in_allowed = any(
                changed == a.rstrip("/") or changed.startswith(a.rstrip("/") + "/")
                for a in allowed_paths
            )
            if not in_allowed:
                errors.append(f"HIGH: File outside allowed paths: {changed}")

    # Check for secrets/credentials patterns
    secret_patterns = [
        r"\.env$",
        r"credentials",
        r"secret",
        r"password",
        r"token",
        r"api_key",
        r"private_key",
    ]
    for changed in changed_files:
        for pattern in secret_patterns:
            if pattern in changed.lower():
                errors.append(f"CRITICAL: Potential secret in changed file: {changed}")

    has_critical = any("CRITICAL" in e for e in errors)
    has_high = any("HIGH" in e for e in errors)

    passed = not has_critical and not has_high
    return passed, errors


def main():
    if len(sys.argv) < 3:
        print("Usage: validate_scope_diff.py <repo_root> <allowed_paths_file>")
        print("  allowed_paths_file: one path per line")
        sys.exit(1)

    repo_root = Path(sys.argv[1])
    allowed_file = Path(sys.argv[2])

    allowed_paths = []
    forbidden_paths = [".env", "secrets", "credentials"]

    if allowed_file.exists():
        allowed_paths = [
            line.strip()
            for line in allowed_file.read_text().split("\n")
            if line.strip() and not line.startswith("#")
        ]

    passed, errors = validate_scope(repo_root, allowed_paths, forbidden_paths)

    if passed:
        print(f"PASS: scope check ({len(errors)} warnings)")
    else:
        print("FAIL: scope check")

    for error in sorted(errors):
        print(f"  {error}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
