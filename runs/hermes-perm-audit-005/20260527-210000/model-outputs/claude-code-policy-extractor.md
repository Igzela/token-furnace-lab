# Claude Code: Gate Policy Extraction

**Role**: Extract shared gate policy module
**Experiment**: hermes-perm-audit-005
**Date**: 2026-05-27

## Implementation Summary

### gate_policy.py Created

New module with:
- `LiveFlags` dataclass (frozen)
- `flags_from_env()` — reads env only when called (import-safe)
- `GateDenied` exception (with gate_id and reason)
- `validate_task_gates(task, dry_run, flags)` — returns gates dict or raises GateDenied

### Canonical Gates (11 checks)

1. `live_execution_enabled_for_this_action_only` — flags.live_enabled
2. `global_live_kill_switch_off` — flags.local_marker_live_enabled
3. `task_state_valid` — state == "dry_run_completed"
4. `task_approved` — approved is True
5. `approval_source_valid` — source == "charlie_local_cli"
6. `dry_run_success` — dry_run status == "success"
7. `idempotency_key_present` — sanitized key is non-empty
8. `risk_class_valid` — risk_class in {"R2", "R3"}
9. `no_external_side_effect` — external_side_effect is False
10. `no_private_content_required` — private_content_included is False
11. `rollback_plan_present` — sanitized plan is non-empty

### Marker Executor Changes

- Removed local `LiveFlags` class → re-exports `gate_policy.LiveFlags`
- Removed local `flags_from_env()` → delegates to `gate_policy.flags_from_env()`
- `check_gates()` now calls `gate_policy.validate_task_gates()`, catches `GateDenied`, re-raises via `_block()`
- Marker-specific check (marker file exists) remains in marker executor

### Worker Changes

- Added `import gate_policy`
- `check_worker_gates()` now calls `gate_policy.validate_task_gates()`, catches `GateDenied`, re-raises as `WorkerError`
- Worker-only arm gate checks remain in worker
- `check_permission_deny_gates()` also delegates to `gate_policy.validate_task_gates()`
- All `local_marker_executor.LiveFlags` references updated to `gate_policy.LiveFlags`

### live6 Fix

`live6_local_execution_request_smoke.py` needed rollback_plan set after task creation (same pattern as 004 D018 fix). Added manual queue modification after `create_task()`.

## Test Results

```
Regression: 24/24 PASS
live4c: PASS
live6: PASS
live7: 34/34 PASS
live9c: 12/12 PASS
live9d: 11/11 PASS
```

## Files Modified

- `scripts/gate_policy.py` — NEW (shared gate module)
- `scripts/local_marker_executor.py` — imports from gate_policy, re-exports LiveFlags
- `scripts/local_execution_worker.py` — imports from gate_policy, delegates canonical checks
- `scripts/live6_local_execution_request_smoke.py` — fixed missing rollback_plan
