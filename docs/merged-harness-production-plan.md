# Merged Harness Production Upgrade Plan

## Security Fixes (from Security agent review)

### S1. Path traversal via subproblem IDs [HIGH]
- Validate all artifact paths resolve within `run_dir` using `Path.resolve().is_relative_to()`
- Reject subproblem IDs containing `/`, `..`, or absolute paths

### S2. Unbounded event store growth [MEDIUM]
- Add max file size check (10MB) to EventStore.append
- Raise if exceeded, log warning

### S3. Event store write race [MEDIUM]
- Use `threading.Lock` in EventStore.append for thread safety

## Production Gaps (from QA agent review)

### G1. LLM-as-judge quality gate
- Replace `_estimate_score` keyword counting with a real LLM call via bridge
- Fallback to keyword logic if bridge unavailable
- Judge prompt: score artifact on completeness, evidence quality, actionability

### G2. Real budget tracking
- Remove synthetic `BudgetReservation("tmp",...)` hack
- Pass real reservation through execution, accumulate actual usage

### G3. Event store schema validation
- Define `EVENT_SCHEMA` with required fields and allowed `event_type` values
- Validate on append, reject non-conforming events

### G4. Adversarial review integration
- After quality gate, if artifacts exist, run adversarial review automatically
- Fused verdict feeds into retry/abort logic

### G5. Error handling + structured logging
- Wrap all I/O in try/except with typed events
- Add `logging` module with JSON-lines output per run
- Bridge failures produce `bridge_failed` event, not unhandled traceback

## Implementation Order

1. Security fixes (S1-S3) — foundational, blocks everything
2. Error handling (G5) — needed before other changes
3. Event schema (G3) — clean foundation
4. Budget tracking (G2) — simple fix
5. Adversarial wiring (G4) — integrates existing module
6. LLM-as-judge (G1) — most complex, last

## Verification

- Mock benchmark: 4/4 PASS (regression)
- Real LLM benchmark: 4/4 PASS
- Security: path traversal test (reject malicious IDs)
- Edge cases: empty artifact, duplicate event, missing YAML keys, bridge timeout
