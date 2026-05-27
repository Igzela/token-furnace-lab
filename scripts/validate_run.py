#!/usr/bin/env python3
"""Validate a run directory for completeness and safety."""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FILES = [
    "run.yaml",
    "task.md",
    "status.md",
]

REQUIRED_MODEL_OUTPUTS = [
    "gpt-architect.md",
    "claude-code-repo-reader.md",
    "codex-risk-reviewer.md",
]

REQUIRED_SYNTHESIS = [
    "decision-record.md",
]

SECRET_PATTERNS = [
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),       # GitHub token
    re.compile(r"sk-[a-zA-Z0-9]{48}"),         # OpenAI key
    re.compile(r"sk-ant-[a-zA-Z0-9]{48}"),     # Anthropic key
    re.compile(r"AKIA[A-Z0-9]{16}"),           # AWS key
    re.compile(r"password\s*[:=]\s*\S+", re.I),
    re.compile(r"secret\s*[:=]\s*\S+", re.I),
    re.compile(r"token\s*[:=]\s*['\"][^'\"]{20,}", re.I),
]


def check_file_exists(run_dir: Path, rel_path: str) -> bool:
    return (run_dir / rel_path).exists()


def check_not_empty(run_dir: Path, rel_path: str) -> bool:
    p = run_dir / rel_path
    return p.exists() and p.stat().st_size > 0


def scan_for_secrets(run_dir: Path) -> list[str]:
    """Scan all .md, .yaml, .txt files for potential secrets."""
    findings = []
    for ext in ("*.md", "*.yaml", "*.yml", "*.txt"):
        for f in run_dir.rglob(ext):
            try:
                content = f.read_text(errors="ignore")
                for pattern in SECRET_PATTERNS:
                    if pattern.search(content):
                        findings.append(f"Potential secret in {f.relative_to(run_dir)}: {pattern.pattern}")
            except Exception:
                pass
    return findings


def main():
    parser = argparse.ArgumentParser(description="Validate a run directory")
    parser.add_argument("run_dir", help="Path to run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"FAIL: Run directory not found: {run_dir}")
        sys.exit(1)

    errors = []
    warnings = []

    # Check required files
    for f in REQUIRED_FILES:
        if not check_file_exists(run_dir, f):
            errors.append(f"Missing required file: {f}")
        elif not check_not_empty(run_dir, f):
            errors.append(f"Empty required file: {f}")

    # Check model outputs
    model_out = run_dir / "model-outputs"
    for f in REQUIRED_MODEL_OUTPUTS:
        path = model_out / f
        if not path.exists():
            warnings.append(f"Missing model output: model-outputs/{f}")
        elif not check_not_empty(run_dir, f"model-outputs/{f}"):
            warnings.append(f"Empty model output: model-outputs/{f}")

    # Check synthesis
    synth_dir = run_dir / "synthesis"
    for f in REQUIRED_SYNTHESIS:
        path = synth_dir / f
        if not path.exists():
            warnings.append(f"Missing synthesis: synthesis/{f}")

    # Scan for secrets
    secret_findings = scan_for_secrets(run_dir)
    if secret_findings:
        errors.extend(secret_findings)

    # Report
    print(f"=== Validation: {run_dir.name} ===")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(f"  FAIL: {e}")

    if warnings:
        print("\n--- WARNINGS ---")
        for w in warnings:
            print(f"  WARN: {w}")

    if errors:
        print("\nResult: FAIL")
        sys.exit(1)
    elif warnings:
        print("\nResult: PASS_WITH_WARNINGS")
        sys.exit(0)
    else:
        print("\nResult: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
