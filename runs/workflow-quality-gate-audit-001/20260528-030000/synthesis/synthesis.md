# Synthesis: workflow-quality-gate-audit-001

## Metadata

- Experiment: workflow-quality-gate-audit-001
- Type: audit
- Status: COMPLETE
- Created: 2026-05-28

## Verdict

```yaml
experiment_verdict: COMPLETE
target_control_verdict: PASS_WITH_NOTES
platform_validation_verdict: PASS_WITH_NOTES
```

## Executive Summary

workflow-quality-gate-audit-001 completed successfully. The audit proves Token Furnace Lab v1 workflow is structurally sound (26/30 strong gates) but not yet mechanically enforced. Five weak gates create risks for false PASS, evidence gaps, and naming inconsistency. The methodology is valid but needs automated enforcement.

## Key Conclusion

**Token Furnace Lab v1 workflow is structurally sound, but not yet mechanically enforced.**

## Scope Boundary

### In Scope
- Template structure and content
- Prior phase artifact compliance
- Gate coverage against W001-W030
- Naming consistency
- Validation script coverage

### Out of Scope
- Hermes gate_policy re-audit
- MCP bridge allowlist re-audit
- Business code modification
- Runtime feature introduction

## Evidence Inputs

| Source | Path | Status |
|--------|------|--------|
| Claude Code output | model_outputs/claude-code-output.md | Present |
| GPT reviewer output | model_outputs/gpt-reviewer-output.md | Present |
| Matrix | knowledge/matrices/workflow-quality-gate-matrix.yaml | Present |
| Templates | templates/*.yaml, templates/*.md | Sampled |
| Prior phases | runs/hermes-perm-audit-*, runs/mcp-bridge-boundary-audit-* | Sampled |

## Gate Assessment

### Strong Gates (26/30)

**Experiment Definition (5/5)**
- W001: explicit type — PASS
- W002: target/platform separated — PASS
- W003: allowed/forbidden declared — PASS
- W004: non-goals declared — PASS
- W005: healthy failure declared — PASS

**Evidence/State (4/5)**
- W007: evidence path per finding — PASS
- W008: evidence type declared — PASS
- W009: model inference alone can't PASS — PASS
- W010: secrets redacted — PASS

**Matrix/Verdict (5/6)**
- W011: matrix exists — PASS
- W013: P0 fail requires follow-up — PASS
- W014: path-aware matrix — PASS
- W015: verdicts separated — PASS
- W016: triple verdict for closeout — PASS

**Agent Handoff (4/5)**
- W017: Claude Code bounded — PASS
- W018: GPT bounded — PASS
- W020: uncertainty preserved — PASS
- W021: disagreement resolved by evidence — PASS

**Fix/Regression (5/5)**
- W022: narrow write scope — PASS
- W023: no unrelated refactor — PASS
- W024: regression follow-up — PASS
- W025: regression tests run — PASS
- W026: no behavior change in refactor — PASS

**Closeout/Knowledge (4/5)**
- W027: synthesis exists — PASS
- W028: knowledge deposited — PASS
- W029: known gaps recorded — PASS
- W030: tag/commit baseline — PASS

### Weak Gates (5/30)

1. **W006: pre/post status** — WARN: Not explicitly recorded in runs
2. **W012: matrix summary counts** — WARN: No automated checker
3. **W019: Codex role** — WARN: Not consistently used
4. **Naming inconsistency** — model-outputs/ vs model_outputs/
5. **validate_run.py drift** — Hardcoded filenames don't match actual

## Workflow Risks

1. **False PASS risk**: Matrix summary counts unchecked
2. **Evidence gap risk**: Accepted findings without evidence_path
3. **Naming inconsistency risk**: Different scripts expect different dirs

## Strong Examples

1. **W009**: Matrix template explicitly prohibits PASS on model_inference alone
2. **W015**: Dual verdict system separates experiment success from target success
3. **W010**: validate_run.py scans for 7 secret patterns
4. **W013**: Matrix template enforces follow_up for P0 fails
5. **W028**: Knowledge distillation produces wiki, decisions, evaluator-rules, matrices

## Weak Examples

1. **W012**: Consistency checks defined in template but not enforced by script
2. **W006**: Git status snapshots exist but not as structured pre/post fields
3. **Naming**: new_run.py uses model-outputs/, distill.sh expects model_outputs/

## Knowledge Assets Created

- `knowledge/wiki/token-furnace-workflow-quality-gates.md`
- `knowledge/failures/F-workflow-false-pass-risk-from-unchecked-matrix-summary.md`
- `knowledge/evaluator-rules/ER-matrix-summary-counts-must-match.md`
- `knowledge/evaluator-rules/ER-accepted-findings-require-evidence-path.md`

## Next Experiment

workflow-quality-gate-audit-002: Workflow Gate Validator Implementation

Priority fixes:
1. Unified naming (canonical model_outputs/)
2. Update validate_run.py
3. Create validate_matrix_consistency.py
4. Create validate_synthesis_evidence.py
