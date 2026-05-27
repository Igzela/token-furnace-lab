# Decision Record: hermes-perm-audit-007

## DR-0013: Queue Hardening Fix

**Status**: Accepted
**Date**: 2026-05-27
**Experiment**: hermes-perm-audit-007

### Context

006 found 3 WARN items in queue ingress audit:
- Q005: No approval TTL (arm gate is actual protection)
- Q007: No recovery/quarantine for corrupt files
- Q008: audit() doesn't sanitize payload

### Decision

Implement 2 of 3 fixes:
1. **audit() sink sanitization**: Add `sanitize_payload()` that recursively applies `sanitize_text()` before writing
2. **Broken queue quarantine**: `load_queue()` quarantines corrupt files instead of crashing

Defer FIX-003 (arm gate TTL) — already has `expires_at` field, verified by Q006.

### Rationale

- **Sink sanitization**: Security sinks should not trust callers. Defense-in-depth.
- **Quarantine**: Corrupt files should not crash operations. Graceful degradation.
- **TTL deferral**: Arm gate already has TTL. No additional code needed.

### Consequences

**Positive**:
- Q007 and Q008 upgraded from WARN to PASS
- Audit entries now sanitized at sink (not just callers)
- Corrupt queue files quarantined with metadata

**Negative**:
- Quarantine returns empty queue (tasks lost if not backed up)
- sanitize_payload adds overhead to every audit write (minimal)

### Verdict

PASS — 24/24 regression, 10/10 audit, Q007+Q008 upgraded.
