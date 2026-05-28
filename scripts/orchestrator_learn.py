#!/usr/bin/env python3
"""
Orchestrator Learning Extractor: ingest run outcomes, extract lessons,
generate policy suggestions and update outcome memory.

Usage:
  python3 scripts/orchestrator_learn.py ingest               # Ingest all runs into outcome_memory.jsonl
  python3 scripts/orchestrator_learn.py suggest               # Generate policy suggestions
  python3 scripts/orchestrator_learn.py stats                 # Print learning metrics
  python3 scripts/orchestrator_learn.py check-self-modify <suggestion.yaml>  # Gate check for self-modification
"""

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"
KNOWLEDGE_DIR = REPO_ROOT / "knowledge" / "orchestrator"
OUTCOME_MEMORY = KNOWLEDGE_DIR / "outcome_memory.jsonl"
POLICY_REGISTRY = KNOWLEDGE_DIR / "policy_registry.yaml"
POLICY_SUGGESTIONS = KNOWLEDGE_DIR / "policy_suggestions.yaml"


@dataclass
class RunOutcome:
    run_id: str
    task_id: str
    task_type: str
    input_complexity: str  # low, medium, high
    agents_used: List[str]
    validators_used: List[str]
    initial_gate: str
    final_gate: str
    repair_rounds: int
    false_accept: bool
    blocking_findings_count: int
    new_findings_after_repair: int
    cascade_defect_detected: bool
    bugs_found_in_orchestrator: int
    time_wall_seconds: float
    human_intervention: str
    lessons: List[str]
    recommended_policy_changes: List[str]


# --- Run discovery ---

def discover_runs() -> List[Dict]:
    """Find all orchestration runs across both directory schemas."""
    runs = []

    # Schema 1: runs/orchestration/<timestamp>/
    orch_dir = RUNS_DIR / "orchestration"
    if orch_dir.exists():
        for ts_dir in sorted(orch_dir.iterdir()):
            if not ts_dir.is_dir():
                continue
            verdict_file = ts_dir / "final_verdict.yaml"
            synthesis_file = ts_dir / "synthesis.md"
            task_file = ts_dir / "task.yaml"
            events_file = ts_dir / "events.jsonl"

            if not task_file.exists():
                continue

            task_data = _safe_yaml(task_file)
            verdict_data = _safe_yaml(verdict_file) if verdict_file.exists() else {}
            synthesis_text = synthesis_file.read_text(encoding="utf-8") if synthesis_file.exists() else ""
            events = _read_events(events_file) if events_file.exists() else []

            runs.append({
                "run_id": ts_dir.name,
                "task_data": task_data,
                "verdict_data": verdict_data,
                "synthesis_text": synthesis_text,
                "events": events,
                "schema": "old",
                "path": str(ts_dir),
            })

    # Schema 2: runs/orchestration-NNN/<timestamp>/run.yaml
    for pattern in ["orchestration-003", "orchestration-006", "orchestration-007", "orchestration-008"]:
        pattern_dir = RUNS_DIR / pattern
        if not pattern_dir.exists():
            continue
        for ts_dir in sorted(pattern_dir.iterdir()):
            if not ts_dir.is_dir():
                continue
            run_file = ts_dir / "run.yaml"
            synthesis_dir = ts_dir / "synthesis"
            synthesis_file = synthesis_dir / "synthesis.md" if synthesis_dir.exists() else None

            if not run_file.exists():
                continue

            run_data = _safe_yaml(run_file)
            synthesis_text = synthesis_file.read_text(encoding="utf-8") if synthesis_file and synthesis_file.exists() else ""

            runs.append({
                "run_id": f"{pattern}/{ts_dir.name}",
                "task_data": run_data,
                "verdict_data": run_data,
                "synthesis_text": synthesis_text,
                "events": [],
                "schema": "new",
                "path": str(ts_dir),
            })

        # Flat directory (orchestration-003)
        synthesis_file = pattern_dir / "synthesis.md"
        if synthesis_file.exists() and not any(r["run_id"].startswith(pattern) for r in runs):
            synthesis_text = synthesis_file.read_text(encoding="utf-8")
            runs.append({
                "run_id": pattern,
                "task_data": {},
                "verdict_data": {},
                "synthesis_text": synthesis_text,
                "events": [],
                "schema": "flat",
                "path": str(pattern_dir),
            })

    return runs


