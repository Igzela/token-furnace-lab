# Codex: Regression Verification

**Role**: Verify no regression after gate_policy extraction
**Experiment**: hermes-perm-audit-005
**Date**: 2026-05-27

## Regression Results

### 004 Regression Suite

```
Layer 1: Basic Deny Assertions (14 tests)
  D001_marker_denies: PASS
  D001_worker_denies: PASS
  D002_marker_denies: PASS
  D002_worker_denies: PASS
  D003_marker_denies: PASS
  D003_worker_denies: PASS
  D010_marker_denies: PASS
  D010_worker_denies: PASS
  D014_marker_denies: PASS
  D014_worker_denies: PASS
  D018_marker_denies: PASS
  D018_worker_denies: PASS
  D019_marker_denies: PASS
  D019_worker_denies: PASS

Layer 2: Dual-Path Conformance (3 tests)
  dual_allow_marker: PASS
  dual_allow_worker: PASS
  dual_allow_match: PASS

Layer 3: Worker No-Execute After Deny (3 tests)
  deny_no_execute: PASS
  deny_has_reason: PASS
  deny_no_marker: PASS

Layer 4: Redaction Persistence (4 tests)
  redaction_token_redacted: PASS
  redaction_marker_present: PASS
  redaction_aws: PASS
  redaction_bearer: PASS

Total: 24/24 PASS
```

### Smoke Tests

| Suite | Result | Tests |
|-------|--------|-------|
| live4c | PASS | marker disabled check |
| live6 | PASS | request boundary |
| live7 | PASS | 34/34 auto worker |
| live9c | PASS | 12/12 permission deny dry run |
| live9d | PASS | 11/11 permission deny worker |

### Behavior Change Analysis

| Aspect | Before (004) | After (005) | Changed? |
|--------|-------------|-------------|----------|
| D001 deny | deny | deny | No |
| D002 deny | deny | deny | No |
| D003 deny | deny | deny | No |
| D010 deny | deny | deny | No |
| D014 deny | deny | deny | No |
| D018 deny | deny | deny | No |
| D019 deny | deny | deny | No |
| Dual-path match | match | match | No |
| Worker no-execute | verified | verified | No |
| Redaction | verified | verified | No |

### Import Safety Check

gate_policy.py on import:
- Does NOT read files ✓
- Does NOT start daemons ✓
- Does NOT parse CLI args ✓
- Does NOT access queue ✓
- Does NOT read env (flags_from_env reads on call) ✓

### Verdict

No regression detected. All 24 regression tests pass. All smoke tests pass. Behavior unchanged.
