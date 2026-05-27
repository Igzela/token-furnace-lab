---
id: ER-model-role-contract-requires-output
name: "Declared Model Role Must Have Corresponding Output"
severity: Medium
source_experiment: workflow-quality-gate-audit-002
created: 2026-05-28
status: enforced
---

## Rule

If experiment.yaml or task.md declares a model role (e.g., Codex), the corresponding output file must exist in model_outputs/.

## Test Method

validate_run.py checks:
1. Scan experiment.yaml and task.md for model role declarations
2. If Codex role declared → check for codex output file
3. If missing → warning

## Source

workflow-quality-gate-audit-001: W019 (Codex not consistently used)

## Current Status

Enforced by validate_run.py. Codex is not globally mandatory, but if declared, output must exist.

## Cross-References

- Script: scripts/validate_run.py
- Matrix: workflow-quality-gate-matrix.yaml (W019)
