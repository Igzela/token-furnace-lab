# hermes-perm-audit-005: Shared Gate Policy Extraction

## Objective

Extract duplicated gate checks from `local_marker_executor.py` and
`local_execution_worker.py` into a shared `gate_policy.py` module.
This eliminates the architectural root cause of gate drift.

## Context

After 003/004:
- 0/25 deny case divergence (behavioral equivalence achieved)
- 24/24 regression tests pass (behavior locked)
- C001 still "partial" — worker retains independent gate function

Both paths implement the same gate logic independently:
```python
# local_marker_executor.py (canonical)
def check_gates(task_id, flags, paths):
    # LIVE_ENABLED check
    # scope check
    # idempotency check
    # rollback_plan check
    # risk_class check
    # external_side_effect check
    # private_content check
    ...

# local_execution_worker.py (duplicate)
def check_worker_gates(request, arm_gate, paths, flags):
    # Same checks, independently implemented
    ...
```

This duplication is the root cause of 002's 6 divergent cases.
003 fixed the behavior, but didn't fix the structure.

## Architecture (from GPT)

### Shared gate_policy.py

```python
# gate_policy.py — single source of truth for gate logic

def flags_from_env() -> LiveFlags:
    """Import from local_marker_executor or redefine."""
    ...

def validate_task_gates(task: dict, flags: LiveFlags, paths) -> dict:
    """Run all canonical gate checks. Returns gates dict.
    Raises LocalMarkerError on failure."""
    ...

def validate_live_enabled(flags: LiveFlags) -> bool:
    ...

def validate_scope(flags: LiveFlags) -> bool:
    ...

def validate_idempotency(task: dict) -> bool:
    ...

def validate_rollback_plan(task: dict) -> bool:
    ...

def validate_risk_class(task: dict) -> bool:
    ...

def sanitize_text(value: str) -> str:
    ...

def redact_secrets(value: str) -> str:
    ...
```

### Marker executor (modified)

```python
# local_marker_executor.py
import gate_policy

def check_gates(task_id, flags, paths):
    # Use shared policy for core gates
    gates = gate_policy.validate_task_gates(task, flags, paths)
    # Add marker-specific checks
    if path.exists():
        _block(task_id, "marker already exists", paths)
    return gates
```

### Worker daemon (modified)

```python
# local_execution_worker.py
import gate_policy

def check_worker_gates(request, arm_gate, paths, flags):
    # Use shared policy for core gates
    gates = gate_policy.validate_task_gates(task, flags, paths)
    # Add worker-only checks
    if arm_gate.get("consumed"):
        raise WorkerError("arm gate already consumed")
    ...
```

## Key Constraints

1. **No behavior change**: 004 regression suite must stay 24/24 pass
2. **No new gates**: Only extract existing checks, don't add new ones
3. **Import-safe**: gate_policy.py must have no CLI/IO/daemon side effects
4. **Live execution stays disabled**: No live execution enabled or run
5. **Approval flow unchanged**: No modifications to approval_queue.py

## Test Plan

1. Run `scripts/gate_conformance_regression.py` — must be 24/24 pass
2. Run all 6 smoke test suites — must all pass
3. Verify C001 upgrades from "partial" to "pass"
4. Verify no new divergent cases in deny-path matrix

## Deliverables

1. `scripts/gate_policy.py` — shared gate module
2. Modified `scripts/local_marker_executor.py` — imports from gate_policy
3. Modified `scripts/local_execution_worker.py` — imports from gate_policy
4. Model outputs and synthesis
5. Updated gate-conformance-matrix.yaml (C001 → pass)

## Non-Goals

- Do not cover D012 (deferred to P1)
- Do not add audit() sink sanitization (deferred to 006)
- Do not enable live execution
- Do not modify approval flow
