#!/usr/bin/env python3
"""
Policy Engine: Safe policy application, repeat failure detection,
and regression testing for the adaptive orchestrator.

Usage:
  python3 scripts/policy_engine.py generate-patches     # Generate patches from suggestions
  python3 scripts/policy_engine.py apply <patch.yaml>    # Apply a single patch
  python3 scripts/policy_engine.py regression            # Run regression tests
  python3 scripts/policy_engine.py detect-repeats        # Detect repeat failures
  python3 scripts/policy_engine.py report                # Generate full application report
"""

import json
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = REPO_ROOT / "configs"
KNOWLEDGE_DIR = REPO_ROOT / "knowledge" / "orchestrator"
SCHEMAS_DIR = REPO_ROOT / "schemas"
POLICY_CONFIG = CONFIGS_DIR / "orchestrator_policy.yaml"
POLICY_REGISTRY = KNOWLEDGE_DIR / "policy_registry.yaml"
POLICY_SUGGESTIONS = KNOWLEDGE_DIR / "policy_suggestions.yaml"
OUTCOME_MEMORY = KNOWLEDGE_DIR / "outcome_memory.jsonl"
PATCHES_DIR = REPO_ROOT / "runs" / "orchestration-010" / "20260528-160000" / "patches"
REPORT_FILE = REPO_ROOT / "runs" / "orchestration-010" / "20260528-160000" / "policy_application_report.yaml"


@dataclass
class PolicyPatch:
    patch_id: str
    source_suggestion: str
    risk: str
    change_type: str
    target: Dict[str, str]
    change: Dict[str, List[str]]
    validation_required: List[str] = field(default_factory=list)
    rollback: Dict[str, any] = field(default_factory=dict)
    status: str = "pending"  # pending, applied, rejected, rolled_back


@dataclass
class RepeatFailure:
    policy_id: str
    policy_name: str
    lesson: str
    occurrences: int
    runs: List[str]
    status: str  # effective, ineffective, not_enforced
    action: str


# --- Patch generation ---

def load_suggestions() -> List[Dict]:
    if not POLICY_SUGGESTIONS.exists():
        return []
    if yaml:
        data = yaml.safe_load(POLICY_SUGGESTIONS.read_text(encoding="utf-8"))
    else:
        data = json.loads(POLICY_SUGGESTIONS.read_text(encoding="utf-8"))
    return data.get("suggestions", [])


def load_registry() -> Dict:
    if not POLICY_REGISTRY.exists():
        return {}
    if yaml:
        return yaml.safe_load(POLICY_REGISTRY.read_text(encoding="utf-8")) or {}
    return json.loads(POLICY_REGISTRY.read_text(encoding="utf-8"))


def load_outcomes() -> List[Dict]:
    if not OUTCOME_MEMORY.exists():
        return []
    outcomes = []
    for line in OUTCOME_MEMORY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            outcomes.append(json.loads(line))
    return outcomes


RISK_TO_CHANGE_TYPE = {
    "cross_audit": "add_strictness_rule",
    "timeout": "add_classifier",
    "failure_injection": "add_validator",
    "confidence": "add_strictness_rule",
    "cascade": "add_strictness_rule",
    "fusion": "add_strictness_rule",
    "parallel": "add_strictness_rule",
    "low_findings": "add_strictness_rule",
}

BLOCKED_TYPES = {"weaken_validator", "auto_merge", "reduce_escalation", "lower_threshold"}


def classify_suggestion_risk(suggestion: Dict) -> str:
    """Classify suggestion risk based on change type and content."""
    change_type = suggestion.get("proposed_change_type", "unknown")
    sugg_text = suggestion.get("suggestion", "").lower()

    # High risk: anything that weakens
    if any(kw in sugg_text for kw in ["weaken", "ignore", "reduce", "lower", "remove.*block"]):
        return "high"

    # Medium risk: gate policy changes
    if change_type in ("gate_policy", "threshold_change"):
        return "medium"

    return suggestion.get("risk", "low")


