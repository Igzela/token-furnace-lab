# Multi-Agent Orchestration: GPT Review

## Score: 93/100 — STRONG_RESEARCH_DIRECTION

**Verdict**: Strong research direction for Token Furnace Lab
**Best pattern**: supervised_hybrid_pipeline
**First build target**: agent_contract_schema + quality_gate_runner

## Key Insight

"Build an orchestrator that makes agents produce evidence-bound artifacts, not just messages."

**Main correction**: Do not aim for "fully autonomous" as the first target. Aim for bounded autonomy with quality gates, rollback, and human escalation.

## Architecture Recommendation

```yaml
architecture:
  primary_pattern: supervised_pipeline
  secondary_pattern: selective_parallel_fanout
  review_pattern: adversarial_cross_review
  repair_pattern: bounded_reflexive_loop
  human_role: escalation_authority
```

## Concrete Design

### Orchestrator Responsibilities
- Task normalization
- Subproblem decomposition
- Budget assignment
- Agent dispatch
- Quality gate enforcement
- Escalation decision
- Final synthesis

### Agent Roles

```yaml
agents:
  explorer:
    tools: read/search
    writes: none
  planner:
    tools: docs
    writes: plan only
  implementer:
    tools: edit/test
    writes: scoped worktree
  reviewer:
    tools: read/diff/test
    writes: review only
  risk_reviewer:
    tools: read/static check
    writes: risk report
  synthesizer:
    tools: read all outputs
    writes: final report
```

### Control Policy

```yaml
control_policy:
  max_iterations_per_subproblem: 2
  max_parallel_agents: 3
  require_evidence_for_pass: true
  require_test_or_validator_for_implementation_pass: true
  human_escalation_on_low_confidence: true
```

## Quality Scoring

```yaml
quality_score:
  correctness: 30
  evidence_quality: 20
  completeness: 15
  implementation_readiness: 15
  risk_handling: 10
  reproducibility: 10
```

### Verdicts

```yaml
experiment_verdict: COMPLETE | INCOMPLETE
target_verdict: PASS | PASS_WITH_NOTES | FAIL
platform_verdict: PASS | PASS_WITH_NOTES | FAIL
confidence: HIGH | MEDIUM | LOW
```

## Failure Modes and Controls

### 1. Hallucination Propagation
- **Failure**: worker invents a claim; reviewer accepts it because plausible
- **Control**: accepted finding requires evidence path; model inference cannot produce PASS alone; every major formula needs source or derivation trace

### 2. Circular Validation Loops
- **Failure**: Agent A approves Agent B; Agent B approves Agent A
- **Control**: one non-generative validator required (test, script, calculation, grep, diff, matrix checker)

### 3. Token Budget Exhaustion
- **Failure**: agents keep expanding context
- **Control**: budget per subproblem, summary checkpoint, evidence index, max repair rounds, archive old context

## Human Escalation Policy

### Escalate When:
1. Agents disagree on a high-impact conclusion
2. Reviewer finds safety/legal/security risk
3. Write scope needs expansion
4. Cost exceeds budget
5. Output confidence stays low after 2 repair rounds
6. Task goal changes
7. Irreversible action is requested
8. External real-world effect exists

### Do NOT Escalate For:
- Minor formatting
- Routine test failure with clear fix
- Known validator mismatch
- Low-risk documentation update

## Iteration Control

```yaml
continue_if:
  - high_value_problem
  - reviewer finds concrete fix
  - evidence gap is bounded
stop_if:
  - no new evidence
  - same disagreement repeats
  - token budget exceeded
  - confidence remains low
```

Do not allow infinite agent debate.

## Most Valuable Sub-Directions (ranked)

1. **Agent contract schema** (value: 10) — converts chat-based coordination into machine-checkable workflow
2. **Quality gate automation** (value: 10) — directly prevents false PASS and hallucination propagation
3. **Bounded repair loop** (value: 9) — matches observed 2-3 iteration ROI
4. **Worktree isolated execution** (value: 9) — enables safe parallel Claude Code workers
5. **Confidence escalation policy** (value: 8) — decides when human is needed
6. **Orchestration pattern benchmark** (value: 8) — gives empirical evidence, needs setup
7. **Peer-to-peer negotiation** (value: 4) — interesting but high risk of loops
8. **EKF-like agent debate** (value: 3) — likely expensive and low operational value

## Phased Implementation

### Phase O-001: Agent Contract Schema
Define machine-readable contract for agent handoffs.

### Phase O-002: Quality Gate Runner
Automated quality scoring and verdict assignment.

### Phase O-003: Bounded Repair Loop
2-iteration max with escalation on failure.

### Phase O-004: Worktree-Isolated Execution
Safe parallel workers with artifact merging.

### Phase O-005: Confidence and Escalation Model
Score confidence, route to human when low.

### Phase O-006: Replay Experiment
Replay prior FOC tasks through orchestrator, compare to manual baseline.

## What to Avoid First

- Pure peer-to-peer agents
- Unlimited autonomous loops
- Fully automatic commits without gated review

## Final Verdict

```yaml
proposal_score: 93/100
verdict: STRONG_RESEARCH_DIRECTION
best_pattern: supervised_hybrid_pipeline
first_build_target: agent_contract_schema + quality_gate_runner
```
