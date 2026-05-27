# Token Furnace Lab — Experiment Lifecycle

## Purpose

This document defines the standard lifecycle for Token Furnace Lab experiments. It ensures high token consumption produces real, reusable engineering assets.

## Lifecycle Phases

```
audit → verify → fix → regress → refactor → ingress audit → harden → closeout
```

### 1. Audit (Discovery)

**Goal**: Identify issues, divergences, risks, or attack surfaces.

**Outputs**:
- Risk matrix
- Issue inventory
- Attack surface map

**Example**: hermes-perm-audit-001 discovered 6 divergent deny cases between marker and worker paths.

### 2. Verify (Confirmation)

**Goal**: Confirm audit findings with targeted tests.

**Outputs**:
- Verified issue list
- Test evidence
- Severity classification

**Example**: hermes-perm-audit-002 confirmed all 6 divergences with path-aware deny matrix.

### 3. Fix (Correction)

**Goal**: Implement corrections for verified issues.

**Outputs**:
- Code changes
- Fix documentation
- Before/after comparison

**Example**: hermes-perm-audit-003 fixed all 6 divergences in worker gate logic.

### 4. Regress (Lock)

**Goal**: Lock corrected behavior with regression suite.

**Outputs**:
- Regression test suite
- Pass/fail matrix
- Automated verification command

**Example**: hermes-perm-audit-004 created 24-test regression suite catching future gate divergence.

### 5. Refactor (Single Source of Truth)

**Goal**: Extract shared logic to eliminate duplication.

**Outputs**:
- Shared module/policy
- Updated imports
- Reduced code duplication

**Example**: hermes-perm-audit-005 extracted gate_policy.py as single source of truth.

### 6. Ingress Audit (Bypass Check)

**Goal**: Verify no bypass paths exist around security controls.

**Outputs**:
- Ingress path matrix
- Bypass risk assessment
- Defense-in-depth verification

**Example**: hermes-perm-audit-006 verified no critical queue bypass paths.

### 7. Harden (Defense-in-Depth)

**Goal**: Add defense-in-depth measures.

**Outputs**:
- Sink sanitization
- Graceful degradation
- Recovery mechanisms

**Example**: hermes-perm-audit-007 added audit sink sanitization and queue quarantine.

### 8. Closeout (Package)

**Goal**: Package results, tag repo, document methodology outcomes.

**Outputs**:
- Closeout document
- Git tag
- Methodology insights
- Next-phase recommendations

**Example**: hermes-perm-audit-008 created closeout doc, tagged repo, documented methodology.

## Asset Types

Every experiment must produce:

| Asset | Purpose |
|-------|---------|
| Experiment record | Reproducible history |
| Model outputs | Multi-model audit trail |
| Matrices | Conformance/risk verification |
| Regression suite | Automated behavior lock |
| Shared policy | Single source of truth |
| Knowledge base | Wiki, decisions, failures |
| Closeout doc | Phase conclusion |

## Multi-Model Cross-Audit

| Model | Role |
|-------|------|
| GPT | Architect, reviewer |
| Claude Code | Implementer, repo reader |
| Codex | Risk reviewer, verifier |

## Dual Verdicts

Each experiment has two verdicts:

1. **experiment_verdict**: COMPLETE / INCOMPLETE
   - Did the experiment achieve its stated objective?

2. **target_control_verdict**: PASS / PASS_WITH_NOTES / FAIL
   - Is the target system's security posture acceptable?

## Directory Structure

```
token-furnace-lab/
├── experiments/
│   └── agent-workflow/
│       └── <experiment-id>/
│           └── experiment.yaml
├── runs/
│   └── <experiment-id>/
│       └── <timestamp>/
│           ├── task.md
│           ├── model_outputs/
│           ├── synthesis/
│           └── traces/
├── knowledge/
│   ├── matrices/
│   ├── decisions/
│   ├── wiki/
│   └── evaluator-rules/
└── docs/
    └── methodology/
        └── token-furnace-experiment-lifecycle.md
```

## Example: hermes-perm-audit Phase 1

| Exp | Phase | Verdict |
|-----|-------|---------|
| 001 | Audit | COMPLETE |
| 002 | Verify | COMPLETE |
| 003 | Fix | PASS_WITH_NOTES |
| 004 | Regress | PASS_WITH_NOTES |
| 005 | Refactor | PASS |
| 006 | Ingress Audit | PASS_WITH_NOTES |
| 007 | Harden | PASS |
| 008 | Closeout | COMPLETE |

**Assets produced**:
- deny-path matrix (25 cases)
- gate conformance matrix (6 tests)
- queue ingress matrix (8 tests)
- 24-test regression suite
- shared gate_policy.py
- queue hardening (audit sink + quarantine)
- closeout documentation

**Token justification**: ~200k tokens converted to reusable security infrastructure.

## Phase 2 Selection Criteria

When choosing next target:

1. **Different domain**: Not another permission audit
2. **Reusable methodology**: Can apply lifecycle pattern
3. **Measurable outcomes**: Clear success criteria
4. **Token justification**: High consumption must produce real assets

## Key Principles

1. **High token consumption → real assets**: Every experiment must produce reusable engineering artifacts
2. **Multi-model cross-audit**: At least 2 models execute, third reviews
3. **Defense-in-depth**: Security sinks don't trust callers
4. **Single source of truth**: Extract shared logic to eliminate divergence
5. **Graceful degradation**: Corrupt inputs quarantined, not crashed
6. **Lock behavior**: Regression suites catch future divergence

## References

- hermes-perm-audit-phase-1 (tag in hermes-gateway-lab)
- project_hermes_perm_audit_series.md (memory)
- methodology_experiment_lifecycle.md (memory)
