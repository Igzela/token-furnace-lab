# Agent Instructions

This repository is Token Furnace Lab, a local research lab for testing when high-token agent work produces durable, reviewable artifacts.

## New Session Bootstrap

Every Codex, Claude Code, or other coding-agent session must start by reading:

1. `docs/SESSION_START_HERE.md`
2. `CLAUDE.md`
3. `docs/runs/token-furnace-current-state.md`
4. `knowledge/wiki/small-dc-link-foc-technical-route.md`
5. The latest active run under `runs/`

If these files disagree with git history, repair the documentation before continuing the experiment.

## Current Active Work

- Canonical handoff branch: `main`
- Research branch retained: `exp/hermes-perm-audit-001`
- Active research thread: `small-dc-link-foc-derivation`
- Latest run: `runs/small-dc-link-foc-derivation-005/20260528-010000`
- Current status: derivation-005 is a local revised PASS candidate; GPT final verification is still pending.

## Hard Boundaries

- This is not a production service, hosted product, or CI/CD project.
- Do not introduce heavy frameworks, deployment systems, or automatic publishing.
- Do not invent missing experimental evidence.
- Do not commit API keys, provider credentials, personal notes, or large binary artifacts.
- Do not treat generated model output as accepted knowledge until synthesis and cross-audit are recorded.

## Run Discipline

Each experiment should leave a durable handoff package:

- `task.md`
- `run.yaml` or `status.md`
- `model_outputs/`
- `synthesis/synthesis.md`
- cost or usage note when known
- failure analysis when a model/result is rejected
- decision or next-experiment note
- updated `knowledge/` notes when findings are accepted

After creating or changing a run, validate it with:

```bash
python3 scripts/validate_run.py runs/<experiment>/<timestamp>/
```

Warnings are acceptable for in-progress research, but errors must be fixed before treating a run as complete.

## Documentation Maintenance Rule

Before every commit-sized change, update the handoff docs if status, branch, active run, accepted findings, validators, or next experiments changed:

- `docs/SESSION_START_HERE.md`
- `docs/runs/token-furnace-current-state.md`
- `knowledge/wiki/small-dc-link-foc-technical-route.md`
- `README.md`
- `CLAUDE.md`
- this file
- the active run's `status.md`, `run.yaml`, and `synthesis/`

If no documentation update is needed, state why in the completion report. New sessions must be able to resume from docs without reconstructing state from shell history.
