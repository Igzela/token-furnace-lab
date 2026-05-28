#!/usr/bin/env python3
"""
Worktree Manager: create, list, quarantine, and cleanup git worktrees
for parallel subproblem isolation.
"""

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKTREE_BASE = REPO_ROOT / ".claude" / "worktrees"
QUARANTINE_BASE = REPO_ROOT / ".claude" / "quarantine"


@dataclass
class WorktreeInfo:
    name: str
    path: Path
    branch: str
    status: str  # active, quarantined, cleaned


@dataclass
class WorktreeManager:
    run_id: str
    base_dir: Path = field(default=WORKTREE_BASE)
    quarantine_dir: Path = field(default=QUARANTINE_BASE)

    def __post_init__(self):
        self.run_dir = self.base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_base = self.quarantine_dir / self.run_id

    def create(self, subproblem_id: str) -> WorktreeInfo:
        """Create an isolated worktree for a subproblem."""
        wt_name = f"{self.run_id}-{subproblem_id}"
        branch = f"orch/{self.run_id}/{subproblem_id}"
        wt_path = self.run_dir / subproblem_id

        if wt_path.exists():
            # Clean up stale worktree
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
            )

        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(wt_path)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree {subproblem_id}: {result.stderr}")

        # Copy essential files into worktree
        essential_files = ["CLAUDE.md", "AGENTS.md"]
        for f in essential_files:
            src = REPO_ROOT / f
            if src.exists():
                shutil.copy2(src, wt_path / f)

        # Copy the target artifact into worktree for the agent to review
        return WorktreeInfo(
            name=wt_name,
            path=wt_path,
            branch=branch,
            status="active",
        )

    def collect_artifact(self, subproblem_id: str, artifact_name: str,
                         dest_dir: Path) -> Optional[Path]:
        """Collect an artifact from a worktree to the main run directory."""
        src = self.run_dir / subproblem_id / artifact_name
        if not src.exists():
            return None

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{subproblem_id}_{artifact_name}"
        shutil.copy2(src, dest)
        return dest

    def quarantine(self, subproblem_id: str, reason: str = "") -> None:
        """Quarantine a failed worktree."""
        src = self.run_dir / subproblem_id
        if not src.exists():
            return

        self.quarantine_base.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        dest = self.quarantine_base / f"{subproblem_id}-failed-{ts}"
        src.rename(dest)

        # Remove git worktree reference
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(src)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )

    def cleanup(self, subproblem_id: Optional[str] = None) -> None:
        """Clean up worktrees after run completes."""
        if subproblem_id:
            wt_path = self.run_dir / subproblem_id
            if wt_path.exists():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt_path)],
                    cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
                )
        else:
            # Clean all worktrees for this run
            if self.run_dir.exists():
                for child in self.run_dir.iterdir():
                    if child.is_dir():
                        subprocess.run(
                            ["git", "worktree", "remove", "--force", str(child)],
                            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
                        )
                self.run_dir.rmdir()

    def list_active(self) -> List[WorktreeInfo]:
        """List active worktrees for this run."""
        result = []
        if self.run_dir.exists():
            for child in self.run_dir.iterdir():
                if child.is_dir():
                    result.append(WorktreeInfo(
                        name=f"{self.run_id}-{child.name}",
                        path=child,
                        branch=f"orch/{self.run_id}/{child.name}",
                        status="active",
                    ))
        return result


def run_parallel(run_id: str, subproblems: List[Dict],
                 max_parallel: int = 3, timeout: int = 300) -> Dict[str, Dict]:
    """Run subproblems in parallel using subprocess.

    Each subproblem dict should have:
      - id: subproblem identifier
      - command: list of command args to run
      - cwd_subpath: optional subpath within worktree to set as cwd

    Returns dict of subproblem_id -> {status, returncode, output_file, worktree_path}
    """
    import concurrent.futures

    manager = WorktreeManager(run_id)
    results: Dict[str, Dict] = {}

    def execute_subproblem(sub: Dict) -> Dict:
        sub_id = sub["id"]
        try:
            wt_info = manager.create(sub_id)
            cmd = sub["command"]
            cwd = wt_info.path / sub["cwd_subpath"] if sub.get("cwd_subpath") else wt_info.path

            output_file = Path(f"/tmp/tf-parallel-{run_id}-{sub_id}.log")
            with open(output_file, "w") as f:
                proc = subprocess.run(
                    cmd, cwd=str(cwd), capture_output=True, text=True,
                    timeout=timeout,
                )
                f.write(proc.stdout)
                if proc.stderr:
                    f.write(f"\n--- STDERR ---\n{proc.stderr}")

            if proc.returncode != 0:
                manager.quarantine(sub_id, f"exit code {proc.returncode}")
                return {
                    "status": "failed",
                    "returncode": proc.returncode,
                    "output_file": str(output_file),
                    "worktree_path": str(wt_info.path),
                }

            return {
                "status": "completed",
                "returncode": 0,
                "output_file": str(output_file),
                "worktree_path": str(wt_info.path),
            }

        except subprocess.TimeoutExpired:
            manager.quarantine(sub_id, "timeout")
            return {
                "status": "timeout",
                "returncode": -1,
                "output_file": "",
                "worktree_path": "",
            }
        except Exception as e:
            manager.quarantine(sub_id, str(e))
            return {
                "status": "error",
                "returncode": -1,
                "output_file": "",
                "worktree_path": "",
                "error": str(e),
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {executor.submit(execute_subproblem, sub): sub["id"] for sub in subproblems}
        for future in concurrent.futures.as_completed(futures):
            sub_id = futures[future]
            results[sub_id] = future.result()

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: worktree_manager.py create <run_id> <subproblem_id>")
        print("       worktree_manager.py quarantine <run_id> <subproblem_id>")
        print("       worktree_manager.py cleanup <run_id> [subproblem_id]")
        print("       worktree_manager.py list <run_id>")
        sys.exit(1)

    action = sys.argv[1]
    run_id = sys.argv[2] if len(sys.argv) > 2 else "test"

    manager = WorktreeManager(run_id)

    if action == "create":
        sub_id = sys.argv[3] if len(sys.argv) > 3 else "test-sub"
        wt = manager.create(sub_id)
        print(f"Created: {wt.name} at {wt.path}")

    elif action == "quarantine":
        sub_id = sys.argv[3] if len(sys.argv) > 3 else "test-sub"
        manager.quarantine(sub_id)
        print(f"Quarantined: {sub_id}")

    elif action == "cleanup":
        sub_id = sys.argv[3] if len(sys.argv) > 3 else None
        manager.cleanup(sub_id)
        print(f"Cleaned up: {sub_id or 'all'}")

    elif action == "list":
        for wt in manager.list_active():
            print(f"  {wt.name} ({wt.status}) at {wt.path}")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
