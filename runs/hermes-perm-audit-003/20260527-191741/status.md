# Run Status: hermes-perm-audit-003/20260527-191741

Created: 2026-05-27T19:17:41
Operator: igzela
Target: /home/igzela/Projects/hermes-gateway-lab

## Status: COMPLETE

### Verdicts
- experiment_verdict: COMPLETE
- target_control_verdict: PASS_WITH_NOTES
- reason: All 4 fixes implemented, C001-C005 pass (C001 partial), 0/25 divergent cases, no regressions

### Checklist
- [x] 003 run directory created
- [x] Fix 1: Worker imports flags_from_env, adds LIVE_ENABLED + idempotency checks
- [x] Fix 2: rollback_plan field added to task schema, gate validates presence
- [x] Fix 3: Secret redaction in sanitize_text (6 pattern types)
- [x] Fix 4: risk_class and external_side_effect checks added to worker
- [x] All 6 smoke test suites pass (57 total assertions)
- [x] 3 model outputs generated
- [x] Synthesis files generated (comparison, decision-record)
- [x] Gate conformance matrix updated (C002-C005 pass, C001 partial)
- [x] Deny-path matrix updated (0/25 divergent)

### Key Findings
1. D001/D002/D003/D010: LIVE_ENABLED and idempotency checks now present in worker
2. D014/D015: rollback_plan field and validation added
3. D024: Secret redaction covers sk-, key-, api_, Bearer, AWS AKIA, PEM keys
4. C001 partial: worker still uses independent function (not delegating to check_gates)
5. No regressions: all previously conformant cases remain conformant

### Next Experiment
hermes-perm-audit-004: Regression test suite
Goal: Automated conformance test that runs both paths with identical inputs
