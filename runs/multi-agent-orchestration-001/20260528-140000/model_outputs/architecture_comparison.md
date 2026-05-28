# Multi-Agent Orchestration: Architecture Comparison

## Recommended: Supervised Hybrid Pipeline

GPT scored this 93/100 as a research direction and recommended **supervised_hybrid_pipeline** as the best pattern.

## Architecture Patterns Evaluated

### 1. Hierarchical (Supervisor → Workers)
- **Pros**: Clear authority, simple control flow
- **Cons**: Bottleneck at supervisor, single point of failure
- **Best for**: Well-defined tasks with clear decomposition

### 2. Peer-to-Peer (Agents Negotiate)
- **Pros**: Flexible, no bottleneck
- **Cons**: Risk of circular loops, hard to resolve disagreements
- **Best for**: Exploratory research, creative tasks

### 3. Pipeline (Sequential with Quality Gates)
- **Pros**: Predictable, easy to audit, bounded iteration
- **Cons**: Rigid, can't adapt to task complexity
- **Best for**: Production workflows, code review

### 4. Hybrid (Context-Dependent Routing)
- **Pros**: Adapts to task, combines strengths
- **Cons**: More complex to implement
- **Best for**: Mixed research + implementation tasks

## Winner: Hybrid

```yaml
architecture:
  primary_pattern: supervised_pipeline
  secondary_pattern: selective_parallel_fanout
  review_pattern: adversarial_cross_review
  repair_pattern: bounded_reflexive_loop
  human_role: escalation_authority
```

## Why Hybrid Wins

Our FOC research showed:
- Claude Code as implementer (local execution, file writes)
- GPT as reviewer (architecture/math review)
- Corrections applied by Claude Code
- Bounded iterations (2-3 max)

This is already a hybrid pipeline with adversarial cross-review.

## Agent Roles

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

## Control Policy

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
