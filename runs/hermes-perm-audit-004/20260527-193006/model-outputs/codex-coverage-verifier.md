# Codex: Coverage Verification

**Role**: Verify test coverage for gate conformance regression suite
**Experiment**: hermes-perm-audit-004
**Date**: 2026-05-27

## Coverage Matrix

### Layer 1: Basic Deny Assertions

| Case | Marker Path | Worker Path | Status |
|------|------------|-------------|--------|
| D001 | ✓ | ✓ | COVERED |
| D002 | ✓ | ✓ | COVERED |
| D003 | ✓ | ✓ | COVERED |
| D010 | ✓ | ✓ | COVERED |
| D012 | - | - | NOT COVERED |
| D014 | ✓ | ✓ | COVERED |
| D018 | ✓ | ✓ | COVERED |
| D019 | ✓ | ✓ | COVERED |

**Coverage**: 7/8 cases (87.5%)

### Layer 2: Dual-Path Conformance

| Test | Description | Status |
|------|-------------|--------|
| dual_allow_marker | Valid task allowed by marker | ✓ |
| dual_allow_worker | Valid task allowed by worker | ✓ |
| dual_allow_match | Both paths agree | ✓ |

**Coverage**: 3/3 tests (100%)

### Layer 3: Worker No-Execute

| Test | Description | Status |
|------|-------------|--------|
| deny_no_execute | Worker doesn't execute on deny | ✓ |
| deny_has_reason | Deny reason contains "gate_failed" | ✓ |
| deny_no_marker | No marker file on deny | ✓ |

**Coverage**: 3/3 tests (100%)

### Layer 4: Redaction Persistence

| Test | Description | Status |
|------|-------------|--------|
| redaction_token_redacted | sk- token not in audit | ✓ |
| redaction_marker_present | REDACTED marker in audit | ✓ |
| redaction_aws | AWS AKIA key redacted | ✓ |
| redaction_bearer | Bearer token redacted | ✓ |

**Coverage**: 4/4 tests (100%)

## Risk Assessment

### Covered Risks
- LIVE_ENABLED bypass (D001/D002)
- Scope bypass (D003)
- Idempotency bypass (D010)
- Rollback bypass (D014)
- External side effect bypass (D018)
- Private content bypass (D019)
- Dual-path divergence
- Worker execution after deny
- Secret leakage in audit log

### Uncovered Risks
- D012: Idempotency key mismatch (not tested, but 003 didn't modify this)
- D024: Secret in description field (not tested)
- Arm gate expiration (not tested)
- Max executions exceeded (not tested)
- Marker already exists (not tested)

### Verdict

Coverage is sufficient for regression testing of 003 fixes. The 7 tested deny cases are the ones that were fixed in 003. Uncovered cases (D012, D024, arm gate, max executions, marker exists) are pre-existing and not part of 003 scope.

## Recommendations for 005+

1. Add D012 test when idempotency logic is refactored
2. Add D024 test when description sanitization is added
3. Add arm gate expiration test when arm gate logic is reviewed
4. Add parameterized test runner for deny cases (reduce boilerplate)
