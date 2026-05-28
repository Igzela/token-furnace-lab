#!/usr/bin/env python3
"""
Token Furnace Orchestrator — reusable multi-agent workflow engine.

Modes:
  - queue:  Write prompts for Claude Code to run (safest, recommended)
  - mock:   Create placeholder artifacts for dry-run testing
  - command: Call user-provided shell commands

Usage:
  python scripts/tf_orchestrator.py run orchestration/tasks/my_task.yaml --mode mock
  python scripts/tf_orchestrator.py run orchestration/tasks/my_task.yaml --mode queue
  python scripts/tf_orchestrator.py gate <run_dir> <round_num>
"""

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parent.parent
ACCEPT_VERDICTS = {"PASS", "PASS_WITH_NOTES"}


@dataclasses.dataclass
class Finding:
    id: str
    severity: str
    blocking: bool
    status: str
    evidence_path: Optional[str]
    claim: str
    correction: str


@dataclasses.dataclass
class Review:
    score: int
    verdict: str
    confidence: str
    findings: List[Finding]
    final_recommendation: Optional[str]


@dataclasses.dataclass
class GateResult:
    status: str  # ACCEPT, REPAIR, REJECT, ESCALATE
    round_num: int
    score: Optional[int]
    verdict: Optional[str]
    blocking_count: int
    reason: str
    next_action: str


def now_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def append_event(run_dir: Path, event: Dict[str, Any]) -> None:
    event = {"ts": dt.datetime.now().isoformat(timespec="seconds"), **event}
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# --- Scope checking ---

def check_scope(path: Path, allowed_paths: List[str], forbidden_paths: List[str]) -> List[str]:
    errors = []
    try:
        rel = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return [f"path_outside_repo: {path}"]

    for forbidden in forbidden_paths:
        f = forbidden.rstrip("/")
        if rel == f or rel.startswith(f + "/"):
            errors.append(f"forbidden_path: {rel}")

    if allowed_paths:
        ok = any(rel == a.rstrip("/") or rel.startswith(a.rstrip("/") + "/") for a in allowed_paths)
        if not ok:
            errors.append(f"not_in_allowed_paths: {rel}")

    return errors


# --- Prompt generation ---

def make_agent_prompt(task: Dict[str, Any], sub: Dict[str, Any], run_dir: Path) -> str:
    sections = "\n".join(f"- {s}" for s in sub.get("required_sections", []))
    allowed = "\n".join(f"- {p}" for p in task.get("allowed_paths", []))
    forbidden = "\n".join(f"- {p}" for p in task.get("forbidden_paths", []))

    return f"""# Token Furnace Agent Task

Role: {sub.get("agent", "implementer")}
Subagent type: {sub.get("subagent_type", "Plan")}

## Objective

{task.get("objective", "")}

## Subproblem

{sub.get("title", sub["id"])}

## Required output file

{run_dir / sub["artifact_path"]}

## Required sections

{sections}

## Constraints

Allowed paths:
{allowed}

Forbidden paths:
{forbidden}

## Task prompt

{sub.get("prompt", "")}

## Output rules

Write the artifact to the exact required output file.
Include evidence paths for claims where possible.
Do not modify files outside allowed paths.
"""


def make_review_prompt(task: Dict[str, Any], sub: Dict[str, Any], artifact_path: Path) -> str:
    artifact_text = artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else "(artifact not found)"

    return f"""# Token Furnace Review Request

Review the artifact below.

## Scoring rules

- Score 0-100.
- Verdict must be one of: PASS, PASS_WITH_NOTES, FAIL.
- Include Confidence: HIGH/MEDIUM/LOW.
- Include Findings as bullets with: id, severity, category, status, blocking, evidence_path, claim, correction.
- Any high/critical blocking finding should make recommendation REPAIR or ESCALATE.

## Quality threshold

score_min: {task.get("score_min", 80)}

## Artifact content

```markdown
{artifact_text}
```
"""


# --- Adapter: dispatch agents ---

def dispatch_agent(mode: str, task: Dict, sub: Dict, run_dir: Path, timeout: int) -> Path:
    artifact_path = run_dir / sub["artifact_path"]
    prompt = make_agent_prompt(task, sub, run_dir)
    prompt_path = run_dir / "prompts" / f"{sub['id']}_agent_prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    if mode == "queue":
        return artifact_path

    if mode == "mock":
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"# Mock: {sub.get('title', sub['id'])}\n\nNo real agent called.\n", encoding="utf-8")
        return artifact_path

    if mode == "command":
        cmd = os.environ.get("TF_AGENT_CMD")
        if not cmd:
            raise RuntimeError("TF_AGENT_CMD required for --mode command")
        result = subprocess.run(cmd.format(prompt=str(prompt_path)), shell=True, timeout=timeout, text=True, capture_output=True)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(result.stdout, encoding="utf-8")
        return artifact_path

    raise ValueError(f"unknown mode: {mode}")


