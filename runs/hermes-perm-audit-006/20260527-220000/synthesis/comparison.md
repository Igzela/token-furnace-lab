# Model Comparison: hermes-perm-audit-006

## Task Distribution

| Model | Role | Scope |
|-------|------|-------|
| Claude Code | Auditor | Audit queue ingress paths, write verification script |
| GPT | Reviewer | Review bypass risk matrix |
| Codex | Verifier | Verify no live execution |

## Findings Comparison

### Q002: Worker Final Gate

| Model | Finding | Agreement |
|-------|---------|-----------|
| Claude Code | gate_policy called unconditionally | ✓ |
| GPT | Single checkpoint effective | ✓ |

### Q003-Q004: Injection/Mutation

| Model | Finding | Agreement |
|-------|---------|-----------|
| Claude Code | Invalid items denied, well-crafted pass | ✓ |
| GPT | Gate policy effective for programmatic paths | ✓ |

### Q005-Q006: Replay Protection

| Model | Finding | Agreement |
|-------|---------|-----------|
| Claude Code | Arm gate consumption prevents replay | ✓ |
| GPT | Arm gate is actual protection, not idempotency key | ✓ |

### Risk Assessment

| Risk | Claude Code | GPT | Agreement |
|------|-------------|-----|-----------|
| File tampering | Medium | Medium | ✓ |
| Stale approval | Low (arm gate) | Low (arm gate) | ✓ |
| Corrupt files | Medium | Medium | ✓ |
| Audit leakage | Low | Low | ✓ |

## Agreement Summary

All 3 models agree:
1. No critical bypass paths found
2. gate_policy is effective checkpoint
3. Arm gate consumption is primary replay protection
4. Known gaps are medium/low severity, not critical

No disagreements found.
