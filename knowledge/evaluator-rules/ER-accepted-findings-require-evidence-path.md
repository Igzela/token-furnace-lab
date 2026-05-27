---
id: ER-accepted-findings-require-evidence-path
name: "Accepted Findings Must Have Evidence Path"
severity: Critical
source_experiment: workflow-quality-gate-audit-001
created: 2026-05-28
status: manual-only
---

## Rule

Every accepted finding in synthesis must include evidence_path and evidence_type. No finding can be accepted based solely on model inference or model agreement.

## Test Method

Automated validation:
1. Parse synthesis.md for accepted findings
2. Verify each finding has evidence_path
3. Verify each finding has evidence_type
4. Verify evidence_type is not only model_inference
5. Verify target_control_verdict is not inferred solely from model agreement

## Source

workflow-quality-gate-audit-001: Evidence gap risk identified

## Current Status

Manual-only. No automated validator exists.

## Cross-References

- Matrix: workflow-quality-gate-matrix.yaml (W007, W009)
- Template: templates/synthesis.md (evidence inputs)
- Template: templates/experiment.yaml (evidence_requirements)
