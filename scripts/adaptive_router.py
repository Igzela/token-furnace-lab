#!/usr/bin/env python3
"""
Adaptive Router: match task profile against outcome memory and select routing strategy.
Three layers: Task Profiler → Memory Matcher → Routing Decision.
"""

import json
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "knowledge" / "orchestrator"
OUTCOME_MEMORY = KNOWLEDGE_DIR / "outcome_memory.jsonl"
ROUTING_MEMORY = KNOWLEDGE_DIR / "routing_memory.jsonl"
POLICY_REGISTRY = KNOWLEDGE_DIR / "policy_registry.yaml"
ROUTING_CONFIG = REPO_ROOT / "configs" / "routing_policy.yaml"
DECISIONS_DIR = REPO_ROOT / "runs" / "orchestration-011" / "20260528-170000" / "decisions"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from task_profiler import TaskProfile, profile_task


# --- Strategy definitions ---

STRATEGIES = {
    "simple_review": {
        "use_when": {"risk_level": "low", "safety_sensitive": False},
        "agents": ["claude_or_gpt_reviewer"],
        "gate": {"score_min": 75, "fusion_required": False},
        "execution": {"mode": "direct", "worktree": False, "parallel": False},
    },
    "cross_audit_review": {
        "use_when": {"risk_level": "high", "safety_sensitive": True},
        "agents": ["claude_reviewer", "gpt_reviewer"],
        "gate": {"score_min": 80, "fusion_required": True, "finding_union": True},
        "execution": {"mode": "bridge", "worktree": False, "parallel": False},
    },
    "closed_loop_repair": {
        "use_when": {"task_type": "repair"},
        "agents": ["claude_implementer", "gpt_reviewer"],
        "gate": {"score_min": 80, "max_repair_rounds": 2, "re_review_required": True},
        "execution": {"mode": "bridge", "worktree": False, "parallel": False},
    },
    "parallel_artifact_audit": {
        "use_when": {"requires_parallelism": True},
        "agents": ["multiple_plan_agents"],
        "gate": {"score_min": 80, "fusion_required": True},
        "execution": {"mode": "bridge", "worktree": True, "parallel": True},
    },
    "implementation_with_validators": {
        "use_when": {"requires_repo_write": True},
        "agents": ["claude_implementer"],
        "gate": {"score_min": 80, "tests_required": True, "schema_required": True},
        "execution": {"mode": "bridge", "worktree": True, "parallel": False},
    },
    "policy_application": {
        "use_when": {"task_type": "policy_update"},
        "agents": ["policy_engine"],
        "gate": {"auto_tighten_allowed": True, "auto_loosen_blocked": True, "regression_required": True},
        "execution": {"mode": "direct", "worktree": False, "parallel": False},
    },
    "derivation_with_cross_audit": {
        "use_when": {"task_type": "derivation", "domain": "control_system"},
        "agents": ["claude_implementer", "gpt_reviewer"],
        "gate": {"score_min": 82, "fusion_required": True, "max_repair_rounds": 2},
        "execution": {"mode": "bridge", "worktree": False, "parallel": False},
    },
}


@dataclass
class SimilarRun:
    run_id: str
    similarity: float
    task_type: str
    result: str
    useful_pattern: str
    warning: str


@dataclass
class RoutingDecision:
    strategy: str
    agents: List[str]
    validators: List[str]
    execution: Dict
    gate_policy: Dict
    escalation: Dict
    rationale: List[str]
    similar_runs: List[Dict]
    confidence: float


# --- Memory matching ---

def load_outcomes() -> List[Dict]:
    if not OUTCOME_MEMORY.exists():
        return []
    outcomes = []
    for line in OUTCOME_MEMORY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            outcomes.append(json.loads(line))
    return outcomes


def compute_similarity(profile: TaskProfile, outcome: Dict) -> float:
    """Compute weighted similarity between a task profile and a past outcome."""
    score = 0.0

    # Task type match (weight: 0.30)
    if profile.task_type == outcome.get("task_type", ""):
        score += 0.30
    elif profile.task_type in outcome.get("task_type", ""):
        score += 0.15

    # Domain match (weight: 0.20)
    # Use keyword overlap as proxy
    profile_kws = set(profile.keywords)
    outcome_text = json.dumps(outcome).lower()
    overlap = sum(1 for kw in profile_kws if kw in outcome_text)
    if overlap > 0:
        score += min(0.20, overlap * 0.05)

    # Risk level match (weight: 0.15)
    if profile.risk_level == outcome.get("input_complexity", ""):
        score += 0.15

    # Artifact type match (weight: 0.15)
    if profile.artifact_type in json.dumps(outcome).lower():
        score += 0.15

    # Validator overlap (weight: 0.10)
    if profile.requires_code_execution and "failure_injection" in json.dumps(outcome):
        score += 0.10

    # Safety sensitivity (weight: 0.10)
    if profile.safety_sensitive and outcome.get("cascade_defect_detected"):
        score += 0.10

    return min(1.0, score)


def find_similar_runs(profile: TaskProfile, top_k: int = 3) -> List[SimilarRun]:
    """Find most similar past runs from outcome memory."""
    outcomes = load_outcomes()
    scored = []
    for o in outcomes:
        sim = compute_similarity(profile, o)
        if sim > 0.1:
            scored.append((sim, o))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for sim, o in scored[:top_k]:
        gate = o.get("final_gate", "UNKNOWN")
        repair = o.get("repair_rounds", 0)
        cascade = o.get("cascade_defect_detected", False)

        pattern = "unknown"
        if repair > 0 and gate in ("ACCEPT", "PASS"):
            pattern = "closed_loop_repair"
        elif o.get("task_type") == "cross_audit":
            pattern = "cross_audit_value"
        elif o.get("task_type") == "parallel_dispatch":
            pattern = "parallel_execution"
        elif cascade:
            pattern = "cascade_defects"

        warning = ""
        if cascade:
            warning = "cascade defects appeared"
        elif repair > 1:
            warning = f"required {repair} repair rounds"

        results.append(SimilarRun(
            run_id=o.get("run_id", "unknown"),
            similarity=round(sim, 2),
            task_type=o.get("task_type", "unknown"),
            result=f"{gate} after {repair} rounds" if repair else gate,
            useful_pattern=pattern,
            warning=warning,
        ))

    return results