def dispatch_review(mode: str, task: Dict, sub: Dict, artifact_path: Path, run_dir: Path, timeout: int) -> Path:
    review_path = run_dir / sub["review_path"]
    prompt = make_review_prompt(task, sub, artifact_path)
    prompt_path = run_dir / "prompts" / f"{sub['id']}_review_prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    if mode == "queue":
        return review_path

    if mode == "mock":
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            f"# Review\n\nScore: 85\nVerdict: PASS_WITH_NOTES\nConfidence: MEDIUM\n\n"
            f"## Findings\n\nNo blocking issues found.\n\n"
            f"## Final Recommendation\n\nACCEPT\n",
            encoding="utf-8",
        )
        return review_path

    if mode == "command":
        cmd = os.environ.get("TF_REVIEW_CMD")
        if not cmd:
            raise RuntimeError("TF_REVIEW_CMD required for --mode command")
        result = subprocess.run(cmd.format(prompt=str(prompt_path)), shell=True, timeout=timeout, text=True, capture_output=True)
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(result.stdout, encoding="utf-8")
        return review_path

    raise ValueError(f"unknown mode: {mode}")


# --- Review parsing ---

def parse_review(text: str) -> Review:
    score_match = re.search(r"Score\s*:\s*(\d{1,3})", text)
    verdict_match = re.search(r"Verdict\s*:\s*(PASS_WITH_NOTES|PASS|FAIL)", text)
    conf_match = re.search(r"Confidence\s*:\s*(HIGH|MEDIUM|LOW)", text)
    final_match = re.search(r"Final Recommendation\s*\n+\s*(\w+)", text)

    score = int(score_match.group(1)) if score_match else 0
    verdict = verdict_match.group(1) if verdict_match else "FAIL"
    confidence = conf_match.group(1) if conf_match else "LOW"
    final_rec = final_match.group(1) if final_match else None

    findings = []
    finding_pattern = re.finditer(
        r"id\s*:\s*(\w+).*?severity\s*:\s*(\w+).*?blocking\s*:\s*(\w+).*?claim\s*:\s*(.+?)(?:\ncorrection\s*:\s*(.+))?",
        text,
        re.DOTALL,
    )
    for m in finding_pattern:
        findings.append(Finding(
            id=m.group(1),
            severity=m.group(2),
            blocking=m.group(3).lower() == "true",
            status="open",
            evidence_path=None,
            claim=m.group(4).strip(),
            correction=(m.group(5) or "None").strip(),
        ))

    return Review(score=score, verdict=verdict, confidence=confidence, findings=findings, final_recommendation=final_rec)


# --- Quality gate ---

def evaluate_gate(task: Dict, review: Review, round_num: int, artifact_exists: bool) -> GateResult:
    score_min = task.get("score_min", 80)
    max_repair = task.get("max_repair_rounds", 2)

    if not artifact_exists:
        return GateResult("REJECT", round_num, review.score, review.verdict, 0, "Artifact missing", "escalate")

    blocking = [f for f in review.findings if f.blocking]

    if review.score < score_min:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, review.score, review.verdict, len(blocking),
                              f"Score {review.score} < {score_min}", "repair")
        return GateResult("ESCALATE", round_num, review.score, review.verdict, len(blocking),
                          f"Score {review.score} < {score_min} after {round_num} rounds", "escalate")

    if blocking:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, review.score, review.verdict, len(blocking),
                              f"{len(blocking)} blocking findings", "repair")
        return GateResult("ESCALATE", round_num, review.score, review.verdict, len(blocking),
                          f"{len(blocking)} blocking findings after {round_num} rounds", "escalate")

    if review.verdict in ACCEPT_VERDICTS:
        return GateResult("ACCEPT", round_num, review.score, review.verdict, 0,
                          f"Score {review.score}, verdict {review.verdict}", "done")

    if round_num < max_repair:
        return GateResult("REPAIR", round_num, review.score, review.verdict, 0,
                          f"Verdict {review.verdict} not in {ACCEPT_VERDICTS}", "repair")
    return GateResult("ESCALATE", round_num, review.score, review.verdict, 0,
                      f"Verdict {review.verdict} not in {ACCEPT_VERDICTS} after {round_num} rounds", "escalate")


