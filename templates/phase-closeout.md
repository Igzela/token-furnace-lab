<!--
Phase closeout rules:
1. Do not hide unresolved gaps. Use PASS_WITH_NOTES when backlog remains.
2. A phase can be COMPLETE even if some target gaps are deferred.
3. Always separate target_control_verdict from platform_validation_verdict.
4. Include tag/commit information so the phase is reproducible.
5. Record whether the next phase is recommended or deferred.
-->

# <phase-id> Closeout

## Metadata

- phase_id:
- phase_name:
- experiment_range: <first-id> through <last-id>
- target_repo:
- target_branch:
- created:
- operator:

## Phase Verdict

```yaml
phase_verdict: COMPLETE | INCOMPLETE
target_control_verdict: PASS | PASS_WITH_NOTES | FAIL
platform_validation_verdict: PASS | PASS_WITH_NOTES | FAIL
overall_reason: ""
```

## Executive Summary

One paragraph. State what the phase proved, what it did not prove, and what should happen next.

## Timeline

| Time | Experiment | Goal | Verdict |
|------|-----------|------|---------|
| T+0 | <id> | <goal> | <verdict> |

## Key Changes

### <experiment-id>: <title>

- <change description>

## Matrices Produced

| Matrix | Purpose | Final Verdict | Path |
|--------|---------|---------------|------|
| deny-path matrix | | | knowledge/matrices/... |
| gate-conformance matrix | | | knowledge/matrices/... |
| queue-ingress matrix | | | knowledge/matrices/... |

## Regression / Test Assets

| Asset | Command | Coverage | Status |
|-------|---------|----------|--------|
| gate conformance regression | | | |
| queue ingress audit | | | |
| smoke tests | | | |

## Knowledge Assets Produced

| Type | Count | Path | Notes |
|------|-------|------|-------|
| wiki | | knowledge/wiki/ | |
| decisions | | knowledge/decisions/ | |
| failures | | knowledge/failures/ | |
| evaluator rules | | knowledge/evaluator-rules/ | |
| reusable prompts | | knowledge/reusable-prompts/ | |

## Target System Final State

### Improved Controls

...

### Remaining Known Gaps

| Gap | Severity | Reason Deferred | Recommended Phase |
|-----|----------|-----------------|-------------------|
| | | | |

### Safety Boundaries Preserved

| Boundary | Status | Evidence |
|----------|--------|----------|
| no live execution | pass/fail | |
| no real secrets | pass/fail | |
| no approval authority expansion | pass/fail | |
| no destructive git history rewrite | pass/fail | |

## Platform Methodology Lessons

### Lesson 1: <title>

- observed_in:
- reusable_rule:
- template_or_rule_updated:

## Token Furnace Platform Validation

State whether the platform methodology was validated.

```yaml
validated_capabilities:
  - multi_model_cross_audit
  - dual_verdict_system
  - path_aware_matrices
  - healthy_failure
  - regression_after_fix
  - knowledge_deposition
```

## Release / Tag

```bash
git tag <phase-tag>
git push origin <phase-tag>
```

- tag:
- commit:
- pushed: yes/no

## Next Phase Decision

```yaml
next_phase:
  decision: stop | continue | defer
  reason:
  recommended_focus:
  backlog:
    - id:
      description:
      severity:
```

## Final Notes

Short final assessment.
