# hermes-perm-audit-003: Worker Gate Conformance Fix

## Objective

Fix the worker daemon's gate function to conform with the canonical marker executor gate function. The 002 experiment found 6/25 deny cases diverge between paths.

## Required Fixes

### Fix 1: Import canonical gate logic
Make `local_execution_worker.py` import `flags_from_env` from `local_marker_executor` and add LIVE_ENABLED + idempotency key checks to `check_worker_gates`.

### Fix 2: Add rollback_plan validation
Add `rollback_plan` field to task schema in `approval_queue.py`. Gate must deny if missing for live-intent tasks.

### Fix 3: Add secret redaction
Extend `sanitize_text` in `approval_queue.py` to scrub API keys, tokens, passwords, path secrets.

### Fix 4: Add risk_class and scope checks to worker
Worker must validate risk_class is in {R2, R3} and external_side_effect is False, matching marker executor.

## Verification
- C001-C003 conformance tests must pass
- D001/D002/D010 must deny on worker path
- No regression in existing conformant cases
