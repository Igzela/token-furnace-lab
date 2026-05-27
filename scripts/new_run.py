#!/usr/bin/env python3
"""Create a new experiment run directory with proper structure."""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def get_git_info(repo_path: str) -> dict:
    """Get git status, branch, and commit for a repo."""
    info = {}
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_path, capture_output=True, text=True
        )
        info["dirty"] = result.stdout.strip()
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path, capture_output=True, text=True
        )
        info["branch"] = result.stdout.strip()
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, capture_output=True, text=True
        )
        info["commit"] = result.stdout.strip()
    except Exception as e:
        info["error"] = str(e)
    return info


def main():
    parser = argparse.ArgumentParser(description="Create a new experiment run")
    parser.add_argument("experiment_id", help="Experiment ID (e.g. hermes-perm-audit-001)")
    parser.add_argument("--target", help="Target repo path", default=None)
    parser.add_argument("--operator", help="Operator name", default=os.environ.get("USER", "unknown"))
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    exp_dir = project_root / "experiments" / "agent-workflow" / args.experiment_id

    if not exp_dir.exists():
        print(f"Error: Experiment not found: {exp_dir}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = project_root / "runs" / args.experiment_id / timestamp

    # Create run directory structure
    dirs = [
        run_dir / "inputs",
        run_dir / "model-outputs",
        run_dir / "synthesis",
        run_dir / "metrics",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Copy experiment spec
    shutil.copy(exp_dir / "task.md", run_dir / "task.md")

    # Generate run metadata
    run_meta = {
        "experiment_id": args.experiment_id,
        "timestamp": timestamp,
        "operator": args.operator,
        "target_repo": args.target,
        "furnace_git": get_git_info(str(project_root)),
        "status": "created",
    }

    if args.target:
        run_meta["target_git"] = get_git_info(args.target)

    with open(run_dir / "run.yaml", "w") as f:
        yaml.dump(run_meta, f, default_flow_style=False, allow_unicode=True)

    # Create status.md
    with open(run_dir / "status.md", "w") as f:
        f.write(f"# Run Status: {args.experiment_id}/{timestamp}\n\n")
        f.write(f"Created: {datetime.now().isoformat()}\n")
        f.write(f"Operator: {args.operator}\n")
        f.write(f"Target: {args.target}\n\n")
        f.write("## Status: CREATED\n\n")
        f.write("### Checklist\n")
        f.write("- [ ] inputs collected\n")
        f.write("- [ ] gpt-architect output\n")
        f.write("- [ ] claude-code-repo-reader output\n")
        f.write("- [ ] codex-risk-reviewer output\n")
        f.write("- [ ] synthesis complete\n")
        f.write("- [ ] decision record written\n")
        f.write("- [ ] knowledge distilled\n")

    print(f"Run created: {run_dir}")
    print(f"Edit {run_dir / 'status.md'} to track progress.")


if __name__ == "__main__":
    main()
