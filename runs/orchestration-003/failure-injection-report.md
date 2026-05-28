# Failure-Injection Test Report

**Date**: 2026-05-28 11:26
**Total cases**: 10
**Passed**: 10
**Failed**: 0
**False accepts**: 0
**Result**: PASS

## Criteria

- critical_cases_pass: 100%
- false_accept_count: 0

## Cases

| Case | Expected | Actual | Reason | Status |
|------|----------|--------|--------|--------|
| F001_missing_artifact | REJECT | REJECT | Artifact missing | PASS |
| F002_missing_score | REPAIR | REPAIR | Score 0 < 70 | PASS |
| F003_invalid_verdict | REPAIR | REPAIR | Verdict FAIL not in {'PASS', 'PASS_WITH_NOTES'} | PASS |
| F004_blocking_high_open | REPAIR | REPAIR | Evidence errors: HIGH: Blocking finding F01 has no evidence_... | PASS |
| F005_no_evidence | REPAIR | REPAIR | Evidence errors: HIGH: Blocking finding F01 has no evidence_... | PASS |
| F006_evidence_not_exist | REPAIR | REPAIR | Evidence errors: HIGH: Blocking finding F01 evidence_path no... | PASS |
| F007_forbidden_path | REPAIR | REPAIR | Evidence errors: forbidden_path: .env | PASS |
| F008_bad_transition | REPAIR | REPAIR | Validator errors: HIGH: Transition target 'NONEXISTENT_STATE... | PASS |
| F009_repair_exhausted | ESCALATE | ESCALATE | Evidence errors after 3 rounds: HIGH: Blocking finding F01 h... | PASS |
| F010_validator_fail_review_pass | REPAIR | REPAIR | Validator errors: CRITICAL: No UNIVERSAL hard-fault block in... | PASS |

## Failed Cases Detail
