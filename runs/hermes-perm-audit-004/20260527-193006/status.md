# Run Status: hermes-perm-audit-004/20260527-193006

Created: 2026-05-27T19:30:06
Operator: claude-code
Target: /home/igzela/Projects/hermes-gateway-lab

## Status: COMPLETE

### Verdicts
- experiment_verdict: COMPLETE
- target_control_verdict: PASS
- reason: All 24 regression tests pass across 4 layers, 0 failures

### Checklist
- [x] 004 run directory created
- [x] gate_conformance_regression.py written (4-layer test architecture)
- [x] Layer 1: 7 P0 deny cases tested on both paths (14 tests)
- [x] Layer 2: Dual-path conformance verified (3 tests)
- [x] Layer 3: Worker no-execute after deny verified (3 tests)
- [x] Layer 4: Redaction persistence verified (4 tests)
- [x] All 24 tests pass
- [x] 3 model outputs generated
- [x] Synthesis files generated (comparison, decision-record, cost_estimate)
- [x] Gate conformance matrix updated (C001 upgrade to full pass)
- [x] Scripts committed to hermes-gateway-lab

### Key Findings
1. D018 fix: `approve_task` and `execute_dry_run` reset `external_side_effect` to False — test must set flag after both steps
2. Redaction fix: `audit()` doesn't sanitize payload — callers must sanitize before writing (matching `_require_reason` pattern)
3. All 003 fixes remain in place — no regressions detected
4. Dual-path equivalence confirmed for all P0 deny cases

### Next Experiment
hermes-perm-audit-005: Shared gate policy extraction
Goal: Extract canonical gate logic into shared module used by both paths
