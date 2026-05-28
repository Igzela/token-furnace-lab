#!/usr/bin/env python3
"""
Task Profiler: extract machine-readable features from a task definition.
Input: task.yaml or task description text
Output: task_profile.json with structured features for routing.
"""

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class TaskProfile:
    task_type: str  # review, repair, implementation, derivation, validation, synthesis, benchmark, policy_update
    domain: str  # control_system, orchestrator, documentation, code, safety, hardware_model
    risk_level: str  # low, medium, high, safety_critical
    artifact_type: str  # markdown, json, yaml, python, c_code, matrix, test_report
    expected_output: str  # review, patch, report, validator, synthesis, final_verdict
    requires_repo_write: bool
    requires_code_execution: bool
    requires_external_review: bool
    requires_parallelism: bool
    safety_sensitive: bool
    has_known_pattern: bool
    complexity: dict  # subproblem_count, dependency_depth, expected_iterations
    keywords: List[str]


TYPE_KEYWORDS = {
    "review": ["review", "audit", "check", "verify", "validate", "re-review"],
    "repair": ["repair", "fix", "correct", "patch", "dangling", "missing"],
    "implementation": ["implement", "create", "build", "add", "new", "write"],
    "derivation": ["derivation", "derive", "calculate", "compute", "model", "simulation"],
    "validation": ["validate", "test", "benchmark", "regression", "failure injection"],
    "synthesis": ["synthesis", "summarize", "distill", "report", "closeout"],
    "benchmark": ["benchmark", "performance", "compare", "measure"],
    "policy_update": ["policy", "策略", "gate", "threshold", "rule"],
}

DOMAIN_KEYWORDS = {
    "control_system": ["foc", "pmsm", "motor", "inverter", "apd", "dc-link", " pwm", "observer", "fault recovery"],
    "orchestrator": ["orchestrat", "pipeline", "gate", "review_fusion", "agent", "worktree"],
    "documentation": ["doc", "wiki", "readme", "synthesis", "closeout"],
    "code": ["script", "python", "function", "class", "import", "module"],
    "safety": ["safety", "fault", "emergency", "trip", "latch", "coast", "timeout"],
    "hardware_model": ["hardware", "inductor", "capacitor", "switching", "thermal"],
}

RISK_KEYWORDS = {
    "safety_critical": ["safety", "fault", "emergency", "trip", "latch", "hazard", "critical"],
    "high": ["blocking", "repair", "high", "cascade", "dangling", "timeout"],
    "medium": ["review", "audit", "validate", "fusion", "confidence"],
    "low": ["synthesis", "doc", "summary", "wiki", "report"],
}

ARTIFACT_KEYWORDS = {
    "python": ["python", ".py", "script", "function"],
    "yaml": ["yaml", ".yml", "config", "task.yaml"],
    "json": ["json", "schema", "contract"],
    "markdown": ["markdown", ".md", "doc", "wiki", "synthesis"],
    "matrix": ["matrix", "conformance", "calibration"],
    "test_report": ["test", "benchmark", "regression", "failure injection"],
}


def profile_task(task_input) -> TaskProfile:
    """Profile a task from dict or text."""
    if isinstance(task_input, dict):
        text = json.dumps(task_input).lower()
        title = task_input.get("title", task_input.get("task_id", ""))
        objective = task_input.get("objective", "")
        text = (title + " " + objective + " " + json.dumps(task_input)).lower()
    else:
        text = str(task_input).lower()
        title = text[:100]

    # Classify task type
    task_type = _classify(text, TYPE_KEYWORDS, "implementation")

    # Classify domain
    domain = _classify(text, DOMAIN_KEYWORDS, "code")

    # Classify risk
    risk_level = _classify(text, RISK_KEYWORDS, "medium")

    # Classify artifact type
    artifact_type = _classify(text, ARTIFACT_KEYWORDS, "markdown")

    # Expected output
    expected_output = "report"
    if "review" in task_type or "audit" in task_type:
        expected_output = "review"
    elif "repair" in task_type or "fix" in task_type:
        expected_output = "patch"
    elif "validator" in text or "test" in text:
        expected_output = "validator"
    elif "synthesis" in text:
        expected_output = "synthesis"
    elif "policy" in text:
        expected_output = "patch"

    # Booleans
    requires_repo_write = any(kw in text for kw in ["implement", "create", "build", "add", "fix", "repair", "write", "edit", "modify"])
    requires_code_execution = any(kw in text for kw in ["run", "execute", "test", "validate", "benchmark", "simulation"])
    requires_external_review = risk_level in ("high", "safety_critical") or "cross-audit" in text
    requires_parallelism = "parallel" in text or "worktree" in text or "subproblem" in text
    safety_sensitive = risk_level in ("high", "safety_critical") or any(kw in text for kw in ["safety", "fault", "emergency", "trip"])
    has_known_pattern = any(kw in text for kw in ["similar to", "same as", "pattern", "repeat", "known"])

    # Complexity
    subproblem_count = text.count("subproblem") + text.count("parallel")
    if subproblem_count == 0:
        subproblem_count = 1
    dependency_depth = 2 if "cascade" in text or "chain" in text else 1
    expected_iterations = 3 if "repair" in text or "loop" in text else 1

    # Keywords
    keywords = []
    for kws in [TYPE_KEYWORDS, DOMAIN_KEYWORDS, RISK_KEYWORDS]:
        for cat, words in kws.items():
            for w in words:
                if w.strip() in text:
                    keywords.append(w.strip())

    return TaskProfile(
        task_type=task_type,
        domain=domain,
        risk_level=risk_level,
        artifact_type=artifact_type,
        expected_output=expected_output,
        requires_repo_write=requires_repo_write,
        requires_code_execution=requires_code_execution,
        requires_external_review=requires_external_review,
        requires_parallelism=requires_parallelism,
        safety_sensitive=safety_sensitive,
        has_known_pattern=has_known_pattern,
        complexity={
            "subproblem_count": subproblem_count,
            "dependency_depth": dependency_depth,
            "expected_iterations": expected_iterations,
        },
        keywords=list(set(keywords))[:10],
    )


def _classify(text: str, keyword_map: dict, default: str) -> str:
    best_score = 0
    best_cat = default
    for cat, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw.strip() in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    return best_cat


def main():
    if len(sys.argv) < 2:
        print("Usage: task_profiler.py <task.yaml> | <text>")
        sys.exit(1)

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

    print(json.dumps(asdict(profile), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
