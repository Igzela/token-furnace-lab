# hermes-perm-audit-002: Deny-Path Implementation Audit

## Objective

Verify that every documented live execution gate in hermes-gateway-lab has a corresponding runtime deny-path test. Establish the deny-path test matrix as a verifiable asset.

Do NOT fix the worker gate function. Do NOT modify source code. This is a read-only + test-writing experiment.

## Context

hermes-perm-audit-001 found that `check_worker_gates` in `local_execution_worker.py` diverges from `local_marker_executor.check_gates`. 6+ required gates are missing from the worker path.

The deny-path matrix (`knowledge/matrices/deny-path-matrix.yaml`) defines 25 deny cases across 6 groups. Currently 7/25 have partial coverage, 18/25 have no coverage.

## Models

1. **GPT**: Design deny-path test specifications for each case
2. **Claude Code**: Map documented gates to actual code locations, identify gaps
3. **Codex**: Verify that proposed tests would actually catch the deny condition

## Deliverables

1. `model-outputs/gpt-test-designer.md`: Test specifications for all 25 cases
2. `model-outputs/claude-code-gate-mapper.md`: Gate-to-code mapping with gap analysis
3. `model-outputs/codex-deny-verifier.md`: Verification that tests would catch deny conditions
4. `synthesis/deny-path-test-plan.md`: Unified test plan with priorities
5. Updated `knowledge/matrices/deny-path-matrix.yaml` with evidence entries

## Rules

- Read-only on target repo source code
- Can write test specifications (not executable tests yet)
- Every claim must cite a specific file and line number
- Mark findings as grounded/inferred/unknown
