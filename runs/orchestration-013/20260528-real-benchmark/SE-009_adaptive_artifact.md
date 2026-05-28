The table already contains `validate_review_artifact.py` and `validate_scope_diff.py` (lines 41-42). Only `validate_synthesis_evidence.py` is genuinely missing. I'll also note `validate_matrix_consistency.py` exists in scripts/ but isn't in the table.

---

**Score:** 92
**Verdict:** PASS_WITH_NOTES
**Confidence:** HIGH

## Findings

- [LOW] Task description claims three entries are missing, but `validate_review_artifact.py` (line 41) and `validate_scope_diff.py` (line 42) are already present. Only `validate_synthesis_evidence.py` is actually absent.
- [LOW] `validate_matrix_consistency.py` exists in `scripts/` but is not listed in the table — possible omission unrelated to the stated task.

## Corrected Validator Types Table

| Validator | Script | Severity Levels |
|-----------|--------|----------------|
| State machine | validate_state_machine.py | CRITICAL (missing states, UNIVERSAL rules) |
| Review artifact | validate_review_artifact.py | CRITICAL (missing score/verdict) |
| Scope diff | validate_scope_diff.py | CRITICAL (forbidden path) |
| Artifact schema | validate_artifact_schema.py | CRITICAL (missing required fields) |
| Synthesis evidence | validate_synthesis_evidence.py | CRITICAL (missing synthesis.md, verdicts, or evidence refs) |
| Evidence | validate_evidence() in tf_orchestrator.py | HIGH (blocking finding without evidence) |

The only change is the addition of the `Synthesis evidence` row between `Artifact schema` and `Evidence`, matching the existing format. The severity is `CRITICAL` because the script enforces structural completeness of synthesis artifacts (missing synthesis.md, missing verdicts, missing evidence references).

## Final Recommendation

REPAIR — apply the single-row addition to the wiki file. The task's claim about three missing entries is inaccurate; only one row needs adding.
