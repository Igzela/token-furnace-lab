#!/usr/bin/env python3
"""Validate a run directory for completeness and safety.

Canonical run layout:
  inputs/
  model_outputs/
  synthesis/
  task.md

Legacy layout (also accepted):
  model-outputs/
  run.yaml
  status.md
"""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FILES = [
    "task.md",
]

OPTIONAL_FILES = [
    "run.yaml",
    "status.md",
]

REQUIRED_DIRS = [
    "model_outputs",
    "synthesis",
]

LEGACY_DIRS = {
    "model-outputs": "model_outputs",
}

# Model output files are flexible; these are recommended
RECOMMENDED_MODEL_OUTPUTS = [
    "claude-code-output.md",
    "gpt-reviewer-output.md",
]

OPTIONAL_MODEL_OUTPUTS = [
    "codex-risk-reviewer-output.md",
]

# Legacy model output names (also accepted)
LEGACY_MODEL_OUTPUTS = {
    "gpt-architect.md": "gpt-reviewer-output.md",
    "claude-code-repo-reader.md": "claude-code-output.md",
    "codex-risk-reviewer.md": "codex-risk-reviewer-output.md",
}

REQUIRED_SYNTHESIS = [
    "synthesis.md",
]

OPTIONAL_SYNTHESIS = [
    "decision-record.md",
    "cost_estimate.md",
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


def detect_model_outputs_dir(run_dir: Path) -> tuple[str, str]:
    """Detect model outputs directory. Returns (dir_name, status)."""
    if (run_dir / "model_outputs").exists():
        return "model_outputs", "canonical"
    if (run_dir / "model-outputs").exists():
        return "model-outputs", "legacy"
    return "model_outputs", "missing"


def find_model_outputs(run_dir: Path, model_dir: str) -> list[str]:
    """Find model output files, accepting both canonical and legacy names."""
    found = []
    dir_path = run_dir / model_dir
    if not dir_path.exists():
        return found

    for f in dir_path.iterdir():
        if f.is_file() and f.suffix == ".md":
            found.append(f.name)
    return found


def check_model_role_contract(run_dir: Path, model_dir: str) -> list[str]:
    """Check if declared model roles have corresponding outputs."""
    warnings = []
    experiment_yaml = run_dir / "experiment.yaml"
    task_md = run_dir / "task.md"

    # Check if experiment.yaml declares codex role
    has_codex_declared = False
    for source in [experiment_yaml, task_md]:
        if source.exists():
            content = source.read_text(errors="ignore")
            if "codex" in content.lower() and "role" in content.lower():
                has_codex_declared = True
                break

    if has_codex_declared:
        dir_path = run_dir / model_dir
        codex_files = [f for f in dir_path.iterdir() if "codex" in f.name.lower()] if dir_path.exists() else []
        if not codex_files:
            warnings.append(f"Codex role declared but no codex output found in {model_dir}/")

    return warnings


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

    # Check optional files
    for f in OPTIONAL_FILES:
        if not check_file_exists(run_dir, f):
            warnings.append(f"Missing optional file: {f}")

    # Detect model outputs directory
    model_dir, model_status = detect_model_outputs_dir(run_dir)
    if model_status == "missing":
        warnings.append("No model outputs directory found (expected model_outputs/ or model-outputs/)")
    elif model_status == "legacy":
        warnings.append(f"Using legacy directory name: model-outputs/ (canonical: model_outputs/)")

    # Check model outputs
    found_outputs = find_model_outputs(run_dir, model_dir)
    for f in RECOMMENDED_MODEL_OUTPUTS:
        if f not in found_outputs:
            # Check legacy name
            legacy_name = None
            for legacy, canonical in LEGACY_MODEL_OUTPUTS.items():
                if canonical == f:
                    legacy_name = legacy
                    break
            if legacy_name and legacy_name in found_outputs:
                warnings.append(f"Legacy model output name: {legacy_name} (canonical: {f})")
            else:
                warnings.append(f"Missing recommended model output: {model_dir}/{f}")

    # Check model role contract
    role_warnings = check_model_role_contract(run_dir, model_dir)
    warnings.extend(role_warnings)

    # Check synthesis
    synth_dir = run_dir / "synthesis"
    if not synth_dir.exists():
        errors.append("Missing synthesis/ directory")
    else:
        for f in REQUIRED_SYNTHESIS:
            if not check_file_exists(run_dir, f"synthesis/{f}"):
                errors.append(f"Missing required synthesis: synthesis/{f}")
            elif not check_not_empty(run_dir, f"synthesis/{f}"):
                errors.append(f"Empty required synthesis: synthesis/{f}")

        for f in OPTIONAL_SYNTHESIS:
            if not check_file_exists(run_dir, f"synthesis/{f}"):
                warnings.append(f"Missing optional synthesis: synthesis/{f}")

    # Scan for secrets
    secret_findings = scan_for_secrets(run_dir)
    if secret_findings:
        errors.extend(secret_findings)

    # Report
    print(f"=== Validation: {run_dir.name} ===")
    print(f"Model outputs dir: {model_dir} ({model_status})")
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
