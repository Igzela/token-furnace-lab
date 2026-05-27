# Task: workflow-quality-gate-audit-001 — Workflow Quality-Gate Audit

## Objective

Audit and validate the Claude/Codex/GPT multi-agent workflow used by Token Furnace Lab. Verify that methodology templates, quality gates, and verdict mechanisms actually constrain workflow execution.

## Target

- **Primary repo**: Igzela/token-furnace-lab
- **Secondary target**: Igzela/hermes-gateway-lab (sample prior phase artifacts)

## Core Question

Can the Claude/Codex/GPT workflow reliably convert model outputs into evidence-backed, matrix-tracked, regression-protected conclusions without false PASS, scope drift, or unverified claims?

## Audit Scope

### Workflows to Audit
1. Experiment creation workflow
2. Evidence collection workflow
3. Multi-model handoff workflow
4. Matrix update workflow
5. Verdict workflow
6. Fix workflow
7. Regression workflow
8. Closeout workflow

### Quality Gates to Audit (W001-W030)
- Group A: Experiment Definition Gates (W001-W005)
- Group B: Evidence and File-State Gates (W006-W010)
- Group C: Matrix and Verdict Gates (W011-W016)
- Group D: Multi-Agent Handoff Gates (W017-W021)
- Group E: Fix and Regression Gates (W022-W026)
- Group F: Closeout and Knowledge Deposition Gates (W027-W030)

## Claude Code Tasks

1. Read all templates (experiment.yaml, synthesis.md, matrix.yaml, phase-closeout.md)
2. Read methodology docs (token-furnace-experiment-lifecycle.md, cross-phase-lessons.md)
3. Sample prior phase artifacts (hermes-perm-audit, mcp-bridge-boundary-audit)
4. Output workflow asset inventory
5. Output experiment lifecycle compliance map
6. Output gate coverage against W001-W030
7. Identify strong gates with examples
8. Identify weak or manual-only gates
9. Confirm no-write for token-furnace-lab

## Safety Constraints

- Read-only audit of workflow
- No code changes to templates (audit only)
- No modification to target repos
- No live execution
