# GPT: Bypass Risk Review

**Role**: Review bypass risk matrix and queue ingress findings
**Experiment**: hermes-perm-audit-006
**Date**: 2026-05-27

## Risk Assessment

### Critical Path Analysis

The execution chain is:
```
queue.json → worker_run_once() → check_worker_gates() → gate_policy.validate_task_gates() → execution
```

**Gate policy is the single checkpoint.** If gate_policy validates, execution proceeds. The audit confirms:
- Worker always calls gate_policy (Q002: PASS)
- Invalid items are denied (Q003: PASS)
- Mutations are detected (Q004: PASS)
- Replay is prevented by arm gate consumption (Q006: PASS)

### Bypass Vectors Assessed

| Vector | Status | Protection |
|--------|--------|------------|
| Manual queue injection | Blocked by gate_policy | Missing fields denied |
| Post-approval mutation | Blocked by gate_policy | Field mismatch detected |
| Stale approval replay | Blocked by arm gate | Arm gate consumed |
| File-level tampering | NOT blocked | No integrity check |
| Corrupt queue file | NOT handled | No quarantine |
| Audit log injection | Partially blocked | Caller discipline |

### Verdict

No critical bypass paths. The gate_policy checkpoint is effective for all programmatic paths. The residual risks (file-level tampering, corrupt files, audit leakage) require filesystem access or disk errors — they are medium severity, not critical.

## Recommendations for 007

1. **Queue item integrity**: Add HMAC signature to prevent file-level tampering
2. **Approval TTL**: Add expiration to prevent unbounded approval validity
3. **Recovery/quarantine**: Handle corrupt files gracefully
4. **Audit sink sanitization**: Sanitize in audit() itself, not just callers
