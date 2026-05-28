# Multi-Agent Orchestration Architecture

## Overview

Reusable multi-agent workflow engine for Token Furnace Lab. Converts user intent into structured agent tasks with quality gates, deterministic validators, and cross-model review.

## Architecture Pattern: Supervised Hybrid Pipeline

```
User intent → Task YAML → Orchestrator → Agent dispatch → Artifact
                                                            ↓
                                              Deterministic validators
                                                            ↓
                                              Review (same or cross-model)
                                                            ↓
                                              Quality gate (score + verdict + validators)
                                                            ↓
                                              ACCEPT / REPAIR / ESCALATE
```

Key design: **validators are separate from reviewers**. Validators check structural properties (states defined, transitions valid, score in range). Reviewers assess quality (completeness, correctness, safety).

## Components

### 1. Orchestrator (`scripts/tf_orchestrator.py`, 833 lines)

**Modes**:
- `queue`: Generate prompts for Claude Code to run (safest, recommended)
- `mock`: Create placeholder artifacts for dry-run testing
- `command`: Call user-provided shell commands

**Subcommands**:
- `run <task.yaml>` — Execute full orchestration loop
- `gate <run_dir> <round>` — Re-evaluate gate for existing run
- `validate <artifact> --type <type>` — Run validators on single artifact
- `closeout <run_dir>` — Generate final_verdict.yaml + synthesis.md

**Adapter pattern**: Cannot directly call Claude Code Agent tool from Python. Instead, generate prompts that a human or automation layer feeds to Claude Code. This is intentional — the orchestrator is agent-agnostic.

### 2. Deterministic Validators

| Validator | Script | Checks |
|-----------|--------|--------|
| State machine | `validate_state_machine.py` | States defined, transitions valid, UNIVERSAL hard-fault rules, fault codes complete |
| Review artifact | `validate_review_artifact.py` | Score 0-100, valid verdict, confidence, findings section, blocking evidence |
| Scope diff | `validate_scope_diff.py` | Changed files in allowed paths, no secrets, no forbidden paths |

**Key insight**: Validators catch structural issues that reviewers miss. A reviewer might give 90/100 to a state machine that's missing UNIVERSAL hard-fault rules. The validator catches it as CRITICAL.

### 3. Quality Gate

Score-based + verdict-based + validator-based:

```
IF validator_errors with CRITICAL/HIGH → REPAIR or ESCALATE
IF score < score_min → REPAIR (if rounds left) or ESCALATE
IF blocking findings → REPAIR (if rounds left) or ESCALATE
IF verdict in ACCEPT_VERDICTS → ACCEPT
ELSE → REPAIR or ESCALATE
```

### 4. Budget Ledger

Tracks per-run:
- Iterations (subproblems × rounds)
- Wall time
- Per-round details (subproblem, round, gate status, score)

Budget limits: max_iterations, max_tokens, timeout_seconds. Exceeded → break loop.

### 5. Idempotent Resume

`run_state.json` records completed subproblems. On restart, skip completed ones. Survives interruption.

### 6. Rollback Policy

On worktree failure: quarantine worktree contents to `run/quarantine/<subproblem>/worktree/` instead of discarding. Preserves evidence for debugging.

### 7. Closeout Generator

Produces `final_verdict.yaml` + `synthesis.md`:
- Overall verdict (PASS/FAIL/ESCALATE)
- Average score
- Per-subproblem gate results
- Budget summary
- Next experiment placeholder

## Task YAML Format

```yaml
task_id: my_task
title: Human-readable title
objective: What this task achieves

allowed_paths:
  - runs/my-experiment/
forbidden_paths:
  - .env
  - secrets/

score_min: 70
max_repair_rounds: 2
run_validators: true
worktree_isolation: false

budget:
  max_iterations: 10
  max_tokens: 100000
  timeout_seconds: 300

subproblems:
  - id: subproblem_1
    title: Description
    agent: implementer
    subagent_type: Plan
    artifact_type: state_machine  # or review, derivation, design_doc
    artifact_path: artifacts/output.md
    review_path: reviews/review.md
    required_sections:
      - "## Section Name"
    prompt: |
      Detailed prompt for the agent.
```

## Design Decisions

### Why adapter pattern (not direct Agent calls)?

Claude Code's Agent tool is only available inside Claude Code sessions. The orchestrator runs as a Python script. The adapter pattern generates prompts that can be fed to any agent execution layer (Claude Code, GPT, Codex, shell). This makes the orchestrator agent-agnostic.

### Why separate validators from reviewers?

Reviewers are expensive (LLM calls) and non-deterministic. Validators are cheap (deterministic parsing) and catch structural issues reliably. Run validators first — if they fail, don't waste a review call.

### Why worktree isolation?

Multi-subproblem runs can produce conflicting file changes. Git worktrees give each subproblem an isolated workspace. On success, copy artifacts back. On failure, quarantine the worktree.

### Why budget ledger?

Token costs are real. The budget ledger makes cost visible and enforces limits. Without it, a repair loop could burn unlimited tokens.

## Current Limitations

1. **No direct Agent tool integration** — prompts must be manually fed or wrapped in automation
2. **Single-threaded** — subproblems execute sequentially (parallel dispatch would require async)
3. **No persistent budget across sessions** — budget resets on restart
4. **Scope validator not integrated into main loop** — exists as standalone script

## Usage Example

```bash
# Dry run
python3 scripts/tf_orchestrator.py run orchestration/tasks/my_task.yaml --mode mock

# Generate prompts for Claude Code
python3 scripts/tf_orchestrator.py run orchestration/tasks/my_task.yaml --mode queue

# Re-evaluate gate
python3 scripts/tf_orchestrator.py gate runs/orchestration/<run_id> 1

# Validate single artifact
python3 scripts/tf_orchestrator.py validate artifact.md --type state_machine

# Generate closeout
python3 scripts/tf_orchestrator.py closeout runs/orchestration/<run_id>
```

## E2E Test Results

**Run**: `runs/orchestration/20260528-101549/`
**Task**: Review Phase E-001 fault recovery model
**Mode**: queue → Plan subagent → gate → closeout

| Step | Result |
|------|--------|
| Prompt generation | 62-line prompt with constraints, sections, evidence requirements |
| Agent execution | Plan subagent reviewed fault recovery model, produced 207-line artifact |
| Review scoring | 82/100, PASS_WITH_NOTES, HIGH confidence |
| Gate evaluation | ACCEPT (82 >= 70 threshold) |
| Findings | 1 HIGH (current_sensor_fault missing from UNIVERSAL), 3 MEDIUM, 6 LOW |
| Closeout | final_verdict.yaml + synthesis.md generated |

**Key finding**: The agent found that `current_sensor_fault` is missing from the UNIVERSAL hard-fault section — it only appears in FOC_NORMAL, meaning current sensor loss in FOC_DERATED, OBSERVER_DEGRADED, or APD_DEGRADED leaves the system running blind.
