# Workflow Quality-Gate Audit — Phase 1 Closeout

## Metadata

- Phase: workflow-quality-gate-audit-phase-1
- Experiments: 001, 002
- Status: COMPLETE
- Created: 2026-05-28

## Triple Verdict

```yaml
phase_verdict: COMPLETE
target_control_verdict: PASS_WITH_NOTES
platform_validation_verdict: PASS
```

## Timeline

| Date | Experiment | Activity | Commit |
|------|------------|----------|--------|
| 2026-05-28 | 001 | Workflow quality-gate audit | ee718d0 |
| 2026-05-28 | 002 | Validator implementation | f3b8346 |

## 001: Workflow Quality-Gate Audit

### Findings
- 30-case matrix: 27 PASS, 3 WARN, 0 FAIL
- Strong gates: 27/30 (experiment definition, evidence, matrix, verdict, fix, regression, closeout)
- Weak gates: 3 (pre/post status, matrix summary counts, Codex role)

### Key Finding
**Token Furnace Lab v1 workflow is structurally sound, but not yet mechanically enforced.**

## 002: Validator Implementation

### Validators Created
1. **validate_run.py** (updated): canonical layout, flexible names, role contract
2. **validate_matrix_consistency.py** (new): 5 consistency checks
3. **validate_synthesis_evidence.py** (new): verdict/evidence/known-gaps checks

### Test Results
- workflow-quality-gate-matrix.yaml: PASS (30 cases)
- Recent runs: PASS_WITH_WARNINGS (optional files)

## Known Notes

1. **Legacy layout supported**: model-outputs/ still works with warnings
2. **Recent runs pass with warnings**: Not strict clean pass (optional files missing)
3. **Codex role is contract-based**: Not globally mandatory, but if declared, output must exist
4. **Future improvement**: Strict mode that fails legacy layout after migration

## Knowledge Assets Created

- `knowledge/wiki/token-furnace-workflow-quality-gates.md`
- `knowledge/wiki/token-furnace-workflow-validators.md`
- `knowledge/failures/F-workflow-false-pass-risk-from-unchecked-matrix-summary.md`
- `knowledge/decisions/DR-workflow-validator-baseline.md`
- `knowledge/evaluator-rules/ER-matrix-summary-counts-must-match.md`
- `knowledge/evaluator-rules/ER-accepted-findings-require-evidence-path.md`
- `knowledge/evaluator-rules/ER-run-layout-canonical-model-outputs.md`
- `knowledge/evaluator-rules/ER-model-role-contract-requires-output.md`

## Weak Gates Status

| Gate | Before | After | Status |
|------|--------|-------|--------|
| W006: pre/post status | Manual-only | Bounded by validate_run.py | BOUNDED |
| W012: matrix summary counts | Manual-only | validate_matrix_consistency.py | ENFORCED |
| Evidence gap | Manual-only | validate_synthesis_evidence.py | ENFORCED |
| Naming drift | Inconsistent | Canonical model_outputs/ + legacy compat | BOUNDED |
| validate_run.py drift | Hardcoded | Flexible model output / role contract | ENFORCED |

## Tag

```
git tag workflow-quality-gate-audit-phase-1
```

## Conclusion

Phase 3 achieved its goal: methodology docs upgraded to methodology validators. The 5 weak gates identified in 001 are now either enforced by scripts or bounded by explicit rules. False PASS risk significantly reduced.
