---
id: ER-run-layout-canonical-model-outputs
name: "Canonical Run Layout Uses model_outputs/"
severity: Medium
source_experiment: workflow-quality-gate-audit-002
created: 2026-05-28
status: enforced
---

## Rule

Canonical run layout uses `model_outputs/` (underscore). Legacy `model-outputs/` (hyphen) is supported with warnings.

## Test Method

validate_run.py checks:
1. If model_outputs/ exists → canonical
2. If model-outputs/ exists → legacy (warning)
3. If neither → missing (warning)

## Source

workflow-quality-gate-audit-001: naming inconsistency identified

## Current Status

Enforced by validate_run.py with legacy compatibility.

## Cross-References

- Script: scripts/validate_run.py
- Matrix: workflow-quality-gate-matrix.yaml (naming drift)
