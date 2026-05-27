# Deny-Path Test Plan: hermes-perm-audit-002

Generated: 2026-05-27

## Experiment Verdict: COMPLETE

### Why Complete
- 25-case deny-path matrix converted to path-aware form
- P0 cases identified (10 cases)
- marker_executor and worker_daemon compared per case
- gate conformance matrix created (C001-C005)
- non-live boundary preserved
- no production worker patch applied

## Target Control Verdict: FAIL

### Why FAIL
- 6/25 cases diverge between paths (D001, D002, D003, D010, D012)
- Worker daemon is less restrictive than canonical marker executor
- D001/D002: LIVE_ENABLED not checked by worker (critical)
- D010: idempotency key not checked by worker (high)
- D014-D016: rollback plan missing on both paths (high)
- D024: secret redaction missing on both paths (medium)
- C001: worker does not use canonical gate function (critical)
- C003: worker and marker produce different deny/allow for P0 cases (critical)

## Cross-Path Findings

| Case | marker_executor | worker_daemon | Conformance |
|------|----------------|---------------|-------------|
| D001 | deny | allow | FAIL |
| D002 | deny | allow | FAIL |
| D003 | deny (partial) | allow | FAIL |
| D004 | deny | deny | pass |
| D005 | deny | deny | pass |
| D006 | deny | deny | pass |
| D007 | deny (partial) | deny (partial) | pass |
| D008 | missing | missing | pass |
| D009 | deny (partial) | deny (partial) | pass |
| D010 | deny | allow | FAIL |
| D011 | deny (partial) | deny (partial) | pass |
| D012 | deny (partial) | allow | FAIL |
| D013 | deny (partial) | deny (partial) | pass |
| D014 | missing | missing | pass |
| D015 | missing | missing | pass |
| D016 | missing | missing | pass |
| D017 | deny (partial) | deny (partial) | pass |
| D018 | deny | deny | pass |
| D019 | deny | deny | pass |
| D020 | deny | deny | pass |
| D021 | deny | deny | pass |
| D022 | deny (partial) | deny (partial) | pass |
| D023 | deny (partial) | deny (partial) | pass |
| D024 | missing | missing | pass |
| D025 | deny | deny | pass |

## Gate Conformance Summary

| Case | Expected | Actual | Status |
|------|----------|--------|--------|
| C001: worker uses canonical gate | true | false | FAIL |
| C002: worker covers all marker gates | true | false | FAIL |
| C003: same deny/allow for P0 | true | false | FAIL |
| C004: no bypass entry | true | unknown | untested |
| C005: no execute after deny | true | partial | partial |

## Required 003 Fixes

1. Make worker_daemon use same canonical gate logic as marker_executor
2. D001/D002/D010 must change from missing to complete on worker path
3. D014 rollback plan must deny on live-intent tasks
4. D024 reason field must be redacted before audit persistence
5. Dual-path P0 conformance tests must pass

## Knowledge Updates

- F-0001 refined: "duplicated worker gate diverges from canonical"
- gate-conformance-matrix.yaml created (C001-C005)
- deny-path-matrix.yaml updated with per-path status
- evaluator-rules/ER-0001 updated with conformance requirement
