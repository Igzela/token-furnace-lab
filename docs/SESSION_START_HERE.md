# Session Start Here

Read this file first in any new Codex, Claude Code, or other coding-agent session.

## Project Identity

Token Furnace Lab is a local AI-agent experiment lab. It deliberately spends many tokens only when the work produces reviewable artifacts, cross-model critique, and reusable knowledge.

## Current State

- Maturity: `L3-VALIDATED`
- Completed platform phases: Hermes permission audit, MCP bridge boundary audit, workflow quality-gate audit, PDF-to-algorithm benchmark
- Active research thread: small DC-link PMSM FOC / APD / 22uF DC-link derivation
- Active branch: `exp/hermes-perm-audit-001`
- Default cloud `main` must not be treated as authoritative unless it contains the same handoff docs and active research history.

## Latest Active Run

Latest run: `runs/small-dc-link-foc-derivation-005/20260528-010000`

Status: `NEEDS_FINAL_VERIFICATION`

What happened:

- Claude Code built a low-order FOC + APD + 22uF DC-link simulation and sweep.
- GPT flagged model bugs in the first result, especially DC-link energy using mechanical instead of electrical motor power.
- A later synthesis says core fixes were applied and ideal APD behavior was recovered, but practical APD clamping still needs final verification before accepting the conclusion.

Do not treat derivation-005 as a final design decision until the corrected model, GPT verification, and synthesis are reconciled.

## Must-Read Order

1. `AGENTS.md` — cross-agent workflow and documentation maintenance discipline
2. `CLAUDE.md` — project rules, active experiments, and research conventions
3. `docs/runs/token-furnace-current-state.md` — platform and phase status
4. `knowledge/wiki/small-dc-link-foc-technical-route.md` — accepted FOC/APD findings so far
5. `runs/small-dc-link-foc-derivation-005/20260528-010000/status.md` — latest in-progress handoff
6. The latest run's `task.md`, `model_outputs/`, and `synthesis/`

## Default Agent Behavior

- Inspect `git status --short --branch` before work.
- Confirm whether the task is documentation-only, run continuation, model verification, or new experiment design.
- Do not accept a model output as knowledge until cross-audit and synthesis are documented.
- Keep run artifacts small, structured, and reviewable.
- Prefer local scripts and simple Python/Bash over new dependencies.

## Documentation Maintenance

Before every commit-sized change, update the docs that a future session will read first:

- `docs/SESSION_START_HERE.md`
- `docs/runs/token-furnace-current-state.md`
- `knowledge/wiki/small-dc-link-foc-technical-route.md`
- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- active run `status.md`, `run.yaml`, and `synthesis/`

If no docs changed, explain why in the completion report.
