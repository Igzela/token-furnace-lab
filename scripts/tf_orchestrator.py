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
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parent.parent
ACCEPT_VERDICTS = {"PASS", "PASS_WITH_NOTES"}

# --- Run state (idempotent resume) ---

@dataclasses.dataclass
class RunState:
    completed: Dict[str, Dict[str, Any]] = dataclasses.field(default_factory=dict)

    def is_done(self, subproblem_id: str) -> bool:
        return subproblem_id in self.completed

    def mark_done(self, subproblem_id: str, gate_status: str, score: Optional[int], round_num: int) -> None:
        self.completed[subproblem_id] = {
            "gate_status": gate_status,
            "score": score,
            "round": round_num,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"completed": self.completed}


def load_run_state(run_dir: Path) -> RunState:
    state_path = run_dir / "run_state.json"
    if state_path.exists():
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return RunState(completed=data.get("completed", {}))
    return RunState()


def save_run_state(run_dir: Path, state: RunState) -> None:
    state_path = run_dir / "run_state.json"
    state_path.write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

# Validator imports (lazy to avoid import errors if scripts/ is not on path)
def _import_validators():
    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    from validate_state_machine import validate as validate_sm
    from validate_review_artifact import validate_review
    from validate_scope_diff import validate_scope
    return validate_sm, validate_review, validate_scope


def validate_artifact(artifact_path: Path, artifact_type: str) -> List[str]:
    """Run deterministic validators on an artifact. Returns list of error strings."""
    errors = []

    if artifact_type == "state_machine":
        try:
            sm_validate, _, _ = _import_validators()
            passed, sm_errors = sm_validate(artifact_path)
            if not passed:
                errors.extend([f"STATE_MACHINE: {e}" for e in sm_errors])
        except Exception as e:
            errors.append(f"STATE_MACHINE: validator error: {e}")

    if artifact_type == "review":
        try:
            _, review_validate, _ = _import_validators()
            passed, review_errors = review_validate(artifact_path)
            if not passed:
                errors.extend([f"REVIEW: {e}" for e in review_errors])
        except Exception as e:
            errors.append(f"REVIEW: validator error: {e}")

    return errors


def validate_scope(repo_root: Path, run_dir: Path, allowed_paths: List[str], forbidden_paths: List[str]) -> List[str]:
    """Run scope validator on changed files in run_dir."""
    try:
        _, _, scope_validate = _import_validators()
        passed, scope_errors = scope_validate(repo_root, allowed_paths, forbidden_paths)
        if not passed:
            return [f"SCOPE: {e}" for e in scope_errors]
    except Exception as e:
        return [f"SCOPE: validator error: {e}"]
    return []


# --- Budget ledger ---

