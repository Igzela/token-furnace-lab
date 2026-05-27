# Token Furnace Lab — Platform Validation

## Definition

Token Furnace Lab is an AI agent experiment platform that produces high token consumption with inspectable artifacts. The platform uses multi-model cross-audit (GPT + Claude Code) and structured experiment lifecycle to produce reusable security/conformance evidence.

## Validation Status

**Platform Maturity: L3-VALIDATED**

The platform has been successfully applied to two different codebases with consistent methodology reuse, template stability, and verdict mechanisms.

## Validated Baselines

| Baseline | Target | Verdict |
|----------|--------|---------|
| hermes-perm-audit-phase-1 | hermes-gateway-lab | PASS_WITH_NOTES |
| mcp-bridge-boundary-audit-phase-1 | hermes-gateway-lab (bridge) | PASS |
| token-furnace-methodology-v1 | Platform methodology | Platform validated |

## Validated Capabilities

1. **Multi-Model Cross-Audit**: GPT (architect) + Claude Code (implementer)
2. **8-Phase Experiment Lifecycle**: audit → verify → fix → regress → refactor → ingress audit → harden → closeout
3. **Dual Verdict System**: experiment_verdict + target_control_verdict
4. **Matrix-Based Evidence Collection**: Conformance matrices with status tracking
5. **Knowledge Distillation**: Wiki, decisions, evaluator-rules, matrices
6. **Cross-Project Generalization**: Same methodology, different codebase

## Risk Types Covered

- Permission escalation
- Path traversal
- Input validation
- Hidden tool exposure
- Subprocess lifecycle
- Session isolation
- Audit leakage
- Argument injection

## Unvalidated Capabilities

- Public internet exposure
- Multi-user auth model
- Long-term stability
- Real production deployment
- Malicious local process protection

## Reusable Patterns

1. **Experiment template**: `templates/experiment.yaml`
2. **Synthesis template**: `templates/synthesis.md`
3. **Matrix template**: `templates/matrix.yaml`
4. **Closeout template**: `templates/phase-closeout.md`
5. **8-phase lifecycle**: Proven in Hermes Phase 1
6. **Dual verdicts**: Consistently applied across phases

## When to Use

Use Token Furnace Lab when:
- You need structured security/conformance evidence
- Multiple models should review the same target
- Knowledge assets should be reusable
- Methodology should be generalizable

Do NOT use when:
- Quick one-off audit is sufficient
- Single model execution is adequate
- No reusable knowledge is needed