# --- Strategy selection ---

def select_strategy(profile: TaskProfile, similar_runs: List[SimilarRun]) -> Tuple[str, List[str]]:
    """Select routing strategy based on profile and similar runs."""
    rationale = []

    # Rule-based selection
    if profile.task_type == "policy_update":
        rationale.append("policy_update task → policy_application strategy")
        return "policy_application", rationale

    if profile.requires_parallelism:
        rationale.append("parallelism required → parallel_artifact_audit")
        return "parallel_artifact_audit", rationale

    if profile.task_type == "repair":
        rationale.append("repair task → closed_loop_repair")
        return "closed_loop_repair", rationale

    if profile.task_type == "derivation" and profile.domain == "control_system":
        rationale.append("derivation in control_system domain → derivation_with_cross_audit")
        return "derivation_with_cross_audit", rationale

    if profile.safety_sensitive or profile.risk_level in ("high", "safety_critical"):
        rationale.append(f"safety_sensitive={profile.safety_sensitive}, risk={profile.risk_level} → cross_audit_review")
        return "cross_audit_review", rationale

    if profile.requires_repo_write:
        rationale.append("repo write required → implementation_with_validators")
        return "implementation_with_validators", rationale

    # Check similar runs for patterns
    if similar_runs:
        best = similar_runs[0]
        if best.similarity > 0.5:
            if best.useful_pattern == "closed_loop_repair":
                rationale.append(f"similar to {best.run_id} (sim={best.similarity}) which used repair loop")
                return "closed_loop_repair", rationale
            elif best.useful_pattern == "cross_audit_value":
                rationale.append(f"similar to {best.run_id} (sim={best.similarity}) which benefited from cross-audit")
                return "cross_audit_review", rationale

    rationale.append("default → simple_review (low risk, no special requirements)")
    return "simple_review", rationale


def build_routing_decision(profile: TaskProfile, strategy_name: str,
                           similar_runs: List[SimilarRun], rationale: List[str]) -> RoutingDecision:
    """Build complete routing decision from profile and strategy."""
    strategy = STRATEGIES[strategy_name]

    # Validators
    validators = ["schema"]
    if profile.safety_sensitive:
        validators.append("evidence_path")
    if profile.task_type == "derivation":
        validators.append("timeout_classifier")
    if profile.requires_code_execution:
        validators.append("failure_injection")
    if profile.requires_repo_write:
        validators.append("scope_diff")

    # Escalation
    escalation_triggers = []
    if profile.risk_level in ("high", "safety_critical"):
        escalation_triggers.append("safety_critical_ambiguity")
    if profile.task_type == "repair":
        escalation_triggers.append("unresolved_high_after_2_rounds")
    escalation_triggers.append("validator_conflict")

    # Confidence
    confidence = 0.5
    if similar_runs:
        confidence = min(0.9, 0.5 + similar_runs[0].similarity * 0.4)
    if profile.has_known_pattern:
        confidence = min(0.95, confidence + 0.1)

    return RoutingDecision(
        strategy=strategy_name,
        agents=strategy["agents"],
        validators=validators,
        execution=strategy["execution"],
        gate_policy=strategy["gate"],
        escalation={"trigger": escalation_triggers},
        rationale=rationale,
        similar_runs=[asdict(r) for r in similar_runs],
        confidence=round(confidence, 2),
    )


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print("Usage: adaptive_router.py <task.yaml> | <text>")
        sys.exit(1)

    # Profile the task
    path = Path(sys.argv[1])
    if path.exists() and path.suffix in (".yaml", ".yml", ".json"):
        if yaml:
            task_data = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            task_data = json.loads(path.read_text(encoding="utf-8"))
        profile = profile_task(task_data)
    else:
        text = " ".join(sys.argv[1:])
        profile = profile_task(text)

    print(f"=== Task Profile ===")
    print(f"  type={profile.task_type}, domain={profile.domain}, risk={profile.risk_level}")
    print(f"  artifact={profile.artifact_type}, safety={profile.safety_sensitive}")
    print(f"  repo_write={profile.requires_repo_write}, parallel={profile.requires_parallelism}")

    # Find similar runs
    similar = find_similar_runs(profile)
    print(f"\n=== Similar Runs ({len(similar)}) ===")
    for r in similar:
        print(f"  {r.run_id}: sim={r.similarity}, type={r.task_type}, result={r.result}")
        if r.warning:
            print(f"    warning: {r.warning}")

    # Select strategy
    strategy_name, rationale = select_strategy(profile, similar)
    print(f"\n=== Routing Decision ===")
    print(f"  strategy: {strategy_name}")
    for r in rationale:
        print(f"  rationale: {r}")

    # Build full decision
    decision = build_routing_decision(profile, strategy_name, similar, rationale)

    # Write decision
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    decision_file = DECISIONS_DIR / "routing_decision.yaml"
    if yaml:
        decision_file.write_text(yaml.dump(asdict(decision), default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        decision_file.write_text(json.dumps(asdict(decision), indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  Decision written to {decision_file}")
    print(f"  confidence: {decision.confidence}")
    print(f"  agents: {decision.agents}")
    print(f"  validators: {decision.validators}")


if __name__ == "__main__":
    main()
