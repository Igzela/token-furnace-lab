## Structured Review

**Score: 92/100**
**Verdict: PASS_WITH_NOTES**
**Confidence: HIGH**

### Findings

- [NOTE] `validate_run.py` (the 7th file) is the orchestrator entry point, not a validator type — correctly excluded from the table.
- [NOTE] Severity levels for the two new validators are inferred from script content. `validate_synthesis_evidence.py` checks verdicts and gaps → HIGH. `validate_matrix_consistency.py` checks summary totals and P0 follow-ups → CRITICAL (structural inconsistency).

### Corrected Table

```
| Validator | Script | Severity Levels |
|-----------|--------|----------------|
| State machine | validate_state_machine.py | CRITICAL (missing states, UNIVERSAL rules) |
| Review artifact | validate_review_artifact.py | CRITICAL (missing score/verdict) |
| Scope diff | validate_scope_diff.py | CRITICAL (forbidden path) |
| Artifact schema | validate_artifact_schema.py | CRITICAL (missing required fields) |
| Evidence | validate_evidence() in tf_orchestrator.py | HIGH (blocking finding without evidence) |
| Synthesis evidence | validate_synthesis_evidence.py | HIGH (missing synthesis, verdicts, or evidence gaps) |
| Matrix consistency | validate_matrix_consistency.py | CRITICAL (summary totals mismatch, missing P0 follow-up) |
```

### Final Recommendation

**REPAIR** — Apply the corrected table to `knowledge/wiki/orchestrator-quality-gate-policy.md` lines 38–44.