def _safe_yaml(path: Path) -> dict:
    if yaml is None:
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _read_events(path: Path) -> List[dict]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


# --- Lesson extraction ---

LESSON_PATTERNS = [
    {
        "pattern": r"blocking.*union|findings.*union",
        "lesson": "Blocking findings must take union across reviewers, not average",
        "source_rule": "POL-002",
    },
    {
        "pattern": r"cascade.*defect|dangling.*target|expose.*downstream",
        "lesson": "Fixing one dangling target exposes related cascade defects in same sequence",
        "source_rule": "POL-004",
    },
    {
        "pattern": r"validator.*fail.*override|validator.*must.*reject",
        "lesson": "Schema/validator failure must override reviewer score — no exceptions",
        "source_rule": "POL-001",
    },
    {
        "pattern": r"cross.?audit|different.*safety.*gap|multiple.*reviewer",
        "lesson": "Multiple reviewers发现 different safety gaps — cross-audit adds real value",
        "source_rule": "POL-005",
    },
    {
        "pattern": r"timeout.*classifier|transition.*semantics",
        "lesson": "Timeout/transition semantics require dedicated classifier, not generic review",
        "source_rule": "POL-003",
    },
    {
        "pattern": r"confidence.*synth|合成.*confidence|multi.*source.*confidence",
        "lesson": "Confidence must synthesize validator + evidence + review convergence, not just model self-report",
        "source_rule": "POL-006",
    },
    {
        "pattern": r"failure.?injection|false.?accept.*prevent",
        "lesson": "Failure injection is essential regression test against false ACCEPT",
        "source_rule": "POL-007",
    },
    {
        "pattern": r"parallel.*dispatch.*可行|merge.*不能太早",
        "lesson": "Parallel artifact dispatch works but merge must not be automated too early",
        "source_rule": "POL-008",
    },
]


def extract_lessons(synthesis_text: str) -> List[str]:
    """Extract reusable lessons from synthesis text."""
    found = []
    for lp in LESSON_PATTERNS:
        if re.search(lp["pattern"], synthesis_text, re.IGNORECASE):
            found.append(lp["lesson"])
    return found


def extract_recommended_changes(synthesis_text: str) -> List[str]:
    """Extract recommended policy changes from synthesis text."""
    changes = []
    lines = synthesis_text.split("\n")
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in ["recommend", "should", "add", "after.*repair", "run.*classifier", "cascade.*scan"]):
            clean = line.strip().lstrip("- *•")
            if len(clean) > 10 and clean not in changes:
                changes.append(clean)
    return changes[:5]  # cap at 5


# --- Outcome memory generation ---

def build_run_outcome(run: Dict) -> RunOutcome:
    """Build a RunOutcome from discovered run data."""
    td = run["task_data"]
    vd = run["verdict_data"]
    synth = run["synthesis_text"]
    events = run["events"]

    # Determine task type and complexity
    task_id = td.get("task_id", td.get("title", run["run_id"]))
    task_type = _classify_task_type(task_id, synth)
    complexity = _assess_complexity(events, synth)

    # Gate results
    initial_gate = vd.get("overall_verdict", vd.get("verdict", "UNKNOWN"))
    final_gate = initial_gate

    # Repair rounds from events
    repair_rounds = sum(1 for e in events if e.get("type") == "repair")

    # Blocking findings
    blocking = _count_blocking(synth)

    # Cascade detection
    cascade = bool(re.search(r"cascade|dangling.*expose|expose.*downstream", synth, re.IGNORECASE))

    # Bugs in orchestrator
    bugs = 0
    if re.search(r"bug.*fix|fixed.*bug|3 bugs", synth, re.IGNORECASE):
        bugs_match = re.search(r"(\d+)\s*bug", synth, re.IGNORECASE)
        bugs = int(bugs_match.group(1)) if bugs_match else 1

    # Wall time
    wall = vd.get("budget", {}).get("wall_seconds", 0)

    # Lessons
    lessons = extract_lessons(synth)
    changes = extract_recommended_changes(synth)

    return RunOutcome(
        run_id=run["run_id"],
        task_id=task_id,
        task_type=task_type,
        input_complexity=complexity,
        agents_used=_detect_agents(td, events),
        validators_used=_detect_validators(td, synth),
        initial_gate=initial_gate,
        final_gate=final_gate,
        repair_rounds=repair_rounds,
        false_accept=False,
        blocking_findings_count=blocking,
        new_findings_after_repair=0,
        cascade_defect_detected=cascade,
        bugs_found_in_orchestrator=bugs,
        time_wall_seconds=wall,
        human_intervention="none",
        lessons=lessons,
        recommended_policy_changes=changes,
    )


