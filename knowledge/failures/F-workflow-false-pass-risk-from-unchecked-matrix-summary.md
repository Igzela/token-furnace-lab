---
id: F-workflow-false-pass-risk
name: "False PASS Risk from Unchecked Matrix Summary Counts"
severity: High
source_experiment: workflow-quality-gate-audit-001
created: 2026-05-28
---

## Failure

Matrix template defines 7 consistency checks (including summary.total_cases == actual case count), but no automated script enforces these checks. If a matrix summary says "16 PASS" but only 14 cases actually have PASS status, the inconsistency goes undetected.

## Root Cause

Consistency checks are defined in `templates/matrix.yaml` as documentation, not as executable validation. No `validate_matrix_consistency.py` script exists.

## Impact

- False PASS: Could declare target_control_verdict: PASS with mismatched counts
- Audit trail corruption: Summary doesn't match actual evidence
- Trust erosion: Matrix-based conclusions become unreliable

## Prevention Rule

Every matrix must pass automated consistency validation before verdict can be declared.

## Evaluator Check

`ER-matrix-summary-counts-must-match.md`

## Resolution

Create `scripts/validate_matrix_consistency.py` in workflow-quality-gate-audit-002.
