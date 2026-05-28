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
- Current status: derivation-005 has GPT final verification recorded as `PASS_WITH_NOTES` (86/100). The result is conditionally accepted for research handoff; the recommended next experiment is APD branch current / inductor / switching-device sizing.

## Autonomous Advancement Authority

The responsible coding agent is expected to advance this research project end to end without waiting for a human prompt for every step. This authority covers research progression, artifact repair, validators, synthesis, knowledge deposition, and git handoff. It does not turn this repository into a production service or CI/CD deployment project.

Allowed autonomous advancement:

- continue or close the latest active run before starting a new one
- create the next experiment when the latest run has a documented decision and next step
- run local simulations, validators, and cross-model review workflows
- repair stale status docs, run metadata, synthesis, and wiki pages
- commit and push completed research packages when validators pass or only documented warnings remain
- update reusable methodology, evaluator rules, and workflow scripts when a run exposes a durable process improvement

Not allowed under autonomous authority:

- invent missing evidence or mark a model output as accepted knowledge before synthesis and cross-audit are recorded
- overwrite uncommitted work from another agent
- commit secrets, personal notes, large binary artifacts, cache files, or raw credentials
- introduce production deployment, CI/CD publishing, hosted services, heavy frameworks, or automatic external publishing

## Autonomous Research Loop

For every autonomous session:

1. Inspect `git status --short --branch` and identify uncommitted or untracked runs before editing.
2. Read the bootstrap docs and the latest run's `status.md`, `run.yaml`, `task.md`, model outputs, and synthesis.
3. If a run is in progress, either finish its next documented step or explicitly leave it untouched; do not start a competing run in the same thread.
4. If the latest run is closed, choose the next experiment from the documented decision record, current-state index, or accepted wiki route.
5. Produce structured artifacts: task, run metadata, model outputs, synthesis, decision/next step, and cost or usage note when known.
6. Run the relevant validators plus `python3 scripts/check_agent_handoff.py`.
7. Update `docs/SESSION_START_HERE.md`, `docs/runs/token-furnace-current-state.md`, relevant `knowledge/wiki/` pages, and active run status before commit.
8. Commit with an English message and push the active branch when the working tree contains only this session's intended changes.
9. Leave a concise handoff with latest commit, verdict, validation, remaining risks, and next experiment.

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
python3 scripts/check_agent_handoff.py
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