def gate_result_yaml(result: GateResult) -> str:
    return yaml.dump({
        "status": result.status,
        "round": result.round_num,
        "score": result.score,
        "verdict": result.verdict,
        "blocking_findings": result.blocking_count,
        "reason": result.reason,
        "next_action": result.next_action,
    }, default_flow_style=False, sort_keys=False)


# --- Main orchestration loop ---

def run_orchestrate(task_path: Path, mode: str, timeout: int) -> None:
    task = load_yaml(task_path)
    run_id = now_id()
    run_dir = REPO_ROOT / "runs" / "orchestration" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    write_yaml(run_dir / "task.yaml", task)
    append_event(run_dir, {"event": "run_start", "task_id": task.get("task_id", "unknown"), "mode": mode})

    print(f"Run ID: {run_id}")
    print(f"Run dir: {run_dir}")
    print(f"Mode: {mode}")
    print()

    for sub in task.get("subproblems", []):
        print(f"--- Subproblem: {sub['id']} ---")

        # Dispatch agent
        artifact_path = dispatch_agent(mode, task, sub, run_dir, timeout)
        print(f"  Artifact: {artifact_path}")
        append_event(run_dir, {"event": "agent_dispatched", "subproblem": sub["id"]})

        if mode == "queue":
            prompt_path = run_dir / "prompts" / f"{sub['id']}_agent_prompt.md"
            print(f"  Prompt queued: {prompt_path}")
            print(f"  -> Run Agent tool with subagent_type={sub.get('subagent_type', 'Plan')}")
            print(f"  -> Write output to {artifact_path}")
            print()
            continue

        # Dispatch review
        review_path = dispatch_review(mode, task, sub, artifact_path, run_dir, timeout)
        print(f"  Review: {review_path}")
        append_event(run_dir, {"event": "review_dispatched", "subproblem": sub["id"]})

        if mode == "queue":
            prompt_path = run_dir / "prompts" / f"{sub['id']}_review_prompt.md"
            print(f"  Review prompt queued: {prompt_path}")
            print()
            continue

        # Parse and gate
        review_text = review_path.read_text(encoding="utf-8")
        review = parse_review(review_text)
        artifact_exists = artifact_path.exists()

        gate = evaluate_gate(task, review, 1, artifact_exists)
        gate_yaml = gate_result_yaml(gate)

        gate_path = run_dir / "gate_results" / f"{sub['id']}_round_1.yaml"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(gate_yaml, encoding="utf-8")

        print(f"  Gate: {gate.status} (score={gate.score}, verdict={gate.verdict})")
        print(f"  Reason: {gate.reason}")
        append_event(run_dir, {"event": "gate_evaluated", "subproblem": sub["id"], "status": gate.status, "score": gate.score})
        print()

    append_event(run_dir, {"event": "run_complete"})
    print("Done.")


def run_gate(run_dir: Path, round_num: int) -> None:
    task_path = run_dir / "task.yaml"
    if not task_path.exists():
        print(f"No task.yaml in {run_dir}", file=sys.stderr)
        sys.exit(1)

    task = load_yaml(task_path)
    for sub in task.get("subproblems", []):
        review_path = run_dir / sub["review_path"]
        artifact_path = run_dir / sub["artifact_path"]

        if not review_path.exists():
            print(f"Review not found: {review_path}")
            continue

        review = parse_review(review_path.read_text(encoding="utf-8"))
        gate = evaluate_gate(task, review, round_num, artifact_path.exists())

        gate_path = run_dir / "gate_results" / f"{sub['id']}_round_{round_num}.yaml"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(gate_result_yaml(gate), encoding="utf-8")

        print(f"Subproblem: {sub['id']}")
        print(f"  Status: {gate.status}")
        print(f"  Score: {gate.score}, Verdict: {gate.verdict}")
        print(f"  Reason: {gate.reason}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Token Furnace Orchestrator")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run orchestration")
    run_p.add_argument("task_yaml", type=Path, help="Path to task YAML")
    run_p.add_argument("--mode", choices=["queue", "mock", "command"], default="mock")
    run_p.add_argument("--timeout", type=int, default=300)

    gate_p = sub.add_parser("gate", help="Evaluate gate for existing run")
    gate_p.add_argument("run_dir", type=Path)
    gate_p.add_argument("round_num", type=int, nargs="?", default=1)

    args = parser.parse_args()

    if args.command == "run":
        run_orchestrate(args.task_yaml, args.mode, args.timeout)
    elif args.command == "gate":
        run_gate(args.run_dir, args.round_num)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