@dataclasses.dataclass
class BudgetLedger:
    start_time: float
    iterations: int = 0
    tokens_used: int = 0
    wall_seconds: float = 0.0
    rounds: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    def tick(self, subproblem_id: str, round_num: int, gate_status: str, score: Optional[int]) -> None:
        self.iterations += 1
        self.wall_seconds = time.time() - self.start_time
        self.rounds.append({
            "subproblem": subproblem_id,
            "round": round_num,
            "gate_status": gate_status,
            "score": score,
            "wall_s": round(self.wall_seconds, 1),
        })

    def check_budget(self, max_iterations: int, max_tokens: int, timeout_seconds: int) -> Optional[str]:
        if self.iterations >= max_iterations:
            return f"budget_exceeded: iterations {self.iterations} >= {max_iterations}"
        if max_tokens and self.tokens_used >= max_tokens:
            return f"budget_exceeded: tokens {self.tokens_used} >= {max_tokens}"
        if timeout_seconds and self.wall_seconds >= timeout_seconds:
            return f"budget_exceeded: wall time {self.wall_seconds:.0f}s >= {timeout_seconds}s"
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": dt.datetime.fromtimestamp(self.start_time).isoformat(timespec="seconds"),
            "iterations": self.iterations,
            "wall_seconds": round(self.wall_seconds, 1),
            "rounds": self.rounds,
        }


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

    if mode == "bridge":
        bridge_script = REPO_ROOT / "scripts" / "tf_agent_bridge.sh"
        cmd = [str(bridge_script), str(prompt_path), str(artifact_path),
               "--timeout", str(timeout), "--subagent-type", sub.get("subagent_type", "Plan")]
        result = subprocess.run(cmd, timeout=timeout + 30, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Agent bridge failed: {result.stderr}")
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

    if mode == "bridge":
        bridge_script = REPO_ROOT / "scripts" / "tf_agent_bridge.sh"
        cmd = [str(bridge_script), str(prompt_path), str(review_path),
               "--timeout", str(timeout)]
        result = subprocess.run(cmd, timeout=timeout + 30, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Review bridge failed: {result.stderr}")
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
    # Try JSON block first (structured output from agents)
    json_blocks = []
    for match in re.finditer(r"```json\s*\n(.*?)```", text, re.DOTALL):
        try:
            json_blocks.append(json.loads(match.group(1).strip()))
        except json.JSONDecodeError:
            continue

    if json_blocks:
        data = json_blocks[0]
        score = data.get("score", 0)
        verdict = data.get("verdict", "FAIL")
        confidence = data.get("confidence", "LOW")
        final_rec = data.get("final_recommendation")

        findings = []
        for f in data.get("findings", []):
            findings.append(Finding(
                id=f.get("id", "?"),
                severity=f.get("severity", "MEDIUM"),
                blocking=f.get("blocking", False),
                status=f.get("status", "open"),
                evidence_path=f.get("evidence_path"),
                claim=f.get("claim", ""),
                correction=f.get("correction", "None"),
            ))

        return Review(score=score, verdict=verdict, confidence=confidence,
                      findings=findings, final_recommendation=final_rec)

    # Markdown fallback
    score_match = re.search(r"Score\s*[:*]*\s*\*{0,2}(\d{1,3})", text)
    verdict_match = re.search(r"Verdict\s*[:*]*\s*\*{0,2}(PASS_WITH_NOTES|PASS|FAIL)", text)
    conf_match = re.search(r"Confidence\s*[:*]*\s*\*{0,2}(HIGH|MEDIUM|LOW)", text)
    final_match = re.search(r"Final Recommendation\s*\n+\s*(\w+)", text)

    score = int(score_match.group(1)) if score_match else 0
    verdict = verdict_match.group(1) if verdict_match else "FAIL"
    confidence = conf_match.group(1) if conf_match else "LOW"
    final_rec = final_match.group(1) if final_match else None

    findings = []
    # Handle both "id: val" and "**id**: val" formats
    finding_pattern = re.finditer(
        r"\*{0,2}id\*{0,2}\s*:\s*(\w+).*?\*{0,2}severity\*{0,2}\s*:\s*(\w+)"
        r".*?\*{0,2}blocking\*{0,2}\s*:\s*(\w+)"
        r"(?:.*?\*{0,2}evidence_path\*{0,2}\s*:\s*(\S+))?"
        r".*?\*{0,2}claim\*{0,2}\s*:\s*(.+?)(?:\n\*{0,2}correction\*{0,2}\s*:\s*(.+))?",
        text,
        re.DOTALL,
    )
    for m in finding_pattern:
        findings.append(Finding(
            id=m.group(1),
            severity=m.group(2),
            blocking=m.group(3).lower() == "true",
            status="open",
            evidence_path=m.group(4),
            claim=m.group(5).strip(),
            correction=(m.group(6) or "None").strip(),
        ))

    return Review(score=score, verdict=verdict, confidence=confidence, findings=findings, final_recommendation=final_rec)


# --- Evidence validation ---

def validate_evidence(review: Review, run_dir: Path) -> List[str]:
    """Check that blocking findings have valid evidence paths."""
    errors = []
    for f in review.findings:
        if not f.blocking:
            continue
        if not f.evidence_path:
            errors.append(f"HIGH: Blocking finding {f.id} has no evidence_path")
            continue
        # Check if evidence file exists (relative to run_dir)
        evidence_abs = run_dir / f.evidence_path
        if not evidence_abs.exists():
            # Also try relative to repo root
            evidence_repo = REPO_ROOT / f.evidence_path
            if not evidence_repo.exists():
                errors.append(f"HIGH: Blocking finding {f.id} evidence_path not found: {f.evidence_path}")
    return errors


# --- Quality gate ---

def evaluate_gate(task: Dict, review: Review, round_num: int, artifact_exists: bool,
                  validator_errors: Optional[List[str]] = None,
                  evidence_errors: Optional[List[str]] = None) -> GateResult:
    """Evaluate quality gate with fixed priority rules:
    1. Artifact exists?
    2. Validator errors (CRITICAL/HIGH)?
    3. Evidence errors?
    4. Blocking findings (override score)?
    5. Score below threshold?
    6. Verdict not accepted?
    """
    score_min = task.get("score_min", 80)
    max_repair = task.get("max_repair_rounds", 2)

    if not artifact_exists:
        return GateResult("REJECT", round_num, review.score, review.verdict, 0, "Artifact missing", "escalate")

    # Priority 1: Validator errors override review — structural issues are blocking
    if validator_errors:
        crit_errors = [e for e in validator_errors if any(sev in e for sev in ("CRITICAL", "HIGH"))]
        if crit_errors:
            if round_num < max_repair:
                return GateResult("REPAIR", round_num, review.score, review.verdict, len(crit_errors),
                                  f"Validator errors: {'; '.join(crit_errors[:3])}", "repair")
            return GateResult("ESCALATE", round_num, review.score, review.verdict, len(crit_errors),
                              f"Validator errors after {round_num} rounds: {'; '.join(crit_errors[:3])}", "escalate")

    # Priority 2: Evidence errors — blocking findings without valid evidence
    if evidence_errors:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, review.score, review.verdict, len(evidence_errors),
                              f"Evidence errors: {'; '.join(evidence_errors[:3])}", "repair")
        return GateResult("ESCALATE", round_num, review.score, review.verdict, len(evidence_errors),
                          f"Evidence errors after {round_num} rounds: {'; '.join(evidence_errors[:3])}", "escalate")

    # Priority 3: Blocking findings override score — even 91 can't cover structural failures
    blocking = [f for f in review.findings if f.blocking]
    if blocking:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, review.score, review.verdict, len(blocking),
                              f"{len(blocking)} blocking findings", "repair")
        return GateResult("ESCALATE", round_num, review.score, review.verdict, len(blocking),
                          f"{len(blocking)} blocking findings after {round_num} rounds", "escalate")

    # Priority 4: Score below threshold
    if review.score < score_min:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, review.score, review.verdict, 0,
                              f"Score {review.score} < {score_min}", "repair")
        return GateResult("ESCALATE", round_num, review.score, review.verdict, 0,
                          f"Score {review.score} < {score_min} after {round_num} rounds", "escalate")

    # Priority 5: Verdict in accept set
    if review.verdict in ACCEPT_VERDICTS:
        return GateResult("ACCEPT", round_num, review.score, review.verdict, 0,
                          f"Score {review.score}, verdict {review.verdict}", "done")

    # Priority 6: Verdict not accepted
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