def _classify_task_type(task_id: str, synth: str) -> str:
    lower = (task_id + " " + synth[:500]).lower()
    if "failure" in lower and "inject" in lower:
        return "failure_injection"
    if "cross" in lower and "audit" in lower:
        return "cross_audit"
    if "fusion" in lower or "merge" in lower:
        return "review_fusion"
    if "repair" in lower:
        return "repair_benchmark"
    if "parallel" in lower or "worktree" in lower:
        return "parallel_dispatch"
    if "confidence" in lower or "escalat" in lower:
        return "confidence_calibration"
    if "schema" in lower:
        return "schema_enforcement"
    if "pipeline" in lower or "mock" in lower:
        return "basic_pipeline"
    return "unknown"


def _assess_complexity(events: List[dict], synth: str) -> str:
    if len(events) > 20 or "cascade" in synth.lower():
        return "high"
    if len(events) > 5 or "repair" in synth.lower():
        return "medium"
    return "low"


def _count_blocking(synth: str) -> int:
    match = re.search(r"(\d+)\s*blocking", synth, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _detect_agents(td: dict, events: List[dict]) -> List[str]:
    agents = set()
    text = json.dumps(td) + json.dumps(events[:5])
    if "claude" in text.lower():
        agents.add("claude")
    if "gpt" in text.lower():
        agents.add("gpt")
    return sorted(agents) or ["unknown"]


def _detect_validators(td: dict, synth: str) -> List[str]:
    validators = set()
    text = json.dumps(td) + synth[:1000]
    if "schema" in text.lower():
        validators.add("schema")
    if "failure" in text.lower() and "inject" in text.lower():
        validators.add("failure_injection")
    if "timeout" in text.lower():
        validators.add("timeout_classifier")
    if "review" in text.lower():
        validators.add("review_validator")
    return sorted(validators) or ["unknown"]


# --- Policy suggestion generation ---

def generate_suggestions(outcomes: List[RunOutcome]) -> List[Dict]:
    """Generate policy suggestions from outcome patterns."""
    suggestions = []
    seen_patterns = set()

    # Pattern: cascade defects
    cascade_runs = [o for o in outcomes if o.cascade_defect_detected]
    if len(cascade_runs) >= 2:
        key = "cascade_scan"
        if key not in seen_patterns:
            seen_patterns.add(key)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "state_machine_repair_with_dangling_target",
                "observed_in": [o.run_id for o in cascade_runs],
                "suggestion": "After any dangling-state repair, run cascade target scan on same sequence.",
                "confidence": "high",
                "proposed_change_type": "validator_rule",
                "risk": "low",
                "requires_human_approval": False,
            })

    # Pattern: cross-audit value
    cross_runs = [o for o in outcomes if o.task_type == "cross_audit"]
    if cross_runs:
        key = "cross_audit"
        if key not in seen_patterns:
            seen_patterns.add(key)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "multi_model_artifact_review",
                "observed_in": [o.run_id for o in cross_runs],
                "suggestion": "Cross-audit by different model class catches safety gaps single reviewer misses.",
                "confidence": "high",
                "proposed_change_type": "prompt_rule",
                "risk": "low",
                "requires_human_approval": False,
            })

    # Pattern: timeout classifier needed
    timeout_runs = [o for o in outcomes if "timeout" in " ".join(o.lessons).lower()]
    if timeout_runs:
        key = "timeout"
        if key not in seen_patterns:
            seen_patterns.add(key)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "timeout_transition_findings",
                "observed_in": [o.run_id for o in timeout_runs],
                "suggestion": "Route timeout/transition semantics to dedicated classifier before accepting.",
                "confidence": "high",
                "proposed_change_type": "gate_policy",
                "risk": "low",
                "requires_human_approval": False,
            })

    # Pattern: failure injection essential
    fi_runs = [o for o in outcomes if o.task_type == "failure_injection"]
    if fi_runs:
        key = "failure_injection"
        if key not in seen_patterns:
            seen_patterns.add(key)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "gate_policy_change",
                "observed_in": [o.run_id for o in fi_runs],
                "suggestion": "Any gate policy change must be validated with failure injection before activation.",
                "confidence": "high",
                "proposed_change_type": "meta_validator",
                "risk": "low",
                "requires_human_approval": False,
            })

    # Pattern: confidence synthesis
    conf_runs = [o for o in outcomes if o.task_type == "confidence_calibration"]
    if conf_runs:
        key = "confidence"
        if key not in seen_patterns:
            seen_patterns.add(key)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "gate_decision_with_multiple_reviewers",
                "observed_in": [o.run_id for o in conf_runs],
                "suggestion": "Confidence must synthesize validator + evidence + reviewer convergence, not just self-report.",
                "confidence": "high",
                "proposed_change_type": "gate_policy",
                "risk": "low",
                "requires_human_approval": False,
            })

    # Pattern: repair success rate
    repair_runs = [o for o in outcomes if o.repair_rounds > 0]
    if len(repair_runs) >= 2:
        key = "repair_rate"
        if key not in seen_patterns:
            seen_patterns.add(key)
            avg_rounds = sum(o.repair_rounds for o in repair_runs) / len(repair_runs)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "repair_rounds_exceed_threshold",
                "observed_in": [o.run_id for o in repair_runs],
                "suggestion": f"After {int(avg_rounds)+1} repair rounds, escalate to human. Average was {avg_rounds:.1f}.",
                "confidence": "medium",
                "proposed_change_type": "gate_policy",
                "risk": "low",
                "requires_human_approval": False,
            })

    # Pattern: repeated LOW findings informational
    low_runs = [o for o in outcomes if o.blocking_findings_count == 0 and o.final_gate in ("ACCEPT", "PASS", "PASS_WITH_NOTES")]
    if low_runs:
        key = "low_findings"
        if key not in seen_patterns:
            seen_patterns.add(key)
            suggestions.append({
                "id": f"PS-{len(suggestions)+1:03d}",
                "trigger_pattern": "multiple_low_findings_no_blocking",
                "observed_in": [o.run_id for o in low_runs],
                "suggestion": "Repeated LOW findings without blocking are informational, not REPAIR triggers.",
                "confidence": "high",
                "proposed_change_type": "gate_policy",
                "risk": "low",
                "requires_human_approval": False,
            })

    return suggestions


