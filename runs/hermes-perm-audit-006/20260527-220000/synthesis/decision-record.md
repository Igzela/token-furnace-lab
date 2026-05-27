# Decision Record: hermes-perm-audit-006

## DR-0012: Queue Ingress / Bypass Entry Audit

**Status**: Accepted
**Date**: 2026-05-27
**Experiment**: hermes-perm-audit-006

### Context

After 001-005, gate_policy.py is the single source of truth for canonical gates. Both paths delegate to it. But the security model assumes "all execution goes through gate_policy". 006 verifies this assumption by checking for bypass entry points.

### Decision

Audit 8 queue ingress questions:
1. Queue writer inventory (Q001)
2. Worker final gate (Q002)
3. Manual injection (Q003)
4. Post-approval mutation (Q004)
5. Stale approval replay (Q005)
6. Idempotency replay (Q006)
7. Broken queue recovery (Q007)
8. Audit sanitization (Q008)

### Findings

**PASS (5/8)**:
- Q001: 9 production write paths identified
- Q002: Worker always calls gate_policy before execution
- Q003: Invalid injected items denied by gate_policy
- Q004: Post-approval mutations detected
- Q006: Arm gate consumption prevents replay

**WARN (3/8)**:
- Q005: No approval TTL (arm gate is actual protection)
- Q007: No recovery/quarantine for corrupt files
- Q008: audit() doesn't sanitize payload

### Key Insight

**Arm gate consumption is the primary replay prevention mechanism**, not idempotency key consumption. The idempotency key is presence-checked but never consumed. The arm gate IS consumed after use, which prevents direct worker execution replays.

### Residual Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| File-level queue tampering | Medium | No integrity check (defer to 007) |
| Corrupt queue files | Medium | No quarantine (defer to 007) |
| Stale approval | Low | Arm gate consumption prevents replay |
| Audit leakage | Low | Most callers sanitize |

### Verdict

PASS_WITH_NOTES — No critical bypass paths. Known gaps documented for 007 hardening.
