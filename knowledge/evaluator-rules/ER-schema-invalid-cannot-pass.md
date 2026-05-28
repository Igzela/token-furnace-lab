# Evaluator Rule: Schema Invalid Cannot Pass

**Rule**: If an artifact's JSON block fails schema validation, the gate MUST NOT return ACCEPT.

**Priority**: Overrides reviewer score. A 91/100 score cannot cover a schema failure.

**Rationale**: Schema validation catches structural issues that reviewers miss:
- Missing required fields (score, verdict, findings)
- Invalid field types (score as string, verdict as number)
- Invalid enum values (verdict = "CONDITIONAL_PASS")
- Missing JSON block entirely

**Application**:
- Run `validate_artifact_schema.py` before `evaluate_gate()`
- If schema validation fails with CRITICAL/HIGH errors → gate returns REPAIR
- If schema validation fails after max repair rounds → gate returns ESCALATE

**Test coverage**: F002 (missing score), F003 (invalid verdict)