def generate_patches() -> List[PolicyPatch]:
    """Generate policy patches from suggestions."""
    suggestions = load_suggestions()
    registry = load_registry()
    active_ids = {p["id"] for p in registry.get("active_policies", [])}

    patches = []
    patch_num = 1

    for sugg in suggestions:
        risk = classify_suggestion_risk(sugg)

        # Block high-risk
        if risk == "high":
            continue

        # Determine change type
        trigger = sugg.get("trigger_pattern", "")
        change_type = "add_strictness_rule"
        for key, ct in RISK_TO_CHANGE_TYPE.items():
            if key in trigger:
                change_type = ct
                break

        # Map to policy config section
        if change_type == "add_classifier":
            section = "decision_policy.strictness_rules"
        elif change_type == "add_validator":
            section = "decision_policy.strictness_rules"
        else:
            section = "decision_policy.strictness_rules"

        patch = PolicyPatch(
            patch_id=f"POLPATCH-{patch_num:03d}",
            source_suggestion=sugg["id"],
            risk=risk,
            change_type=change_type,
            target={"file": "configs/orchestrator_policy.yaml", "section": section},
            change={"add": [sugg["suggestion"]]},
            validation_required=["failure_injection", "calibration"],
            rollback={"remove": [sugg["suggestion"]]},
        )
        patches.append(patch)
        patch_num += 1

    return patches


# --- Patch application ---

