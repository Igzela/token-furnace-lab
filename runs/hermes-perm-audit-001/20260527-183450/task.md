# hermes-perm-audit-001: Hermes Gateway Lab Permission Boundary Audit

## Objective

Audit hermes-gateway-lab's agent permission boundaries and propose 3 actionable improvements.

## Scope

- Read-only on target repo
- Identify all permission control points
- Check permission escalation risks
- Evaluate permission isolation effectiveness
- Propose 3 implementable improvements

## Models

| Role | Provider | Focus |
|------|----------|-------|
| GPT Architect | OpenAI | Architecture audit, permission model, risk boundaries |
| Claude Code Repo Reader | Anthropic | Local repo reading, inventory, grounded suggestions |
| Codex Risk Reviewer | OpenAI | Code-level risk: scripts, writes, injection, secrets |

## Verification Criteria

- [ ] At least 5 permission control points identified
- [ ] At least 1 potential risk discovered
- [ ] Suggestions are directly implementable
- [ ] Three model conclusions cross-verifiable
- [ ] Target repo unmodified

## Expected Outputs

- [ ] 3 independent audit reports (model-outputs/)
- [ ] 1 cross-audit synthesis (synthesis/)
- [ ] 1 decision record
- [ ] 1 wiki note for knowledge distillation
- [ ] 1 evaluator rule
- [ ] 1 next experiment proposal
