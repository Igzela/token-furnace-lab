# hermes-perm-audit-006: Queue Ingress / Bypass Entry Audit

## Objective

Audit queue ingress paths and bypass entry risks.
Answer: can any request bypass `marker_executor` / `gate_policy`
and reach `worker_daemon` execution directly?

## Context

After 001-005:
- 0/25 deny case divergence (behavioral equivalence)
- 24/24 regression tests pass (behavior locked)
- gate_policy.py is single source of truth (C001-C006 all pass)
- Both paths delegate to validate_task_gates() for core gates

But the security model assumes "all execution goes through gate_policy".
006 verifies this assumption by checking for bypass entry points.

## 8 Queue Ingress Questions

### Q001: Queue Item Writer Inventory
**Question**: Who can create queue items?
**Method**: Grep for `save_queue`, `create_task`, direct file writes to queue store
**Expected**: All writers identified and documented

### Q002: Worker Final Gate Before Execution
**Question**: Does worker always call gate_policy before side effect?
**Method**: Trace worker_run_once flow, verify gate check is unconditional
**Expected**: gate_policy.validate_task_gates() called before any execution

### Q003: Manual Queue Injection
**Question**: Can a hand-crafted queue item trigger worker execution?
**Method**: Write invalid queue item, attempt worker execution
**Expected**: Denied by gate_policy (missing required fields)

### Q004: Post-Approval Queue Mutation
**Question**: Can a queue item be modified after approval/dry-run?
**Method**: Approve task, mutate queue item, attempt execution
**Expected**: Denied (field mismatch detected by gate_policy)

### Q005: Stale Approval Replay
**Question**: Can a stale approval trigger execution?
**Method**: Create old approval, attempt execution
**Expected**: Denied (stale timestamp or state mismatch)

### Q006: Stale Idempotency Replay
**Question**: Can a stale idempotency key trigger execution?
**Method**: Reuse idempotency key from completed task
**Expected**: Denied or noop (key already consumed)

### Q007: Broken Queue Recovery
**Question**: Are broken queue files quarantined?
**Method**: Corrupt queue file, check recovery behavior
**Expected**: Quarantined, not re-entered into active queue

### Q008: Recovery Artifact Secret Redaction
**Question**: Do recovery/audit artifacts redact secrets?
**Method**: Check recovery files for secret patterns
**Expected**: Secrets redacted before persistence

## Deliverables

1. `knowledge/matrices/queue-ingress-matrix.yaml` — Q001-Q008 status
2. `knowledge/matrices/queue-bypass-risk-matrix.yaml` — risk assessment
3. `scripts/queue_ingress_audit.py` — verification script
4. Model outputs and synthesis

## Non-Goals

- Do not fix queue logic (defer to 007 if needed)
- Do not enable live execution
- Do not use real secrets
- Do not modify approval flow
