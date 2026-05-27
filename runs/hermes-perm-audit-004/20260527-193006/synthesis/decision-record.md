# Decision Record: hermes-perm-audit-004

## DR-0010: Gate Conformance Regression Suite

**Status**: Accepted
**Date**: 2026-05-27
**Experiment**: hermes-perm-audit-004

### Context

hermes-perm-audit-003 fixed 6 divergent deny cases between marker_executor and worker_daemon. But conformance was verified by 6 separate smoke test suites with 57 assertions — not a dedicated conformance regression suite. Need a single test script that validates behavioral equivalence for all P0 deny cases.

### Decision

Implement a 4-layer regression test suite:

1. **Layer 1: Basic Deny Assertions** — Test each P0 deny case on both paths (7 cases x 2 paths = 14 tests)
2. **Layer 2: Dual-Path Conformance** — Verify both paths produce identical decisions for valid tasks (3 tests)
3. **Layer 3: Worker No-Execute** — Verify deny prevents execution (3 tests)
4. **Layer 4: Redaction Persistence** — Verify secrets are scrubbed in audit log (4 tests)

### Rationale

- **Defense-in-depth**: 4 layers catch different failure modes (gate divergence, equivalence failure, enforcement gap, data leakage)
- **Shared fixture**: TestFixture provides identical inputs to both paths, eliminating test setup divergence
- **Minimal scope**: Only tests 003 fixes (7/8 P0 cases), not pre-existing logic
- **Executable**: Single `python3 scripts/gate_conformance_regression.py` command

### Consequences

**Positive**:
- Regression suite catches future gate divergence automatically
- 24 tests run in <1 second
- Clear pass/fail verdict for CI integration

**Negative**:
- D012 (idempotency mismatch) not covered — acceptable since 003 didn't modify this
- D024 (secret in description) not covered — acceptable since 003 focused on reason field
- TestFixture creates temp directories — cleanup required

### Alternatives Considered

1. **Parameterized pytest suite**: More idiomatic but requires pytest dependency
2. **Extend existing smoke tests**: Would dilute smoke test focus
3. **Shared gate policy extraction**: Deferred to 005

### Implementation Notes

- `approve_task()` and `execute_dry_run()` reset `external_side_effect` to False — D018 test must set flag after both steps
- `audit()` doesn't sanitize payload — callers must sanitize before writing (matching `_require_reason` pattern)
- TestFixture.set_task_field() helper needed for post-creation field modification

### Verdict

PASS — All 24 tests pass, 0 failures.
