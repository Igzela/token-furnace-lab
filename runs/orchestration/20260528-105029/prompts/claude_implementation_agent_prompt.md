# Token Furnace Agent Task

Role: implementer
Subagent type: Plan

## Objective

Run a real multi-model cross-audit on the Phase E-001 fault recovery model. Claude Code as implementer, GPT as architecture reviewer. Validate all outputs against schemas. Verify gate handles real model output drift.


## Subproblem

Claude Code: Review fault recovery model

## Required output file

/home/igzela/Projects/token-furnace-lab/runs/orchestration/20260528-105029/artifacts/claude_review.md

## Required sections

- Score
- Verdict
- Confidence
- Findings
- Final Recommendation

## Constraints

Allowed paths:
- runs/orchestration-004/
- runs/small-dc-link-foc-phase-e-001/
- knowledge/wiki/

Forbidden paths:
- .env
- secrets/
- credentials/

## Task prompt

You are reviewing the Phase E-001 runtime fault recovery model for a
sensorless FOC water pump drive (22uF DC-link, TMS320F28035).

Read the model at: runs/small-dc-link-foc-phase-e-001/20260528-130000/model_outputs/fault_recovery_model.md

Produce a structured review with:
- Score (0-100)
- Verdict (PASS, PASS_WITH_NOTES, or FAIL)
- Confidence (HIGH, MEDIUM, LOW)
- Findings (each with: id, severity, blocking, evidence_path, claim, correction)
- Final Recommendation

Focus on:
1. Are all critical fault paths covered?
2. Are timing constants physically reasonable?
3. Is the restart logic correct?
4. Are there safety gaps?

Include evidence paths for all claims.


## Output rules

Write the artifact to the exact required output file.
Include evidence paths for claims where possible.
Do not modify files outside allowed paths.
