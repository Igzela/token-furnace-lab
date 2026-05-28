# Orchestrator Quality Gate Policy

## Gate Priority Rules (Fixed)

The quality gate evaluates in this strict order. Each level overrides all lower levels:

```
1. Artifact exists?           → REJECT
2. Validator errors CRITICAL/HIGH? → REPAIR or ESCALATE
3. Evidence errors?           → REPAIR or ESCALATE
4. Blocking findings?         → REPAIR or ESCALATE
5. Score below threshold?     → REPAIR or ESCALATE
6. Verdict not accepted?      → REPAIR or ESCALATE
7. All checks pass            → ACCEPT
```

**Key invariant**: A 91/100 score CANNOT override a structural failure.

## Failure-Injection Test Matrix

| Case | Trigger | Expected | Validated |
|------|---------|----------|-----------|
| F001 | Missing artifact | REJECT | Yes |
| F002 | Missing score | REPAIR | Yes |
| F003 | Invalid verdict | REPAIR | Yes |
| F004 | Score PASS + blocking HIGH open | REPAIR | Yes |
| F005 | Blocking finding no evidence_path | REPAIR | Yes |
| F006 | evidence_path doesn't exist | REPAIR | Yes |
| F007 | Forbidden path touched | REPAIR | Yes |
| F008 | Undefined transition target | REPAIR | Yes |
| F009 | Repair rounds exhausted | ESCALATE | Yes |
| F010 | Validator FAIL + review PASS | REPAIR | Yes |

**Result**: 10/10 pass, 0 false accepts.

## Validator Types

| Validator | Script | Severity Levels |
|-----------|--------|----------------|
| State machine | validate_state_machine.py | CRITICAL (missing states, UNIVERSAL rules) |
| Review artifact | validate_review_artifact.py | CRITICAL (missing score/verdict) |
| Scope diff | validate_scope_diff.py | CRITICAL (forbidden path) |
| Artifact schema | validate_artifact_schema.py | CRITICAL (missing required fields) |
| Evidence | validate_evidence() in tf_orchestrator.py | HIGH (blocking finding without evidence) |

## Design Decisions

### Why blocking findings override score?

Because reviewers are non-deterministic. A reviewer might overlook a missing UNIVERSAL hard-fault rule and still give 90/100. The gate must catch structural issues regardless of score.

### Why validator errors override everything?

Validators are deterministic and cheap. Reviewers are expensive and non-deterministic. Run validators first — if they fail, don't waste a review call.

### Why evidence validation is separate from schema?

Schema validates structure (fields exist, types correct). Evidence validates content (blocking findings have backing files). Both are necessary; neither is sufficient.

## Related Rules

- [[ER-schema-invalid-cannot-pass]]
- [[ER-validator-fail-overrides-review-score]]
