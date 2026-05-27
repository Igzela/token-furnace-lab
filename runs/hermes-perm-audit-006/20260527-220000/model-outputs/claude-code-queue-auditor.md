# Claude Code: Queue Ingress Audit

**Role**: Audit queue ingress paths and bypass entry risks
**Experiment**: hermes-perm-audit-006
**Date**: 2026-05-27

## Audit Summary

### Q001: Queue Writer Inventory

9 production write paths to queue.json:
1. `approval_queue.create_task()` — task creation
2. `approval_queue.approve_task()` — approval
3. `approval_queue.reject_task()` — rejection
4. `approval_queue.transition()` — state transition
5. `dry_run_executor.execute_dry_run()` — dry run completion
6. `local_marker_executor.execute_marker()` — marker completion
7. `local_execution_worker.worker_run_once()` — worker completion
8. `local_execution_worker.worker_execute_permission_deny()` — permission deny completion
9. `h2c6r-get-compat-bridge.py` — bridge direct access

Plus indirect writes to requests.json, arm gate JSON, dry-run-results.json, previews, and executions.

### Q002: Worker Final Gate

**PASS**: Worker always calls gate_policy before execution.
- `worker_run_once()` → `check_worker_gates()` → `gate_policy.validate_task_gates()`
- `worker_execute_permission_deny()` → `check_permission_deny_gates()` → `gate_policy.validate_task_gates()`
- All early-return paths perform no side effects.

### Q003: Manual Injection

**PASS with warnings**:
- Missing approval: denied by gate_policy
- Wrong risk class: denied by gate_policy
- Well-crafted item with all fields: passes (no integrity check)

### Q004: Post-Approval Mutation

**PASS**: Mutating external_side_effect to True after approval → denied by gate_policy.

### Q005: Stale Approval

**WARN**: No approval TTL. Approvals valid indefinitely. Arm gate consumption is the actual replay protection.

### Q006: Idempotency Replay

**PASS**: Arm gate consumed after use. Second execution attempt denied.

### Q007: Broken Queue

**WARN**: Corrupt queue file raises unhandled exception. No recovery/quarantine mechanism.

### Q008: Audit Sanitization

**WARN**: audit() doesn't sanitize payload. Most callers sanitize, but edge cases exist (permission_id, requested_by).

## Files Created

- `scripts/queue_ingress_audit.py` — verification script
