# Decision Record: hermes-perm-audit-005

## DR-0011: Shared Gate Policy Extraction

**Status**: Accepted
**Date**: 2026-05-27
**Experiment**: hermes-perm-audit-005

### Context

After 003/004, behavioral equivalence is achieved (0/25 divergence) and locked by regression tests (24/24 pass). But both paths still maintain independent gate logic — C001 remains "partial". The architectural root cause of gate drift hasn't been fixed.

### Decision

Extract shared `gate_policy.py` module with:
- `LiveFlags` dataclass
- `flags_from_env()` function (reads env on call, not on import)
- `GateDenied` exception
- `validate_task_gates(task, dry_run, flags)` — 11 canonical gate checks

Both `local_marker_executor.py` and `local_execution_worker.py` import from `gate_policy` and delegate core permission checks to `validate_task_gates()`.

### Rationale

- **Single source of truth**: Canonical gate logic lives in one place
- **Import-safe**: No I/O, no daemon, no CLI, no queue access on import
- **Clean error boundary**: `GateDenied` is neutral; callers re-raise as their own type
- **No behavior change**: 24/24 regression tests pass, all smoke tests pass
- **C001 upgrade**: From "partial" to "pass"

### Key Design Decisions

1. **GateDenied as intermediate exception**: gate_policy raises neutral exception, callers catch and re-raise as `LocalMarkerError` / `WorkerError`. Preserves error semantics.

2. **LiveFlags in gate_policy**: Moved from local_marker_executor to gate_policy. Marker executor re-exports for backwards compatibility. Worker imports from gate_policy directly.

3. **Worker-only checks stay in worker**: Arm gate validation (created_by, expires_at, request_id match, consumed, max_executions) is operational, not policy.

4. **Marker-only checks stay in marker**: Marker file existence check is marker-specific.

### Consequences

**Positive**:
- Future gate changes only need to happen in one place
- C001 no longer "partial"
- Clear separation: policy (gate_policy) vs operational (arm gate, marker exists)

**Negative**:
- One more import dependency
- live6 smoke test needed rollback_plan fix (same pattern as 004)

### Verdict

PASS — 24/24 regression, all smoke tests pass, C001 → pass.
