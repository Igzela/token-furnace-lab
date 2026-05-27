# <experiment-id> Synthesis

## Metadata

- experiment_id:
- experiment_type:
- target_repo:
- target_branch:
- target_commit:
- run_id:
- created:
- depends_on:

## Verdict

```yaml
experiment_verdict: COMPLETE | INCOMPLETE
target_control_verdict: PASS | PASS_WITH_NOTES | FAIL
overall_reason: ""
```

## Executive Summary

One paragraph. State what the experiment proved, what it did not prove, and what should happen next.

## Scope Boundary

### In Scope

...

### Out of Scope

...

### Forbidden Operations Confirmation

- live execution:
- destructive operations:
- real secrets:
- approval authority changes:

## Evidence Inputs

| Source | Path | Role | Status |
|--------|------|------|--------|
| Claude Code output | model-outputs/claude-code.md | repo/evidence collector | present |
| GPT output | model-outputs/gpt.md | architecture reviewer | present |
| Codex output | model-outputs/codex.md | code risk reviewer | present |
| Matrix | knowledge/matrices/<matrix>.yaml | structured verdict source | present |

## Model Output Comparison

| Finding | Claude Code | GPT | Codex | Synthesis Decision |
|---------|-------------|-----|-------|-------------------|
| <finding> | agree/disagree/unknown | agree/disagree/unknown | agree/disagree/unknown | accepted/rejected/revised |

## Accepted Findings

### F-001: <finding title>

- status: accepted
- severity:
- evidence_type:
- evidence_path:
- affected_component:
- reasoning:
- required_follow_up:

## Rejected Findings

### R-001: <finding title>

- status: rejected
- reason:
- missing_evidence:

## Revised Findings

### RF-001: <finding title>

- original_claim:
- revised_claim:
- why_revised:
- evidence_path:
- impact:

## Matrix Results

| Matrix | Pass | Warn/Partial | Fail | Notes |
|--------|------|--------------|------|-------|
| <matrix-name> | | | | |

## Path / Component Conformance

Use this section only when the experiment compares multiple execution paths.

| Case | Path A | Path B | Conformance | Evidence |
|------|--------|--------|-------------|----------|
| D001 | | | | |

## Cost Estimate

| Model | Role | Estimated Tokens | Actual Tokens |
|-------|------|------------------|---------------|
| Claude Code | | | |
| GPT | | | |
| Codex | | | |
| **Total** | | | |

## Decision Record

### DR-XXXX: <decision title>

- **Status**: Accepted/Rejected
- **Context**: ...
- **Decision**: ...
- **Rationale**: ...
- **Consequences**: ...

## Next Experiment

- recommended_if_pass:
- recommended_if_fail:
- rationale:
