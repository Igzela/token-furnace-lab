# Token Furnace: When Does Token Consumption Become Productive?

## Core Question

大量 AI agent token 在什么条件下变成真实生产力，而不是噪声？

## Observed Patterns (from 13 FOC experiments)

### 1. Multi-Model Cross-Audit Effectiveness

GPT catches real Claude errors in these categories:

| Error Type | Example | Catch Rate | Value |
|-----------|---------|------------|-------|
| Formula/numerical | ψ_f=0.15→0.08 | High | High — prevents hardware damage |
| Model structure | Observer tracking commanded not actual angle | Medium | High — invalidates simulation |
| Constraint violation | 56KB trace > 12KB RAM | Medium | High — code won't compile |
| Conclusion overreach | "22µF needs three-phase" → "can't conclude that" | Low-Medium | Medium — prevents wrong direction |
| Style/naming | Variable naming, comments | High | Low — cosmetic only |

**Rule**: Cross-audit is most valuable for formula/parameter/constraint errors. Less valuable for architectural judgment.

### 2. Token ROI by Experiment Round

| Round | Token Spend | New Knowledge | Pattern |
|-------|------------|---------------|---------|
| 1→2 (B-001→B-002) | High | High | Correction of fundamental parameters |
| 2→3 (B-002→B-003) | Medium | Medium | Engineering refinement |
| 3→4 (B-003→B-004) | Medium | Low | Implementation spec, no new physics |
| 1→2 (C-001→C-002) | High | High | Model correction, feasibility closure |
| 2→3 (C-002→C-003) | Low | Low | Margin testing, confirming existing conclusions |

**Rule**: First 2-3 iterations per sub-problem yield highest returns. After that, diminishing returns as work shifts to engineering refinement.

### 3. What Counts as "Real Productive Output"

Not conversation itself, but checkable artifacts:

- Corrected parameters (ψ_f=0.08 Wb)
- Validated models (189/189 configs pass)
- Implementable code specs (startup_sm.h/c)
- Quantified margins (22µF+90% APD, worst-case 100% pass)
- Decision records with evidence paths

**Rule**: Productivity = (artifacts produced) × (artifact quality). Conversation volume is noise unless it produces artifacts.

### 4. Conditions That Enable Productivity

| Condition | Why It Works |
|-----------|-------------|
| Clear success criteria | GPT can verify pass/fail, not just "looks good" |
| Quantitative sweeps | 189 configs > "seems reasonable" |
| Fixed-point constraints | Hardware limits force concrete decisions |
| Cross-model disagreement | Disagreement → investigation → knowledge |
| Autonomous operation | No human bottleneck, but requires structured output |

### 5. Conditions That Kill Productivity

| Condition | Why It Fails |
|-----------|-------------|
| No verification loop | Claude writes, nobody checks → errors propagate |
| Open-ended exploration | "What could we do about X?" burns tokens with no artifact |
| Style over substance | Polishing code that hasn't been verified |
| Repeated correction cycles | Same error type fixed 3+ times = model limitation |

### 6. The 30% Rule

Across 13 experiments, ~30% of rounds produced substantive corrections from GPT. The other 70% were either:
- Confirmation (model was already correct)
- Minor style/suggestion (not blocking)
- Diminishing returns (engineering refinement)

This suggests the optimal strategy is: **run 3 rounds per sub-problem, then move on**.

## Unanswered Questions

1. Does this pattern scale to other domains (software engineering, not just physics)?
2. What's the optimal Claude:GPT token ratio?
3. Can we predict which rounds will have high-value corrections?
4. How does this compare to single-model with human review?

## Evidence

All patterns derived from experiments in `runs/small-dc-link-foc-*` (derivation-001 through phase-c-003).
