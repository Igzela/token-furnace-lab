# hermes-perm-audit-004: Worker Gate Conformance Regression Suite

## Objective

Turn the 003 gate conformance fix into an executable regression suite.
Ensure marker_executor and worker_daemon remain behaviorally equivalent
for all P0 deny cases.

## Context

hermes-perm-audit-003 fixed 6 divergent deny cases (D001/D002/D003/D010/D014/D024).
But conformance is currently verified by 6 smoke test suites with 57 assertions —
not a dedicated conformance regression suite.

004 creates a single test script that:
1. Tests each P0 deny case on both paths
2. Compares dual-path results for equivalence
3. Verifies deny prevents execution
4. Verifies secret redaction persists in audit log

## Test Architecture (from GPT)

### Layer 1: basic deny assertions
```python
D001 LIVE_ENABLED missing -> deny
D002 LIVE_ENABLED=false -> deny
D003 scope not enabled -> deny
D010 idempotency missing -> deny
D012 idempotency mismatch -> deny
D014 rollback missing for live-intent -> deny
D018 R4 -> deny
D019 R5 -> deny
```

### Layer 2: dual-path conformance tests
```python
# Same fixture fed to both paths
assert marker_result.decision == worker_result.decision
```

### Layer 3: worker no-execute tests
```python
# Deny must prevent execution
given invalid task
when worker_run_once()
then WorkerError / denied status
and no output file written
and no side effect marker created
```

### Layer 4: redaction persistence tests
```python
# Secrets must be redacted in audit log
input reason contains fake token
audit log exists
audit log contains <REDACTED_SECRET>
audit log does not contain original token
```

## Non-Goals

- Do not refactor gate architecture
- Do not extract gate_policy yet
- Do not enable live execution
- Do not modify approval flow

## Deliverables

1. `scripts/gate_conformance_regression.py` — executable test suite
2. Updated gate-conformance-matrix.yaml with C001 upgrade
3. Model outputs and synthesis
