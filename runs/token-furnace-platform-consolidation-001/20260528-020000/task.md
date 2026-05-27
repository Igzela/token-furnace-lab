# Task: token-furnace-platform-consolidation-001 — Cross-Phase Platform Consolidation

## Objective

Consolidate Hermes Phase 1, MCP Bridge Phase 1, and methodology-v1 into a platform-level index and maturity assessment.

## Completed Baselines

1. **hermes-perm-audit-phase-1**: Deep control-plane audit + fix + regression + hardening (001-007 + closeout)
   - Verdict: PASS_WITH_NOTES
   - Tag: hermes-perm-audit-phase-1

2. **mcp-bridge-boundary-audit-phase-1**: Cross-project boundary audit + runtime verification (001-002)
   - Verdict: PASS
   - Tag: mcp-bridge-boundary-audit-phase-1

3. **token-furnace-methodology-v1**: Reusable experiment methodology baseline
   - Verdict: Platform validated
   - Tag: token-furnace-methodology-v1

## Consolidation Questions

1. What capabilities has Token Furnace Lab validated?
2. What risk types do Hermes and MCP Bridge cases cover?
3. Which templates/matrices/verdict mechanisms are stable?
4. What capabilities remain unvalidated?
5. How should Phase 3 select its target?

## Required Outputs

1. `docs/runs/token-furnace-platform-v1-closeout.md`
2. `docs/methodology/token-furnace-cross-phase-lessons.md`
3. `knowledge/wiki/token-furnace-platform-validation.md`
4. `knowledge/matrices/platform-validation-matrix.yaml`

## Constraints

- Read-only consolidation
- No new experiments
- No code changes
- Evidence from completed experiments only
