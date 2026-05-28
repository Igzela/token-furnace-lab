# Token Furnace Agent Task

Role: implementer
Subagent type: Plan

## Objective

Review the Phase E-001 fault recovery model for the 22uF DC-link sensorless FOC water pump drive and produce corrected implementation guidance.


## Subproblem

Review runtime fault recovery model

## Required output file

/home/igzela/Projects/token-furnace-lab/runs/orchestration/20260528-092721/artifacts/e001_fault_recovery_review.md

## Required sections

- Score
- Verdict
- Findings
- Corrections
- Final Recommendation

## Constraints

Allowed paths:
- runs/orchestration/
- runs/small-dc-link-foc-phase-e-001/
- knowledge/wiki/
- docs/design/

Forbidden paths:
- .env
- secrets/
- credentials/

## Task prompt

Review the Phase E-001 runtime fault recovery model for a sensorless FOC
water pump drive (22uF DC-link, TMS320F28035).

The model is at: runs/small-dc-link-foc-phase-e-001/20260528-130000/model_outputs/fault_recovery_model.md

Produce a structured artifact with Score, Verdict, Findings, Corrections, and Final Recommendation.

Focus on:
1. Are all critical fault paths covered?
2. Are timing constants reasonable?
3. Is the restart logic correct?
4. Are there safety gaps?

The artifact must include evidence-backed claims.


## Output rules

Write the artifact to the exact required output file.
Include evidence paths for claims where possible.
Do not modify files outside allowed paths.
