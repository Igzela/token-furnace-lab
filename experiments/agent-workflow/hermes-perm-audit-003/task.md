# hermes-perm-audit-003: Worker Gate Conformance Fix

## Objective

Fix the worker daemon's gate function to conform with the canonical marker executor gate function. The 002 experiment found 6/25 deny cases diverge between paths.

## Context

hermes-perm-audit-002 found:
- `check_worker_gates` in `local_execution_worker.py` uses independent gate logic
- `local_marker_executor.check_gates` is the canonical gate function
- 6 cases diverge: D001, D002, D003, D010, D012
- C001-C003 conformance tests fail

## Required Fixes

### Fix 1: Import canonical gate function
Make `local_execution_worker.py` import and use `check_gates` from `local_marker_executor`, or delegate to it.

### Fix 2: Add missing gate checks
If keeping independent `check_worker_gates`, add:
- LIVE_ENABLED check (D001/D002)
- idempotency key check (D010)
- scope re-validation (D003/D004)
- idempotency key match (D012)

### Fix 3: Add rollback plan validation
- Add `rollback_plan` field to task schema
- Gate must deny if missing for live-intent tasks (D014)

### Fix 4: Add secret redaction
- Extend `sanitize_text` in `approval_queue.py` to scrub secret patterns
- Patterns: API keys, tokens, passwords, path secrets (D024)

## Verification

After fixes:
1. Run conformance tests: C001-C003 must pass
2. Run deny-path tests: D001/D002/D010 must deny on worker path
3. Verify no regression: D005/D006/D018/D019 still deny
4. Verify no new divergent cases

## Rules

- Do not enable live execution
- Do not modify marker executor gate logic
- Do not change approval flow
- All changes must be on experiment branch
