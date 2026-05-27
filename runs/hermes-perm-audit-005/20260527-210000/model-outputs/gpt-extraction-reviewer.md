# GPT: Extraction Architecture Review

**Role**: Review gate_policy extraction architecture
**Experiment**: hermes-perm-audit-005
**Date**: 2026-05-27

## Architecture Assessment

### Design Correctness

The extraction follows the recommended architecture:

```
gate_policy.py (shared)
  validate_task_gates() → core permission checks
  LiveFlags, flags_from_env()
  GateDenied exception

marker_executor (caller)
  check_gates() → validate_task_gates() + marker-specific
  _block() catches GateDenied, raises LocalMarkerError

worker_daemon (caller)
  check_worker_gates() → validate_task_gates() + arm gate checks
  catches GateDenied, raises WorkerError
```

### Key Design Decisions

1. **GateDenied as intermediate exception**: Clean separation — gate_policy raises neutral exception, callers re-raise as their own type. This preserves error semantics for each path.

2. **Import-safe**: `flags_from_env()` reads env on call, not on import. No I/O, no daemon, no CLI parsing in gate_policy.py. Correct.

3. **LiveFlags re-export**: marker_executor re-exports `gate_policy.LiveFlags` for backwards compatibility. Worker now imports from gate_policy directly. Clean migration path.

4. **Worker-only checks remain in worker**: Arm gate validation (created_by, expires_at, request_id match, consumed, max_executions) stays in worker. This is the correct boundary — arm gates are operational, not policy.

5. **Marker-only checks remain in marker**: Marker file existence check stays in marker. Worker doesn't need this.

### C001 Upgrade

**Before**: C001 partial — worker had independent gate function with duplicated logic
**After**: C001 pass — both paths call `gate_policy.validate_task_gates()` for core gates

The C001 PASS condition is met:
- marker_executor's core permission checks go through gate_policy.validate_task_gates()
- worker_daemon's core permission checks go through gate_policy.validate_task_gates()
- Worker-only arm gate checks are clearly labeled as "worker-only operational gate"

### Verdict

Extraction is clean and correct. No behavior change. C001 upgraded to PASS.
