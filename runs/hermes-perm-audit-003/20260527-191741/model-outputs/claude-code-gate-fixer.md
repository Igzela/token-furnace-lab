# Claude Code Gate Fixer Output — hermes-perm-audit-003

## Summary

Implemented 4 fixes to make `check_worker_gates` in `local_execution_worker.py` conformant with the canonical `check_gates` in `local_marker_executor.py`. All smoke tests pass (6/6 suites, 57 total assertions).

## Fix 1: Canonical flag and gate imports

**File:** `local_execution_worker.py:113-210`

`check_worker_gates` now accepts an optional `flags: LiveFlags` parameter. If not provided, it calls `local_marker_executor.flags_from_env()` to read LIVE_ENABLED and LOCAL_MARKER_LIVE_ENABLED from environment.

**New gates added to the `gates` dict:**
- `live_execution_enabled_for_this_action_only`: `flags.live_enabled and flags.local_marker_live_enabled`
- `global_live_kill_switch_off`: `flags.live_enabled`
- `idempotency_key_present`: validates task has non-empty idempotency key
- `risk_class_valid`: task.risk_class in {R2, R3}
- `no_external_side_effect`: task.external_side_effect is False
- `rollback_plan_present`: task.rollback_plan is non-empty

**New validation checks (matching marker executor order):**
1. LIVE_ENABLED must be true (D001/D002)
2. LOCAL_MARKER_LIVE_ENABLED must be true
3. Idempotency key must be present (D010)
4. Risk class must be R2 or R3
5. External side effect must be False
6. Rollback plan must be present (D014)

**Divergent cases fixed:**
- D001: LIVE_ENABLED missing → now denies (was: allows)
- D002: LIVE_ENABLED=false → now denies (was: allows)
- D003: scope not enabled → now denies via flag check (was: allows)
- D010: idempotency key missing → now denies (was: allows)
- D012: idempotency key mismatch → partial fix (still trusts dry-run for match)

## Fix 2: Rollback plan validation

**File:** `approval_queue.py:133-158`

Added `"rollback_plan": ""` to the default task dict in `create_task`. Both `check_worker_gates` and `check_gates` now validate that `rollback_plan` is non-empty before allowing live execution.

**File:** `local_marker_executor.py:364-365`

Added rollback plan check to canonical `check_gates`:
```python
if not approval_queue.sanitize_text(str(task.get("rollback_plan") or "")):
    _block(clean_task_id, "rollback plan is required for live execution", paths)
```

D014 status changed from `missing` to `complete` on both paths.

## Fix 3: Secret redaction in sanitize_text

**File:** `approval_queue.py:90-110`

Extended `sanitize_text` with regex-based secret detection. Patterns covered:
- OpenAI-style API keys (`sk-...`)
- Generic key-... and api_... patterns
- Bearer tokens
- Key=value pairs with token/password/secret/pwd
- AWS AKIA keys
- PEM private key headers

D024 status changed from `missing` to `complete` on both paths.

## Fix 4: Risk class and scope checks in worker

**File:** `local_execution_worker.py:171-177`

Worker now validates:
- `risk_class` in {R2, R3} (matching marker executor)
- `external_side_effect` is False (matching marker executor)

## Threaded flags through worker operations

**File:** `local_execution_worker.py`

- `worker_run_once` accepts optional `flags` parameter
- `worker_execute_permission_deny` accepts optional `flags` parameter
- Both thread flags to their respective gate check functions

## Test updates

- `live7_auto_worker_smoke.py`: Updated to pass `LiveFlags(live_enabled=True, local_marker_live_enabled=True)` to `worker_run_once`. Added rollback_plan to test task.
- `live9d_permission_deny_worker_smoke.py`: Updated all gate check calls to pass `LIVE_FLAGS`. Added `risk_class`, `external_side_effect`, `rollback_plan` to test task creation.

## Verification

| Test Suite | Result |
|-----------|--------|
| h4_approval_queue_smoke | PASS |
| h5_inert_executor_smoke | PASS |
| live4c_marker_executor_disabled_smoke | PASS |
| live7_auto_worker_smoke | 34/34 PASS |
| live9c_permission_deny_dry_run_smoke | 12/12 PASS |
| live9d_permission_deny_worker_smoke | 11/11 PASS |
