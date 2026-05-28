# Agent Contract Schema (v1.0)

## Overview

Machine-readable contract for multi-agent orchestration. Defines what agents can do, what artifacts they must produce, and how quality is enforced.

## Three Contracts

### 1. AgentTask Contract
What an agent is allowed/expected to do.

```yaml
agent_contract:
  version: "1.0"
  contract_id: string
  run_id: string
  parent_task_id: string | null

  task:
    objective: string
    scope:
      target_repo: string
      allowed_paths: [string]
      forbidden_paths: [string]
      allowed_actions: [read, write, test, commit]
      forbidden_actions: [network, secrets, destructive_ops]
    non_goals: [string]
    assumptions: [string]
    expected_outputs: [string]

  agent:
    role: explorer | implementer | reviewer | risk_reviewer | synthesizer
    model_hint: string | null
    tools_allowed: [read, edit, shell, test, browser, send_message]
    execution_mode: foreground | background
    worktree: string | null
```

### 2. Artifact Contract
What the produced file must contain.

```yaml
  artifact:
    artifact_id: string
    artifact_type: code | review | plan | derivation | synthesis | test_report
    file_path: string
    required_sections: [string]
    evidence_required: true
    schema_path: string | null
```

### 3. ReviewFinding Contract
How corrections are represented and gated.

```yaml
  review:
    required: true
    reviewer_role: gpt_reviewer | codex_reviewer | security_reviewer
    review_output_path: string
    finding_schema_required: true
```

## Quality Gate

```yaml
  quality_gate:
    score_min: 70
    verdict_accept: [PASS, PASS_WITH_NOTES]
    verdict_reject: [FAIL]
    max_repair_rounds: 2
    require_evidence_for_pass: true
    require_tests_for_code_pass: true
    reject_if:
      - accepted_finding_without_evidence
      - missing_required_section
      - score_below_min
      - forbidden_path_changed
      - unresolved_high_severity_finding
```

## Budget

```yaml
  budget:
    max_tokens: 100000
    max_iterations: 3
    timeout_seconds: 300
    max_cost_usd: null
```

## Escalation

```yaml
  escalation:
    triggers:
      - low_confidence
      - reviewer_disagreement
      - high_severity_unresolved
      - scope_expansion_needed
      - budget_exceeded
```

## Gate Result

```yaml
  gate_result:
    status: ACCEPT | REPAIR | REJECT | ESCALATE
    round: 1
    score: 86
    verdict: PASS_WITH_NOTES
    blocking_findings: []
    scope_violations: []
    budget_status:
      tokens_used: 42100
      iterations_used: 1
    next_action:
      type: repair | accept | escalate
      assign_to: implementer
      prompt_path: runs/<run_id>/gate_results/repair_prompt.md
```

## Decision Logic

```python
if schema_invalid:
    REJECT

if forbidden_path_changed:
    ESCALATE

if score < score_min:
    REPAIR if repair_rounds_left else ESCALATE

if blocking_findings_open:
    REPAIR if repair_rounds_left else ESCALATE

if accepted_findings_without_evidence:
    REJECT

if required_tests_missing_for_code:
    REPAIR

if verdict in accepted and no blocking findings:
    ACCEPT
```

## Key Design Decision

**Separate review score from gate decision.**

GPT can say:
```yaml
score: 86
verdict: PASS_WITH_NOTES
```

But the runner can still decide:
```yaml
status: REPAIR
reason: "High severity finding remains open"
```

This prevents: reviewer gives good score while one blocking issue remains unresolved.
