#!/usr/bin/env python3
"""
Routing Outcome Update: record the actual result of a routing decision
into routing_memory.jsonl for future learning.
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTING_MEMORY = REPO_ROOT / "knowledge" / "orchestrator" / "routing_memory.jsonl"


@dataclass
class RoutingOutcome:
    route_id: str
    selected_strategy: str
    predicted_confidence: float
    actual_gate_result: str
    repair_rounds: int
    false_accept: bool
    validators_failed: List[str]
    escalation_needed: bool
    wall_time: float
    success: bool
    timestamp: str

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


def record_outcome(route_id: str, strategy: str, predicted_confidence: float,
                   actual_gate: str, repair_rounds: int = 0,
                   false_accept: bool = False, validators_failed: list = None,
                   escalation_needed: bool = False, wall_time: float = 0,
                   success: bool = True) -> RoutingOutcome:
    """Record a routing outcome."""
    outcome = RoutingOutcome(
        route_id=route_id,
        selected_strategy=strategy,
        predicted_confidence=predicted_confidence,
        actual_gate_result=actual_gate,
        repair_rounds=repair_rounds,
        false_accept=false_accept,
        validators_failed=validators_failed or [],
        escalation_needed=escalation_needed,
        wall_time=wall_time,
        success=success,
        timestamp=datetime.now().isoformat(),
    )

    ROUTING_MEMORY.parent.mkdir(parents=True, exist_ok=True)
    with open(ROUTING_MEMORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(outcome), ensure_ascii=False) + "\n")

    return outcome


def load_outcomes() -> list:
    if not ROUTING_MEMORY.exists():
        return []
    outcomes = []
    for line in ROUTING_MEMORY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            outcomes.append(json.loads(line))
    return outcomes


def compute_metrics() -> Dict:
    """Compute routing metrics from recorded outcomes."""
    outcomes = load_outcomes()
    if not outcomes:
        return {"total_routes": 0}

    total = len(outcomes)
    successes = sum(1 for o in outcomes if o.get("success"))
    escalations = sum(1 for o in outcomes if o.get("escalation_needed"))

    # Confidence gap
    gaps = []
    for o in outcomes:
        predicted = o.get("predicted_confidence", 0.5)
        actual = 1.0 if o.get("actual_gate_result") in ("ACCEPT", "PASS", "PASS_WITH_NOTES") else 0.0
        gaps.append(abs(predicted - actual))
    avg_gap = sum(gaps) / len(gaps) if gaps else 0

    # Strategy distribution
    strategies = {}
    for o in outcomes:
        s = o.get("selected_strategy", "unknown")
        strategies[s] = strategies.get(s, 0) + 1

    return {
        "total_routes": total,
        "success_rate": successes / total,
        "escalation_rate": escalations / total,
        "avg_confidence_gap": round(avg_gap, 3),
        "strategy_distribution": strategies,
        "avg_repair_rounds": sum(o.get("repair_rounds", 0) for o in outcomes) / total,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: routing_outcome_update.py record <route_id> <strategy> <confidence> <gate_result>")
        print("       routing_outcome_update.py metrics")
        sys.exit(1)

    action = sys.argv[1]

    if action == "record":
        if len(sys.argv) < 6:
            print("Usage: routing_outcome_update.py record <route_id> <strategy> <confidence> <gate_result>")
            sys.exit(1)
        outcome = record_outcome(
            route_id=sys.argv[2],
            strategy=sys.argv[3],
            predicted_confidence=float(sys.argv[4]),
            actual_gate=sys.argv[5],
        )
        print(f"Recorded: {outcome.route_id} → {outcome.actual_gate_result}")

    elif action == "metrics":
        metrics = compute_metrics()
        print(json.dumps(metrics, indent=2))

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