# --- Safety gate for self-modification ---

SAFE_CHANGE_TYPES = {"validator_rule", "prompt_rule", "report_field", "meta_validator"}
REVIEW_CHANGE_TYPES = {"gate_policy", "threshold_change"}
BLOCKED_CHANGE_TYPES = {"auto_merge", "weaken_validator", "reduce_escalation"}

CHANGE_RISK_LEVELS = {
    "validator_rule": "low",
    "prompt_rule": "low",
    "report_field": "low",
    "meta_validator": "low",
    "gate_policy": "medium",
    "threshold_change": "medium",
    "auto_merge": "high",
    "weaken_validator": "high",
    "reduce_escalation": "high",
}


def check_self_modify(suggestion: Dict) -> Dict:
    """Check if a policy suggestion is safe for autonomous application."""
    change_type = suggestion.get("proposed_change_type", "unknown")
    risk = CHANGE_RISK_LEVELS.get(change_type, "high")

    if change_type in BLOCKED_CHANGE_TYPES:
        return {
            "allowed": False,
            "risk": "high",
            "reason": f"Change type '{change_type}' requires human approval — weakens safety",
            "requires_human_approval": True,
        }

    if change_type in REVIEW_CHANGE_TYPES:
        return {
            "allowed": True,
            "risk": "medium",
            "reason": f"Change type '{change_type}' requires cross-review before activation",
            "requires_human_approval": False,
            "apply_mode": "require_cross_review",
        }

    if change_type in SAFE_CHANGE_TYPES:
        return {
            "allowed": True,
            "risk": "low",
            "reason": f"Change type '{change_type}' can be applied autonomously with logging",
            "requires_human_approval": False,
            "apply_mode": "auto_with_log",
        }

    return {
        "allowed": False,
        "risk": "high",
        "reason": f"Unknown change type '{change_type}' — defaulting to blocked",
        "requires_human_approval": True,
    }


# --- Stats ---

