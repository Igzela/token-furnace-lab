#!/usr/bin/env python3
"""
Agent Executor: dispatch agents via tf_agent_bridge.sh with single
and parallel execution support.

Usage:
  python3 scripts/tf_agent_executor.py single <prompt_file> <artifact_path> [options]
  python3 scripts/tf_agent_executor.py parallel <tasks_json> [options]
"""

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIDGE_SCRIPT = REPO_ROOT / "scripts" / "tf_agent_bridge.sh"


@dataclass
class AgentTask:
    subproblem_id: str
    prompt_path: str
    artifact_path: str
    write_mode: bool = False
    timeout: int = 300
    model: Optional[str] = None
    subagent_type: str = "Plan"


@dataclass
class AgentResult:
    subproblem_id: str
    artifact_path: str
    success: bool
    wall_seconds: float
    error: Optional[str] = None
    exit_code: int = 0


class AgentExecutor:
    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel

    def execute_one(self, task: AgentTask) -> AgentResult:
        cmd = ["bash", str(BRIDGE_SCRIPT), task.prompt_path, task.artifact_path]
        cmd += ["--timeout", str(task.timeout)]
        if task.write_mode:
            cmd += ["--write-mode"]
        if task.model:
            cmd += ["--model", task.model]
        if task.subagent_type:
            cmd += ["--subagent-type", task.subagent_type]

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=task.timeout + 30,
                cwd=REPO_ROOT,
            )
            wall = time.monotonic() - start
            if result.returncode == 0:
                return AgentResult(
                    subproblem_id=task.subproblem_id,
                    artifact_path=task.artifact_path,
                    success=True,
                    wall_seconds=round(wall, 1),
                )
            else:
                return AgentResult(
                    subproblem_id=task.subproblem_id,
                    artifact_path=task.artifact_path,
                    success=False,
                    wall_seconds=round(wall, 1),
                    error=result.stderr[:500] if result.stderr else "bridge returned non-zero",
                    exit_code=result.returncode,
                )
        except subprocess.TimeoutExpired:
            wall = time.monotonic() - start
            return AgentResult(
                subproblem_id=task.subproblem_id,
                artifact_path=task.artifact_path,
                success=False,
                wall_seconds=round(wall, 1),
                error=f"timeout after {task.timeout}s",
                exit_code=-1,
            )
        except Exception as e:
            wall = time.monotonic() - start
            return AgentResult(
                subproblem_id=task.subproblem_id,
                artifact_path=task.artifact_path,
                success=False,
                wall_seconds=round(wall, 1),
                error=str(e),
                exit_code=-2,
            )

    def execute_parallel(self, tasks: List[AgentTask]) -> Dict[str, AgentResult]:
        results: Dict[str, AgentResult] = {}
        with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
            futures = {pool.submit(self.execute_one, t): t for t in tasks}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = AgentResult(
                        subproblem_id=task.subproblem_id,
                        artifact_path=task.artifact_path,
                        success=False,
                        wall_seconds=0,
                        error=str(e),
                        exit_code=-3,
                    )
                results[task.subproblem_id] = result
        return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]

    if action == "single":
        if len(sys.argv) < 4:
            print("Usage: single <prompt_file> <artifact_path> [--write-mode] [--timeout N]")
            sys.exit(1)
        prompt_file = sys.argv[2]
        artifact_path = sys.argv[3]
        write_mode = "--write-mode" in sys.argv
        timeout = 300
        for i, arg in enumerate(sys.argv):
            if arg == "--timeout" and i + 1 < len(sys.argv):
                timeout = int(sys.argv[i + 1])

        executor = AgentExecutor()
        task = AgentTask(
            subproblem_id="cli_single",
            prompt_path=prompt_file,
            artifact_path=artifact_path,
            write_mode=write_mode,
            timeout=timeout,
        )
        result = executor.execute_one(task)
        print(json.dumps(asdict(result), indent=2))
        sys.exit(0 if result.success else 1)

    elif action == "parallel":
        if len(sys.argv) < 3:
            print("Usage: parallel <tasks_json> [--max-parallel N]")
            sys.exit(1)
        tasks_file = sys.argv[2]
        max_parallel = 3
        for i, arg in enumerate(sys.argv):
            if arg == "--max-parallel" and i + 1 < len(sys.argv):
                max_parallel = int(sys.argv[i + 1])

        with open(tasks_file) as f:
            raw = json.load(f)
        tasks = [AgentTask(**t) for t in raw]

        executor = AgentExecutor(max_parallel=max_parallel)
        results = executor.execute_parallel(tasks)
        print(json.dumps({k: asdict(v) for k, v in results.items()}, indent=2))
        failed = sum(1 for r in results.values() if not r.success)
        sys.exit(1 if failed else 0)

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
