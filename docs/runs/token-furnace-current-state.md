# Token Furnace Lab — Current State Index

## Metadata

- Generated: 2026-05-28
- Maturity: L3-VALIDATED
- Total Phases Completed: 3

## Completed Phases

| Phase | Target | Tag | Verdict | Commit |
|-------|--------|-----|---------|--------|
| Phase 1 | Hermes permission audit (001-008) | hermes-perm-audit-phase-1 | COMPLETE/PASS | 3e1b004 |
| Phase 2 | MCP bridge tool-boundary audit | mcp-bridge-boundary-audit-phase-1 | COMPLETE/PASS/PASS | a9615de |
| Phase 3 | Workflow quality-gate audit | workflow-quality-gate-audit-phase-1 | COMPLETE/PASS_WITH_NOTES/PASS | 6a7df2d |

## Platform Consolidation

| Milestone | Tag | Verdict | Commit |
|-----------|-----|---------|--------|
| Platform v1 | token-furnace-platform-v1 | L3-VALIDATED | 9a0c4b8 |
| Methodology v1 | token-furnace-methodology-v1 | ACCEPTED | 6100a6c |

## Current Maturity

**L3-VALIDATED**: Multi-phase experiment lifecycle proven across heterogeneous targets.

Capabilities validated:
- Multi-model cross-audit (GPT + Claude Code + Codex)
- Structured knowledge distillation (decisions, evaluator-rules, failures, wiki, matrices)
- Automated workflow validators (3 scripts)
- Canonical run layout with legacy compatibility
- 30-case workflow quality-gate matrix
- 16-case MCP bridge boundary matrix
- 8-case hermes permission matrix

## Reusable Templates

- `templates/experiment.yaml` — Experiment definition
- `templates/synthesis.md` — Synthesis report
- `templates/matrix.yaml` — Conformance/risk matrix
- `templates/phase-closeout.md` — Phase closeout

## Runnable Validators

```bash
# Run layout validation
python3 scripts/validate_run.py runs/<experiment>/<timestamp>/

# Matrix consistency
python3 scripts/validate_matrix_consistency.py knowledge/matrices/<matrix>.yaml

# Synthesis evidence
python3 scripts/validate_synthesis_evidence.py runs/<experiment>/<timestamp>/
```

## Why PASS_WITH_NOTES (Not Strict PASS)

1. **Legacy layout still supported**: `model-outputs/` (hyphen) works with warnings, not errors
2. **Optional files not enforced**: `run.yaml`, `status.md` generate warnings, not failures
3. **Codex role is contract-based**: Not globally mandatory, only checked if declared
4. **No CI/CD integration**: Validators run locally, not in pipeline

## Phase 4 Candidates

1. **PDF-to-algorithm extraction benchmark** — Validates generalization from agent security audit to research extraction
2. **OpenClaw runtime permission audit** — Another agent security target
3. **Public exposure / tunnel security audit** — Network boundary testing

**Recommended**: PDF-to-algorithm extraction benchmark (GPT recommendation)

## Tags

```bash
git tag hermes-perm-audit-phase-1
git tag mcp-bridge-boundary-audit-phase-1
git tag token-furnace-platform-v1
git tag token-furnace-methodology-v1
git tag workflow-quality-gate-audit-phase-1
```
