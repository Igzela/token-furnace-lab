---
id: ER-matrix-summary-counts-must-match
name: "Matrix Summary Counts Must Match Actual Cases"
severity: Critical
source_experiment: workflow-quality-gate-audit-001
created: 2026-05-28
status: manual-only
---

## Rule

Matrix summary counts must exactly match actual case lists. No PASS verdict can be declared if summary.total_cases != len(cases) or summary.by_status counts don't match actual case statuses.

## Test Method

Automated validation:
1. Count all cases in matrix groups
2. Compare to summary.total_cases
3. Count cases by status
4. Compare to summary.by_status
5. Verify all PASS cases have evidence_path and evidence_type
6. Verify no PASS case relies only on model_inference

## Source

workflow-quality-gate-audit-001: W012 gate identified as weak (manual-only)

## Current Status

Manual-only. No automated validator exists.

## Cross-References

- Matrix: workflow-quality-gate-matrix.yaml (W012)
- Failure: F-workflow-false-pass-risk-from-unchecked-matrix-summary.md
- Template: templates/matrix.yaml (consistency_checks)
