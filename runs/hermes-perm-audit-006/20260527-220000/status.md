# Run Status: hermes-perm-audit-006/20260527-220000

Created: 2026-05-27T22:00:00
Operator: claude-code
Target: /home/igzela/Projects/hermes-gateway-lab

## Status: COMPLETE

### Verdicts
- experiment_verdict: COMPLETE
- target_control_verdict: PASS_WITH_NOTES
- reason: 5/8 pass, 3 warnings. No critical bypass paths found. Known gaps documented.

### Checklist
- [x] 006 run directory created
- [x] Queue writer inventory (Q001): 9 production write paths identified
- [x] Worker final gate (Q002): gate_policy called unconditionally before execution
- [x] Manual injection (Q003): invalid items denied, well-crafted items pass (no integrity check)
- [x] Post-approval mutation (Q004): mutation detected by gate_policy
- [x] Stale approval (Q005): no TTL, arm gate consumption is actual protection
- [x] Idempotency replay (Q006): arm gate consumed, replay prevented
- [x] Broken queue (Q007): corrupt file raises exception, no quarantine
- [x] Audit sanitization (Q008): audit() doesn't sanitize, caller discipline required
- [x] 3 model outputs generated
- [x] Synthesis files generated

### Key Findings
1. Worker always calls gate_policy before execution — no bypass paths
2. Gate_policy catches missing approval, wrong risk class, external side effects
3. No integrity check on queue items — file-level tampering possible
4. Arm gate consumption prevents replay (not idempotency key consumption)
5. No approval TTL — approvals valid indefinitely
6. No recovery/quarantine for corrupt queue files
7. audit() doesn't sanitize payload — depends on caller discipline

### Risk Assessment
- No critical bypass paths found
- 2 medium residual risks (file tampering, corrupt files)
- 3 low residual risks (stale approval, audit leakage, bridge writes)

### Next Experiment
hermes-perm-audit-007: Queue hardening (if needed)
- Add approval TTL
- Add queue item integrity check
- Add recovery/quarantine mechanism
- Add audit() sink sanitization