def compute_stats(outcomes: List[RunOutcome]) -> Dict:
    """Compute learning metrics from outcomes."""
    if not outcomes:
        return {"total_runs": 0}

    total = len(outcomes)
    repair_runs = [o for o in outcomes if o.repair_rounds > 0]
    cascade_runs = [o for o in outcomes if o.cascade_defect_detected]

    all_lessons = []
    for o in outcomes:
        all_lessons.extend(o.lessons)

    return {
        "total_runs": total,
        "task_types": {t: sum(1 for o in outcomes if o.task_type == t)
                       for t in set(o.task_type for o in outcomes)},
        "gate_distribution": {g: sum(1 for o in outcomes if o.final_gate == g)
                              for g in set(o.final_gate for o in outcomes)},
        "avg_repair_rounds": sum(o.repair_rounds for o in outcomes) / total,
        "repair_rate": len(repair_runs) / total,
        "cascade_rate": len(cascade_runs) / total,
        "total_lessons": len(all_lessons),
        "unique_lessons": len(set(all_lessons)),
        "total_bugs_found": sum(o.bugs_found_in_orchestrator for o in outcomes),
    }


# --- Ingest to JSONL ---

def ingest_all():
    """Discover runs, build outcomes, write outcome_memory.jsonl."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    runs = discover_runs()
    print(f"Discovered {len(runs)} runs")

    outcomes = []
    for run in runs:
        outcome = build_run_outcome(run)
        outcomes.append(outcome)
        print(f"  {outcome.run_id}: {outcome.task_type} -> {outcome.final_gate} "
              f"({len(outcome.lessons)} lessons)")

    # Write JSONL
    with open(OUTCOME_MEMORY, "w", encoding="utf-8") as f:
        for o in outcomes:
            f.write(json.dumps(asdict(o), ensure_ascii=False) + "\n")

    print(f"\nWrote {len(outcomes)} outcomes to {OUTCOME_MEMORY}")

    # Stats
    stats = compute_stats(outcomes)
    print(f"\n=== Learning Metrics ===")
    print(f"Total runs: {stats['total_runs']}")
    print(f"Task types: {stats['task_types']}")
    print(f"Gate distribution: {stats['gate_distribution']}")
    print(f"Avg repair rounds: {stats['avg_repair_rounds']:.1f}")
    print(f"Cascade rate: {stats['cascade_rate']:.0%}")
    print(f"Unique lessons: {stats['unique_lessons']}")
    print(f"Total bugs found: {stats['total_bugs_found']}")

    return outcomes


def suggest_all(outcomes: Optional[List[RunOutcome]] = None):
    """Generate and write policy suggestions."""
    if outcomes is None:
        outcomes = []
        if OUTCOME_MEMORY.exists():
            for line in OUTCOME_MEMORY.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    data = json.loads(line)
                    outcomes.append(RunOutcome(**data))

    suggestions = generate_suggestions(outcomes)

    # Write YAML
    doc = {
        "generated_from": f"{len(outcomes)} run outcomes",
        "total_suggestions": len(suggestions),
        "suggestions": suggestions,
    }

    if yaml:
        with open(POLICY_SUGGESTIONS, "w", encoding="utf-8") as f:
            yaml.dump(doc, f, default_flow_style=False, allow_unicode=True)
    else:
        with open(POLICY_SUGGESTIONS, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(suggestions)} policy suggestions")
    for s in suggestions:
        safety = check_self_modify(s)
        print(f"  {s['id']}: {s['suggestion'][:80]}... [{s['risk']}] {'AUTO' if safety['apply_mode'] == 'auto_with_log' else 'REVIEW'}")

    return suggestions


def stats_only():
    """Print stats from existing outcome memory."""
    if not OUTCOME_MEMORY.exists():
        print("No outcome memory found. Run 'ingest' first.")
        return

    outcomes = []
    for line in OUTCOME_MEMORY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            outcomes.append(RunOutcome(**data))

    stats = compute_stats(outcomes)
    print(json.dumps(stats, indent=2))


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]

    if action == "ingest":
        ingest_all()

    elif action == "suggest":
        suggest_all()

    elif action == "stats":
        stats_only()

    elif action == "check-self-modify":
        if len(sys.argv) < 3:
            print("Usage: orchestrator_learn.py check-self-modify <suggestion.yaml>")
            sys.exit(1)
        path = Path(sys.argv[2])
        if yaml:
            suggestion = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            suggestion = json.loads(path.read_text(encoding="utf-8"))
        result = check_self_modify(suggestion)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
