# Run Status: hermes-perm-audit-005/20260527-210000

Created: 2026-05-27T21:00:00
Operator: claude-code
Target: /home/igzela/Projects/hermes-gateway-lab

## Status: COMPLETE

### Verdicts
- experiment_verdict: COMPLETE
- target_control_verdict: PASS
- reason: gate_policy.py extracted, both paths delegate to it, 24/24 regression pass, all smoke tests pass, C001 → pass

### Checklist
- [x] 005 run directory created
- [x] gate_policy.py created with shared gate functions
- [x] local_marker_executor.py modified to import from gate_policy
- [x] local_execution_worker.py modified to import from gate_policy
- [x] 004 regression suite: 24/24 pass
- [x] live4c smoke: PASS
- [x] live6 smoke: PASS (fixed missing rollback_plan)
- [x] live7 smoke: 34/34 PASS
- [x] live9c smoke: 12/12 PASS
- [x] live9d smoke: 11/11 PASS
- [x] C001 upgraded from partial to pass
- [x] 3 model outputs generated
- [x] Synthesis files generated

### Key Findings
1. gate_policy.py is import-safe: no I/O, no daemon, no CLI on import
2. flags_from_env() reads env only when called, not on import
3. GateDenied exception caught by callers and re-raised as their own error type
4. Worker-only arm gate checks remain in worker (not in shared policy)
5. Marker-only marker-exists check remains in marker (not in shared policy)
6. live6 needed rollback_plan fix (same pattern as 004 D018)

### Architecture
```
gate_policy.py (NEW)
  LiveFlags, flags_from_env()
  validate_task_gates(task, dry_run, flags) → gates dict
  GateDenied exception

local_marker_executor.py
  imports gate_policy
  check_gates() → gate_policy.validate_task_gates() + marker-exists check

local_execution_worker.py
  imports gate_policy
  check_worker_gates() → gate_policy.validate_task_gates() + arm gate checks
  check_permission_deny_gates() → gate_policy.validate_task_gates() + deny-specific checks
```

### Next Experiment
hermes-perm-audit-006: Queue ingress / bypass entry audit
Goal: Verify who can write queue, whether stale approvals can be replayed, etc.
