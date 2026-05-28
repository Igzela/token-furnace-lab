## Structured Review

### Current State

The wiki table at `knowledge/wiki/orchestrator-quality-gate-policy.md:38-44` lists 5 validators:

| # | Validator | Script |
|---|-----------|--------|
| 1 | State machine | validate_state_machine.py |
| 2 | Review artifact | validate_review_artifact.py |
| 3 | Scope diff | validate_scope_diff.py |
| 4 | Artifact schema | validate_artifact_schema.py |
| 5 | Evidence | validate_evidence() in tf_orchestrator.py |

`scripts/` contains 7 `validate_*.py` files. Two are missing from the table:

1. **`validate_synthesis_evidence.py`** — checks synthesis.md exists/non-empty, verdicts present, accepted findings have evidence references, known gaps listed when matrix has warn/partial/deferred status.
2. **`validate_matrix_consistency.py`** — checks matrix summary totals match actual case counts, by_status matches, P0 fails have follow-up, PASS cases have evidence_path, no PASS relies only on model_inference.

Neither script uses explicit severity labels; they output error counts. Based on what they check (synthesis completeness = structural requirement, matrix consistency = data integrity), appropriate severity mapping is CRITICAL for synthesis existence/verdicts and HIGH for matrix consistency issues.

### Corrected Table

| Validator | Script | Severity Levels |
|-----------|--------|----------------|
| State machine | validate_state_machine.py | CRITICAL (missing states, UNIVERSAL rules) |
| Review artifact | validate_review_artifact.py | CRITICAL (missing score/verdict) |
| Scope diff | validate_scope_diff.py | CRITICAL (forbidden path) |
| Artifact schema | validate_artifact_schema.py | CRITICAL (missing required fields) |
| Synthesis evidence | validate_synthesis_evidence.py | CRITICAL (missing synthesis/verdicts), HIGH (missing evidence refs, missing known gaps) |
| Matrix consistency | validate_matrix_consistency.py | HIGH (summary mismatch, P0 without follow-up, PASS without evidence) |
| Evidence | validate_evidence() in tf_orchestrator.py | HIGH (blocking finding without evidence) |

Note: `validate_run.py` (the 7th file) is an orchestrator/meta-validator that invokes the others, not a standalone validator — it belongs outside the table. The existing "Evidence" row references `validate_evidence()` inside `tf_orchestrator.py`, which is a different function from `validate_synthesis_evidence.py` (the script checks synthesis completeness, the function checks blocking-finding evidence paths).

---

**Score:** 95
**Verdict:** PASS
**Confidence:** HIGH

**Findings:**
- [LOW] Severity level assignments for the two new validators are inferred from script behavior, not explicit labels in the code. If the project later standardizes severity tagging inside scripts, these rows should be updated.

**Final Recommendation:** ACCEPT

The corrected table above is ready to apply. Want me to edit the wiki file directly?
