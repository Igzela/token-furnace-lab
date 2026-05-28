# Synthesis: Orchestration-003 Failure-Injection Benchmark

**Date**: 2026-05-28 11:26
**Total cases**: 10
**Passed**: 10/10
**False accepts**: 0
**Verdict**: PASS

## Gate Priority Rules Validated

1. Validator FAIL overrides reviewer score
2. Blocking HIGH finding overrides score
3. Missing evidence triggers REPAIR
4. Scope violations trigger REPAIR
5. Repair exhaustion triggers ESCALATE
6. Missing artifact triggers REJECT

## Cases Summary

- **F001_missing_artifact**: REJECT (PASS) — Artifact missing
- **F002_missing_score**: REPAIR (PASS) — Score 0 < 70
- **F003_invalid_verdict**: REPAIR (PASS) — Verdict FAIL not in {'PASS', 'PASS_WITH_NOTES'}
- **F004_blocking_high_open**: REPAIR (PASS) — Evidence errors: HIGH: Blocking finding F01 has no evidence_path
- **F005_no_evidence**: REPAIR (PASS) — Evidence errors: HIGH: Blocking finding F01 has no evidence_path
- **F006_evidence_not_exist**: REPAIR (PASS) — Evidence errors: HIGH: Blocking finding F01 evidence_path not found: nonexistent/path/model.md
- **F007_forbidden_path**: REPAIR (PASS) — Evidence errors: forbidden_path: .env
- **F008_bad_transition**: REPAIR (PASS) — Validator errors: HIGH: Transition target 'NONEXISTENT_STATE' not in state definitions
- **F009_repair_exhausted**: ESCALATE (PASS) — Evidence errors after 3 rounds: HIGH: Blocking finding F01 has no evidence_path
- **F010_validator_fail_review_pass**: REPAIR (PASS) — Validator errors: CRITICAL: No UNIVERSAL hard-fault block in transition matrix; HIGH: Active state FOC_NORMAL missing oc_trip path
