# Decision Record — hermes-perm-audit-003

## DR-0009: Worker gate conformance via check injection

**Decision:** Add canonical gate checks directly to `check_worker_gates` rather than delegating to `check_gates` from `local_marker_executor`.

**Rationale:** The worker has additional gate requirements (arm gate validation, request state checks) that don't exist in the marker executor. Delegating to `check_gates` would require refactoring the marker executor to accept external gate results. The injection approach preserves the worker's autonomy while achieving behavioral equivalence.

**Trade-off:** Code duplication between the two gate functions. Mitigated by the shared `flags_from_env` import and identical validation logic.

## DR-0010: Rollback plan as required string field

**Decision:** Add `rollback_plan` as a required string field to the task schema. Gate denies if empty.

**Rationale:** The YAML specs (live4a, live0) declare `rollback_plan_present` as a required gate. Making it a string field (rather than a boolean) allows future content validation.

**Trade-off:** Existing tasks without rollback plans will fail the gate. This is intentional — forces explicit rollback plan declaration.

## DR-0011: Secret redaction in sanitize_text

**Decision:** Add regex-based secret detection to `sanitize_text` rather than a separate redaction function.

**Rationale:** `sanitize_text` is called pervasively (task IDs, reasons, metadata). Integrating redaction here provides defense-in-depth without requiring callers to opt-in.

**Trade-off:** Regex patterns may produce false positives on non-secret strings containing patterns like "sk-" followed by alphanumeric characters. Acceptable given the 500-char truncation limit.