def evaluate_fused_gate(task: Dict, fused_findings: List[Finding], fused_scores: Dict[str, int],
                        fused_verdicts: Dict[str, str], round_num: int,
                        artifact_exists: bool = True,
                        validator_errors: Optional[List[str]] = None,
                        evidence_errors: Optional[List[str]] = None) -> GateResult:
    """Evaluate gate using fused multi-reviewer findings.
    Same priority rules as evaluate_gate, but operates on merged findings.
    """
    score_min = task.get("score_min", 80)
    max_repair = task.get("max_repair_rounds", 2)

    if not artifact_exists:
        return GateResult("REJECT", round_num, 0, "FAIL", 0, "Artifact missing", "escalate")

    if validator_errors:
        crit_errors = [e for e in validator_errors if any(sev in e for sev in ("CRITICAL", "HIGH"))]
        if crit_errors:
            if round_num < max_repair:
                return GateResult("REPAIR", round_num, min(fused_scores.values()) if fused_scores else 0,
                                  "PASS_WITH_NOTES", len(crit_errors),
                                  f"Validator errors: {'; '.join(crit_errors[:3])}", "repair")
            return GateResult("ESCALATE", round_num, min(fused_scores.values()) if fused_scores else 0,
                              "PASS_WITH_NOTES", len(crit_errors),
                              f"Validator errors after {round_num} rounds", "escalate")

    if evidence_errors:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, min(fused_scores.values()) if fused_scores else 0,
                              "PASS_WITH_NOTES", len(evidence_errors),
                              f"Evidence errors: {'; '.join(evidence_errors[:3])}", "repair")
        return GateResult("ESCALATE", round_num, min(fused_scores.values()) if fused_scores else 0,
                          "PASS_WITH_NOTES", len(evidence_errors),
                          f"Evidence errors after {round_num} rounds", "escalate")

    # Blocking findings from fused reviews
    blocking = [f for f in fused_findings if f.blocking]
    if blocking:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, min(fused_scores.values()) if fused_scores else 0,
                              "PASS_WITH_NOTES", len(blocking),
                              f"{len(blocking)} blocking findings (fused)", "repair")
        return GateResult("ESCALATE", round_num, min(fused_scores.values()) if fused_scores else 0,
                          "PASS_WITH_NOTES", len(blocking),
                          f"{len(blocking)} blocking findings after {round_num} rounds (fused)", "escalate")

    # Score below threshold (check all reviewers)
    min_score = min(fused_scores.values()) if fused_scores else 0
    if min_score < score_min:
        if round_num < max_repair:
            return GateResult("REPAIR", round_num, min_score, "PASS_WITH_NOTES", 0,
                              f"Score {min_score} < {score_min} (fused min)", "repair")
        return GateResult("ESCALATE", round_num, min_score, "PASS_WITH_NOTES", 0,
                          f"Score {min_score} < {score_min} after {round_num} rounds (fused)", "escalate")

    # All verdicts accepted
    all_accept = all(v in ACCEPT_VERDICTS for v in fused_verdicts.values())
    if all_accept:
        avg_score = sum(fused_scores.values()) / len(fused_scores) if fused_scores else 0
        return GateResult("ACCEPT", round_num, int(avg_score), "PASS_WITH_NOTES", 0,
                          f"Avg score {avg_score:.0f}, all verdicts PASS (fused)", "done")

    # Some verdicts not accepted
    bad = [f"{r}={v}" for r, v in fused_verdicts.items() if v not in ACCEPT_VERDICTS]
    if round_num < max_repair:
        return GateResult("REPAIR", round_num, min(fused_scores.values()) if fused_scores else 0,
                          "PASS_WITH_NOTES", 0, f"Non-accept verdicts: {', '.join(bad)} (fused)", "repair")
    return GateResult("ESCALATE", round_num, min(fused_scores.values()) if fused_scores else 0,
                      "PASS_WITH_NOTES", 0,
                      f"Non-accept verdicts after {round_num} rounds: {', '.join(bad)} (fused)", "escalate")


