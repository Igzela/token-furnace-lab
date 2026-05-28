# Merged Harness Production Upgrade Plan

## Security Fixes (from Security agent review)

### S1. Path traversal via subproblem IDs [HIGH]
- Validate all artifact paths resolve within `run_dir` using `Path.resolve().is_relative_to()`
- Reject subproblem IDs containing `/`, `..`, or absolute paths
- **Status: IMPLEMENTED** — `safe_artifact_path()` + `safe_prompt_path()` helpers

### S2. Unbounded event store growth [MEDIUM]
- Add max file size check (10MB) to EventStore.append
- Raise `RuntimeError` if exceeded
- **Status: IMPLEMENTED** — `MAX_EVENT_STORE_BYTES` constant, checked in `append()`

### S3. Event store write race [MEDIUM]
- Use `threading.Lock` in EventStore.append for thread safety
- **Status: IMPLEMENTED** — `_lock` attribute, all reads/writes under `with self._lock`

### S4. Run directory collision [HIGH] (from GPT gate)
- Unique `run_id` using `{timestamp_ns}-{uuid_short}`
- `mkdir(exist_ok=False)` as belt-and-suspenders
- **Status: IMPLEMENTED** — `merged-{time_ns}-{uuid8}` format

## Production Gaps (from QA agent review)

### G1. LLM-as-judge quality gate
- Replace `_estimate_score` keyword counting with a real LLM call via bridge
- Fallback to keyword logic if bridge unavailable
- Judge prompt: score artifact on completeness, evidence quality, actionability
- **Status: IMPLEMENTED** — `llm_judge_score()` with fallback, called in gate evaluation

### G2. Real budget tracking
- Remove synthetic `BudgetReservation("tmp",...)` hack
- Pass real reservation through execution, accumulate actual usage
- **Status: IMPLEMENTED** — reservation passed through `_execute_bridge()`, usage recorded against it

### G3. Event store schema validation
- Define `ALLOWED_EVENT_TYPES` set with allowed `event_type` values
- Validate on append, reject non-conforming events
- **Status: IMPLEMENTED** — `Event.validate()` called in `EventStore.append()`

### G4. Adversarial review integration
- After quality gate, if artifacts exist, run adversarial review automatically
- Fused verdict feeds into retry/abort logic
- **Status: IMPLEMENTED** — `DevilsAdvocate` class, `fuse_verdicts()` deterministic fusion

### G5. Error handling + structured logging
- Wrap all I/O in try/except with typed events
- Add `logging` module with stderr output
- Bridge failures produce `agent_error` event, not unhandled traceback
- **Status: IMPLEMENTED** — `_run_inner()` try/except with error event + logging

## Validation Requirements (V1-V4, from GPT gate)

### V1. Task YAML schema validation
- **Status: IMPLEMENTED** — `validate_task_yaml()` checks required fields, subproblem structure, traversal IDs

### V2. Artifact path coverage
- **Status: IMPLEMENTED** — `safe_artifact_path()` + `safe_prompt_path()` cover both paths

### V3. Budget reservation threading
- **Status: IMPLEMENTED** — real reservation object passed through `_execute_bridge()` to `record_usage()`

### V4. Adversarial re-run on retry
- **Status: IMPLEMENTED** — adversarial review runs on each retry iteration

## Implementation Order (revised by GPT gate)

1. S4 + S1: run identity isolation + path traversal protection
2. G3 + S2 + S3: EventStore append hardening as one unit
3. V1 + G5: task YAML validation + structured error handling
4. G2: real budget tracking
5. G4: adversarial review integration
6. G1: LLM-as-judge

**All steps: COMPLETE**

## Verification

- Mock benchmark: 4/4 PASS (regression)
- Real LLM benchmark: 4/4 PASS
- Security: path traversal test (reject malicious IDs)
- Edge cases: empty artifact, duplicate event, missing YAML keys, bridge timeout
- Adversarial: mock adversarial review + deterministic fusion
- Event store: schema validation, size limit, thread safety
- Budget: real reservation tracking, no synthetic hacks

## GPT Gate Re-Review (after BLOCK fix)

First review: BLOCK (3 HIGH findings). All resolved:
- **Fusion**: PASS_WITH_NOTES now downgradeable via overrule + confidence >= 0.9
- **EventStore size**: pending event bytes included in size check
- **Budget**: judge and adversarial budget recorded against reservation

Final: **PASS_WITH_NOTES** (binary PASS for single-process scope)
Accepted limitations: symlink TOCTOU, multi-process, billing-grade budget accuracy