def apply_patch(patch: PolicyPatch, dry_run: bool = False) -> bool:
    """Apply a policy patch to the orchestrator config."""
    if patch.risk == "high":
        print(f"BLOCKED: {patch.patch_id} is high risk — requires human approval")
        patch.status = "rejected"
        return False

    if not POLICY_CONFIG.exists():
        print(f"ERROR: Policy config not found: {POLICY_CONFIG}")
        return False

    if yaml:
        config = yaml.safe_load(POLICY_CONFIG.read_text(encoding="utf-8")) or {}
    else:
        config = json.loads(POLICY_CONFIG.read_text(encoding="utf-8"))

    strictness = config.get("decision_policy", {}).get("strictness_rules", [])

    # Check if rule already exists
    new_rule_text = patch.change.get("add", [])[0] if patch.change.get("add") else ""
    existing = [r for r in strictness if r.get("description", "") == new_rule_text]
    if existing:
        print(f"SKIP: {patch.patch_id} — rule already exists: {existing[0].get('id')}")
        patch.status = "applied"
        return True

    # Create new rule
    new_rule = {
        "id": f"SR-{len(strictness)+1:03d}",
        "name": patch.source_suggestion.lower().replace("-", "_"),
        "description": new_rule_text,
        "enabled": True,
        "source": patch.source_suggestion,
        "applied_by": "policy_engine",
    }

    if dry_run:
        print(f"DRY RUN: Would add {new_rule['id']}: {new_rule_text[:60]}...")
        patch.status = "applied"
        return True

    strictness.append(new_rule)
    config["decision_policy"]["strictness_rules"] = strictness

    if yaml:
        POLICY_CONFIG.write_text(
            yaml.dump(config, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
    else:
        POLICY_CONFIG.write_text(
            json.dumps(config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"APPLIED: {patch.patch_id} → {new_rule['id']}: {new_rule_text[:60]}...")
    patch.status = "applied"
    return True


def rollback_patch(patch: PolicyPatch) -> bool:
    """Rollback a previously applied patch."""
    if not POLICY_CONFIG.exists():
        return False

    if yaml:
        config = yaml.safe_load(POLICY_CONFIG.read_text(encoding="utf-8")) or {}
    else:
        config = json.loads(POLICY_CONFIG.read_text(encoding="utf-8"))

    strictness = config.get("decision_policy", {}).get("strictness_rules", [])
    remove_text = patch.change.get("add", [])[0] if patch.change.get("add") else ""

    original_len = len(strictness)
    strictness = [r for r in strictness if r.get("description", "") != remove_text]

    if len(strictness) == original_len:
        print(f"SKIP: Nothing to rollback for {patch.patch_id}")
        return False

    config["decision_policy"]["strictness_rules"] = strictness

    if yaml:
        POLICY_CONFIG.write_text(
            yaml.dump(config, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
    else:
        POLICY_CONFIG.write_text(
            json.dumps(config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"ROLLED BACK: {patch.patch_id}")
    patch.status = "rolled_back"
    return True


# --- Regression testing ---

def run_regression() -> Dict[str, bool]:
    """Run regression tests to validate policy changes."""
    results = {}

    # Test 1: Confidence calibrator (9/9 calibration cases)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", """
import sys; sys.path.insert(0, 'scripts')
from tf_orchestrator import Finding
from confidence_calibrator import classify_timeout_finding
import yaml

cases = yaml.safe_load(open('runs/orchestration-008/20260528-140000/calibration_cases.yaml'))
passed = 0
for case in cases['cases']:
    fd = case['finding']
    f = Finding(id=fd['id'], claim=fd['claim'], severity=fd['severity'],
                blocking=fd['blocking'], status='OPEN', evidence_path='', correction='')
    result = classify_timeout_finding(f, '')
    if result == case['expected_classification']:
        passed += 1
print(f'{passed}/{len(cases["cases"])}')
"""],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
        results["calibration_cases"] = proc.stdout.strip() == "9/9"
        print(f"  Calibration cases: {proc.stdout.strip()} {'PASS' if results['calibration_cases'] else 'FAIL'}")
    except Exception as e:
        results["calibration_cases"] = False
        print(f"  Calibration cases: ERROR {e}")

    # Test 2: Confidence pipeline (round 1 REPAIR, round 2 ACCEPT)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", """
import sys; sys.path.insert(0, 'scripts')
from tf_orchestrator import parse_review
from confidence_calibrator import evaluate_decision_policy

r1 = parse_review(open('runs/orchestration-006/20260528-120000/artifacts/claude_review_round_1.md').read())
r2 = parse_review(open('runs/orchestration-006/20260528-120000/artifacts/claude_review_round_2.md').read())

d1 = evaluate_decision_policy([(r1, 'claude')], r1.findings)
d2 = evaluate_decision_policy([(r2, 'claude')], r2.findings)

ok1 = d1.verdict == 'REPAIR'
ok2 = d2.verdict == 'ACCEPT'
print(f'REPAIR={ok1} ACCEPT={ok2}')
"""],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
        results["confidence_pipeline"] = "REPAIR=True" in proc.stdout and "ACCEPT=True" in proc.stdout
        print(f"  Confidence pipeline: {proc.stdout.strip()} {'PASS' if results['confidence_pipeline'] else 'FAIL'}")
    except Exception as e:
        results["confidence_pipeline"] = False
        print(f"  Confidence pipeline: ERROR {e}")

    # Test 3: Core imports still work
    try:
        proc = subprocess.run(
            [sys.executable, "-c", """
import sys; sys.path.insert(0, 'scripts')
from tf_orchestrator import Finding, Review, parse_review, evaluate_gate
from confidence_calibrator import compute_confidence, evaluate_decision_policy
from review_fusion import fuse_reviews
from worktree_manager import WorktreeManager
from orchestrator_learn import discover_runs, generate_suggestions
print('ALL_IMPORTS_OK')
"""],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
        results["core_imports"] = "ALL_IMPORTS_OK" in proc.stdout
        print(f"  Core imports: {'PASS' if results['core_imports'] else 'FAIL'}")
    except Exception as e:
        results["core_imports"] = False
        print(f"  Core imports: ERROR {e}")

    # Test 4: Policy config is valid YAML
    try:
        if yaml:
            config = yaml.safe_load(POLICY_CONFIG.read_text(encoding="utf-8"))
        else:
            config = json.loads(POLICY_CONFIG.read_text(encoding="utf-8"))
        results["config_valid"] = "decision_policy" in config
        print(f"  Config valid: {'PASS' if results['config_valid'] else 'FAIL'}")
    except Exception as e:
        results["config_valid"] = False
        print(f"  Config valid: ERROR {e}")

    return results


# --- Repeat failure detection ---

def detect_repeats() -> List[RepeatFailure]:
    """Detect repeat failures from outcome memory."""
    outcomes = load_outcomes()
    registry = load_registry()

    # Build lesson occurrence map
    lesson_runs: Dict[str, List[str]] = {}
    for o in outcomes:
        for lesson in o.get("lessons", []):
            # Normalize lesson to key
            key = lesson.lower().strip()
            if key not in lesson_runs:
                lesson_runs[key] = []
            lesson_runs[key].append(o.get("run_id", "unknown"))

    # Check each active policy
    active_policies = registry.get("active_policies", [])
    repeats = []

    for policy in active_policies:
        policy_name = policy.get("name", "")
        # Find matching lessons
        matching_lessons = []
        for lesson_key, runs in lesson_runs.items():
            if _policy_matches_lesson(policy_name, lesson_key):
                matching_lessons.append((lesson_key, runs))

        if matching_lessons:
            for lesson_key, runs in matching_lessons:
                if len(runs) >= 2:
                    # Check if runs span before and after policy activation
                    source = policy.get("source", "")
                    before = [r for r in runs if not r.startswith(source)]
                    after = [r for r in runs if r.startswith(source)]

                    if before and after:
                        status = "ineffective_or_not_enforced"
                        action = "escalate_policy_review"
                    elif len(runs) >= 3:
                        status = "potentially_ineffective"
                        action = "monitor"
                    else:
                        status = "effective"
                        action = "none"

                    repeats.append(RepeatFailure(
                        policy_id=policy["id"],
                        policy_name=policy_name,
                        lesson=lesson_key[:100],
                        occurrences=len(runs),
                        runs=runs,
                        status=status,
                        action=action,
                    ))

    return repeats


def _policy_matches_lesson(policy_name: str, lesson: str) -> bool:
    """Check if a policy name matches a lesson text."""
    keywords = {
        "validator_fail": ["validator", "override", "score"],
        "blocking_findings": ["blocking", "union"],
        "timeout": ["timeout", "transition"],
        "cascade": ["cascade", "dangling"],
        "cross_audit": ["cross-audit", "different", "reviewer"],
        "confidence": ["confidence", "synth"],
        "failure_injection": ["failure", "injection", "regression"],
        "parallel": ["parallel", "worktree"],
        "repeated_low": ["low", "informational"],
    }

    for key, words in keywords.items():
        if key in policy_name:
            return any(w in lesson for w in words)
    return False


# --- Report generation ---

def generate_report(patches: List[PolicyPatch], regression: Dict[str, bool],
                    repeats: List[RepeatFailure]) -> Dict:
    """Generate policy application report."""
    applied = [p for p in patches if p.status == "applied"]
    rejected = [p for p in patches if p.status == "rejected"]

    report = {
        "run_id": "orchestration-010",
        "generated_at": "2026-05-28",
        "summary": {
            "total_patches": len(patches),
            "applied": len(applied),
            "rejected": len(rejected),
            "regression_pass": all(regression.values()),
            "repeat_failures_detected": len(repeats),
            "repeat_failures_ineffective": sum(1 for r in repeats if r.status != "effective"),
        },
        "patches": [asdict(p) for p in patches],
        "regression_results": regression,
        "repeat_failures": [asdict(r) for r in repeats],
        "policy_effectiveness": [],
    }

    # Measure effectiveness per policy
    outcomes = load_outcomes()
    for policy in load_registry().get("active_policies", []):
        pid = policy["id"]
        # Count occurrences in outcomes
        total = sum(1 for o in outcomes if any(
            policy.get("name", "").split("_")[0] in l.lower()
            for l in o.get("lessons", [])
        ))
        report["policy_effectiveness"].append({
            "policy_id": pid,
            "name": policy.get("name", ""),
            "lesson_occurrences": total,
            "status": "active",
        })

    return report


# --- Main ---

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]

    if action == "generate-patches":
        patches = generate_patches()
        PATCHES_DIR.mkdir(parents=True, exist_ok=True)

        for p in patches:
            patch_file = PATCHES_DIR / f"{p.patch_id}.yaml"
            if yaml:
                patch_file.write_text(yaml.dump(asdict(p), default_flow_style=False), encoding="utf-8")
            else:
                patch_file.write_text(json.dumps(asdict(p), indent=2), encoding="utf-8")
            print(f"Generated: {p.patch_id} ({p.risk}) {p.change_type}")

        print(f"\n{len(patches)} patches generated in {PATCHES_DIR}")

    elif action == "apply":
        if len(sys.argv) < 3:
            print("Usage: policy_engine.py apply <patch.yaml>")
            sys.exit(1)
        patch_file = Path(sys.argv[2])
        if yaml:
            data = yaml.safe_load(patch_file.read_text(encoding="utf-8"))
        else:
            data = json.loads(patch_file.read_text(encoding="utf-8"))
        patch = PolicyPatch(**data)
        apply_patch(patch)

    elif action == "regression":
        print("=== Regression Tests ===")
        results = run_regression()
        all_pass = all(results.values())
        print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")

    elif action == "detect-repeats":
        print("=== Repeat Failure Detection ===")
        repeats = detect_repeats()
        if repeats:
            for r in repeats:
                print(f"  {r.policy_id} ({r.policy_name}): {r.occurrences} occurrences, status={r.status}")
        else:
            print("  No repeat failures detected")

    elif action == "report":
        print("=== Policy Application Report ===")
        patches = generate_patches()
        regression = run_regression()
        repeats = detect_repeats()
        report = generate_report(patches, regression, repeats)

        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        if yaml:
            REPORT_FILE.write_text(yaml.dump(report, default_flow_style=False), encoding="utf-8")
        else:
            REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(f"\nReport written to {REPORT_FILE}")
        print(f"Patches: {report['summary']['applied']}/{report['summary']['total_patches']} applied")
        print(f"Regression: {'PASS' if report['summary']['regression_pass'] else 'FAIL'}")
        print(f"Repeat failures: {report['summary']['repeat_failures_detected']}")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