# --- Worktree isolation ---

def create_worktree(run_dir: Path, subproblem_id: str) -> Optional[Path]:
    """Create an isolated git worktree for a subproblem. Returns worktree path or None."""
    wt_name = f"tf-{subproblem_id}-{now_id()}"
    wt_path = REPO_ROOT / ".claude" / "worktrees" / wt_name
    try:
        subprocess.run(
            ["git", "worktree", "add", str(wt_path), "--orphan", wt_name],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
        if wt_path.exists():
            return wt_path
    except Exception:
        pass
    return None


def cleanup_worktree(wt_path: Optional[Path]) -> None:
    """Remove a worktree after subproblem completes."""
    if not wt_path or not wt_path.exists():
        return
    try:
        subprocess.run(
            ["git", "worktree", "remove", str(wt_path), "--force"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
    except Exception:
        pass


def quarantine_worktree(wt_path: Optional[Path], run_dir: Path, subproblem_id: str) -> None:
    """On failure, quarantine worktree changes instead of discarding."""
    if not wt_path or not wt_path.exists():
        return
    quarantine_dir = run_dir / "quarantine" / subproblem_id
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(wt_path), str(quarantine_dir / "worktree"))
    except Exception:
        # If move fails, at least log it
        pass


# --- Main orchestration loop ---

def run_orchestrate(task_path: Path, mode: str, timeout: int) -> None:
    task = load_yaml(task_path)
    run_id = now_id()
    run_dir = REPO_ROOT / "runs" / "orchestration" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    write_yaml(run_dir / "task.yaml", task)
    append_event(run_dir, {"event": "run_start", "task_id": task.get("task_id", "unknown"), "mode": mode})

    budget = BudgetLedger(start_time=time.time())
    state = load_run_state(run_dir)

    use_worktree = task.get("worktree_isolation", False)
    use_validators = task.get("run_validators", True)

    print(f"Run ID: {run_id}")
    print(f"Run dir: {run_dir}")
    print(f"Mode: {mode}")
    print(f"Worktree isolation: {use_worktree}")
    print(f"Validators: {use_validators}")
    print()

    for sub in task.get("subproblems", []):
        # Resume: skip completed subproblems
        if state.is_done(sub["id"]):
            prev = state.completed[sub["id"]]
            print(f"--- Subproblem: {sub['id']} --- (already done: {prev['gate_status']}, score={prev['score']})")
            continue

        print(f"--- Subproblem: {sub['id']} ---")

        # Check budget before starting
        max_iter = task.get("budget", {}).get("max_iterations", 10)
        max_tokens = task.get("budget", {}).get("max_tokens", 0)
        budget_exceeded = budget.check_budget(max_iter, max_tokens, timeout)
        if budget_exceeded:
            print(f"  BUDGET EXCEEDED: {budget_exceeded}")
            append_event(run_dir, {"event": "budget_exceeded", "detail": budget_exceeded})
            break

        # Worktree isolation
        wt_path = create_worktree(run_dir, sub["id"]) if use_worktree else None
        effective_run_dir = wt_path if wt_path else run_dir

        try:
            # Dispatch agent
            artifact_path = dispatch_agent(mode, task, sub, effective_run_dir, timeout)
            print(f"  Artifact: {artifact_path}")
            append_event(run_dir, {"event": "agent_dispatched", "subproblem": sub["id"]})

            if mode == "queue":
                prompt_path = effective_run_dir / "prompts" / f"{sub['id']}_agent_prompt.md"
                print(f"  Prompt queued: {prompt_path}")
                print(f"  -> Run Agent tool with subagent_type={sub.get('subagent_type', 'Plan')}")
                print(f"  -> Write output to {artifact_path}")
                if wt_path:
                    print(f"  -> Worktree: {wt_path}")
                print()
                continue

            # Dispatch review
            review_path = dispatch_review(mode, task, sub, artifact_path, effective_run_dir, timeout)
            print(f"  Review: {review_path}")
            append_event(run_dir, {"event": "review_dispatched", "subproblem": sub["id"]})

            if mode == "queue":
                prompt_path = effective_run_dir / "prompts" / f"{sub['id']}_review_prompt.md"
                print(f"  Review prompt queued: {prompt_path}")
                print()
                continue

            # Run deterministic validators
            v_errors: List[str] = []
            if use_validators:
                artifact_type = sub.get("artifact_type", "")
                v_errors = validate_artifact(artifact_path, artifact_type)
                if v_errors:
                    print(f"  Validator errors: {len(v_errors)}")
                    for ve in v_errors:
                        print(f"    {ve}")

            # Parse and gate
            review_text = review_path.read_text(encoding="utf-8")
            review = parse_review(review_text)
            artifact_exists = artifact_path.exists()

            # Validate evidence for blocking findings
            e_errors = validate_evidence(review, effective_run_dir)

            gate = evaluate_gate(task, review, 1, artifact_exists,
                                 validator_errors=v_errors or None,
                                 evidence_errors=e_errors or None)
            gate_yaml = gate_result_yaml(gate)

            gate_path = run_dir / "gate_results" / f"{sub['id']}_round_1.yaml"
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            gate_path.write_text(gate_yaml, encoding="utf-8")

            # Update budget and state
            budget.tick(sub["id"], 1, gate.status, gate.score)
            state.mark_done(sub["id"], gate.status, gate.score, 1)
            save_run_state(run_dir, state)

            print(f"  Gate: {gate.status} (score={gate.score}, verdict={gate.verdict})")
            print(f"  Reason: {gate.reason}")
            append_event(run_dir, {"event": "gate_evaluated", "subproblem": sub["id"],
                                   "status": gate.status, "score": gate.score,
                                   "validator_errors": len(v_errors)})
            print()

            # Cleanup worktree on success
            if wt_path:
                # Copy artifacts back to run_dir before cleanup
                if artifact_path.exists():
                    dest = run_dir / sub["artifact_path"]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(artifact_path, dest)
                if review_path.exists():
                    dest = run_dir / sub["review_path"]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(review_path, dest)
                cleanup_worktree(wt_path)

        except Exception as e:
            # Rollback: quarantine worktree changes
            print(f"  ERROR: {e}")
            append_event(run_dir, {"event": "subproblem_error", "subproblem": sub["id"], "error": str(e)})
            if wt_path:
                quarantine_worktree(wt_path, run_dir, sub["id"])
                print(f"  Worktree quarantined to {run_dir / 'quarantine' / sub['id']}")
            raise

    # Write budget ledger
    write_yaml(run_dir / "budget_ledger.yaml", budget.to_dict())
    append_event(run_dir, {"event": "run_complete", "iterations": budget.iterations})

    # Generate closeout
    generate_closeout(run_dir)

    print(f"Done. {budget.iterations} iterations, {budget.wall_seconds:.1f}s wall time.")
    print(f"Budget ledger: {run_dir / 'budget_ledger.yaml'}")


def generate_closeout(run_dir: Path) -> None:
    """Generate final_verdict.yaml and synthesis.md at end of run."""
    task_path = run_dir / "task.yaml"
    budget_path = run_dir / "budget_ledger.yaml"
    state_path = run_dir / "run_state.json"

    if not task_path.exists():
        return

    task = load_yaml(task_path)
    budget = load_yaml(budget_path) if budget_path.exists() else {}
    state = load_run_state(run_dir)

    # Collect gate results
    gate_results = []
    gate_dir = run_dir / "gate_results"
    if gate_dir.exists():
        for gf in sorted(gate_dir.glob("*.yaml")):
            gate_results.append(load_yaml(gf))

    # Determine overall verdict
    statuses = [gr.get("status", "") for gr in gate_results]
    if all(s == "ACCEPT" for s in statuses):
        overall = "PASS"
    elif any(s == "REJECT" for s in statuses):
        overall = "FAIL"
    elif any(s == "ESCALATE" for s in statuses):
        overall = "ESCALATE"
    else:
        overall = "PASS_WITH_NOTES"

    # Write final_verdict.yaml
    verdict_data = {
        "run_id": run_dir.name,
        "task_id": task.get("task_id", "unknown"),
        "overall_verdict": overall,
        "subproblems": {
            sub_id: {
                "gate_status": info.get("gate_status"),
                "score": info.get("score"),
            }
            for sub_id, info in state.completed.items()
        },
        "budget": {
            "iterations": budget.get("iterations", 0),
            "wall_seconds": budget.get("wall_seconds", 0),
        },
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    write_yaml(run_dir / "final_verdict.yaml", verdict_data)

    # Write synthesis.md
    scores = [gr.get("score") for gr in gate_results if gr.get("score")]
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    synthesis_lines = [
        f"# Synthesis: {task.get('title', task.get('task_id', 'unknown'))}",
        "",
        f"**Overall verdict**: {overall}",
        f"**Average score**: {avg_score}/100",
        f"**Subproblems**: {len(state.completed)} completed",
        f"**Iterations**: {budget.get('iterations', 0)}",
        f"**Wall time**: {budget.get('wall_seconds', 0):.1f}s",
        "",
        "## Gate Results",
        "",
    ]
    for gr in gate_results:
        synthesis_lines.append(
            f"- **{gr.get('round', '?')}**: {gr.get('status', '?')} "
            f"(score={gr.get('score', '?')}, verdict={gr.get('verdict', '?')})"
        )
        synthesis_lines.append(f"  - {gr.get('reason', 'no reason')}")

    synthesis_lines.extend([
        "",
        "## Budget",
        "",
        f"- Start: {budget.get('start_time', 'unknown')}",
        f"- Iterations: {budget.get('iterations', 0)}",
        f"- Wall seconds: {budget.get('wall_seconds', 0)}",
    ])

    if budget.get("rounds"):
        synthesis_lines.extend(["", "## Round Details", ""])
        for r in budget["rounds"]:
            synthesis_lines.append(
                f"- {r.get('subproblem', '?')} round {r.get('round', '?')}: "
                f"{r.get('gate_status', '?')} (score={r.get('score', '?')})"
            )

    synthesis_lines.extend([
        "",
        "## Next Experiment",
        "",
        "TBD — derive from findings and verdict.",
        "",
    ])

    (run_dir / "synthesis.md").write_text("\n".join(synthesis_lines), encoding="utf-8")
    print(f"Closeout generated: {run_dir / 'final_verdict.yaml'}")
    print(f"                  {run_dir / 'synthesis.md'}")


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

        # Run validators if configured
        v_errors: List[str] = []
        if task.get("run_validators", True):
            v_errors = validate_artifact(artifact_path, sub.get("artifact_type", ""))

        # Validate evidence
        e_errors = validate_evidence(review, run_dir)

        gate = evaluate_gate(task, review, round_num, artifact_path.exists(),
                             validator_errors=v_errors or None,
                             evidence_errors=e_errors or None)

        gate_path = run_dir / "gate_results" / f"{sub['id']}_round_{round_num}.yaml"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(gate_result_yaml(gate), encoding="utf-8")

        print(f"Subproblem: {sub['id']}")
        print(f"  Status: {gate.status}")
        print(f"  Score: {gate.score}, Verdict: {gate.verdict}")
        print(f"  Reason: {gate.reason}")
        if v_errors:
            print(f"  Validator errors: {len(v_errors)}")
            for ve in v_errors:
                print(f"    {ve}")
        print()


def run_validate(artifact_path: Path, artifact_type: str) -> None:
    """Run validators on a single artifact."""
    errors = validate_artifact(artifact_path, artifact_type)
    if errors:
        print(f"FAIL: {artifact_path.name}")
        for e in sorted(errors):
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"PASS: {artifact_path.name} (all validators passed)")


def run_fuse(review_files: List[Path], score_min: int = 80) -> None:
    """Fuse multiple review files and evaluate fused gate."""
    from review_fusion import load_review, fuse_reviews, fused_to_yaml

    reviews = []
    for f in review_files:
        if not f.exists():
            print(f"ERROR: {f} not found")
            sys.exit(1)
        review, reviewer = load_review(f)
        reviews.append((review, reviewer))
        print(f"Loaded: {f.name} (reviewer={reviewer}, score={review.score}, verdict={review.verdict})")

    if len(reviews) < 2:
        print("ERROR: Need at least 2 reviews to fuse")
        sys.exit(1)

    fused = fuse_reviews(reviews, score_min=score_min)

    print(f"\n=== Fused Gate ===")
    print(f"Scores: {fused.scores}")
    print(f"Verdicts: {fused.verdicts}")
    print(f"Blocking findings: {len(fused.blocking_findings)}")
    print(f"Disagreements: {len(fused.reviewer_disagreements)}")
    print(f"Decision: {fused.final_gate_decision}")
    print(f"Reason: {fused.fusion_reason}")

    # Write fused review YAML
    output_dir = review_files[0].parent.parent / "gate_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "fused_review.yaml"
    output_path.write_text(fused_to_yaml(fused), encoding="utf-8")
    print(f"\nWritten: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Token Furnace Orchestrator")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run orchestration")
    run_p.add_argument("task_yaml", type=Path, help="Path to task YAML")
    run_p.add_argument("--mode", choices=["queue", "mock", "command", "bridge"], default="mock")
    run_p.add_argument("--timeout", type=int, default=300)

    gate_p = sub.add_parser("gate", help="Evaluate gate for existing run")
    gate_p.add_argument("run_dir", type=Path)
    gate_p.add_argument("round_num", type=int, nargs="?", default=1)

    validate_p = sub.add_parser("validate", help="Run validators on an artifact")
    validate_p.add_argument("artifact_path", type=Path)
    validate_p.add_argument("--type", dest="artifact_type", default="",
                            help="Artifact type (state_machine, review, etc.)")

    closeout_p = sub.add_parser("closeout", help="Generate closeout for existing run")
    closeout_p.add_argument("run_dir", type=Path)

    fuse_p = sub.add_parser("fuse", help="Fuse multiple reviews into a single gate decision")
    fuse_p.add_argument("review_files", nargs="+", type=Path, help="Review markdown files")
    fuse_p.add_argument("--score-min", type=int, default=80)

    args = parser.parse_args()

    if args.command == "run":
        run_orchestrate(args.task_yaml, args.mode, args.timeout)
    elif args.command == "gate":
        run_gate(args.run_dir, args.round_num)
    elif args.command == "validate":
        run_validate(args.artifact_path, args.artifact_type)
    elif args.command == "closeout":
        generate_closeout(args.run_dir)
    elif args.command == "fuse":
        run_fuse(args.review_files, args.score_min)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
