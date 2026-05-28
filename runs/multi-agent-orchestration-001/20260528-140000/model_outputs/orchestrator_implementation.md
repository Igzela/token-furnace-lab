# Orchestrator Implementation

## What Was Built

`scripts/tf_orchestrator.py` — reusable multi-agent workflow engine.

## Modes

1. **queue** (safest): Writes prompts for Claude Code to run via Agent tool
2. **mock**: Creates placeholder artifacts for dry-run testing
3. **command**: Calls user-provided shell commands

## How It Works

1. Load task YAML (defines subproblems, paths, quality gates)
2. Create run directory with timestamps
3. For each subproblem:
   - Generate agent prompt
   - Dispatch agent (queue/mock/command)
   - Generate review prompt
   - Dispatch review (queue/mock/command)
   - Parse review score/verdict/findings
   - Apply quality gate: ACCEPT / REPAIR / ESCALATE
4. Emit events to events.jsonl

## Tested

- Mock mode: ACCEPT (score 85, verdict PASS_WITH_NOTES)
- Queue mode: Generates prompts for Agent tool execution

## Usage

```bash
# Mock mode (dry run)
python scripts/tf_orchestrator.py run orchestration/tasks/my_task.yaml --mode mock

# Queue mode (generates prompts for Claude Code)
python scripts/tf_orchestrator.py run orchestration/tasks/my_task.yaml --mode queue

# Evaluate gate for existing run
python scripts/tf_orchestrator.py gate runs/orchestration/<run_id> 1
```

## Task YAML Format

```yaml
task_id: my_task
title: My Task
objective: What this task achieves
allowed_paths: [runs/orchestration/]
forbidden_paths: [.env, secrets/]
score_min: 80
max_repair_rounds: 2
subproblems:
  - id: sub1
    title: Subproblem title
    agent: implementer
    subagent_type: Plan
    artifact_path: artifacts/output.md
    review_path: reviews/gpt_review.md
    required_sections: ["Score", "Verdict"]
    prompt: |
      What the agent should do
```
