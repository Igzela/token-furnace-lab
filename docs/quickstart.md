# Quick Start Guide

## 1. Create a New Run

```bash
cd ~/Projects/token-furnace-lab
./scripts/new-run.sh my-experiment-001
```

## 2. Define the Task

Edit `runs/YYYY-MM-DD-my-experiment-001/task.md`:
- Describe the objective
- List models to use
- Set verification criteria

## 3. Execute the Experiment

Run the task with each assigned model. Save outputs to `model_outputs/`.

## 4. Cross-Audit

Have a judge model compare all outputs. Save to `cross_audit/judge-report.md`.

## 5. Document Costs

Fill in `cost_estimate.md` with token usage and costs.

## 6. Analyze Failures

Document any failures in `failure_analysis.md`.

## 7. Distill Knowledge

```bash
./scripts/distill.sh runs/YYYY-MM-DD-my-experiment-001
```

Move outputs to appropriate knowledge directories:
- Wiki notes → `knowledge/wiki/`
- Rules → `knowledge/evaluator-rules/`
- Failures → `knowledge/failures/`
- Decisions → `knowledge/decisions/`

## 8. Plan Next Experiment

Fill in `next_experiment.md` based on observations.

## Example First Run

```bash
# Create run
./scripts/new-run.sh hermes-perm-audit-001

# Edit task.md to define: "Audit hermes-gateway-lab permission boundaries"

# Execute with 3 models, save outputs

# Cross-audit with judge model

# Distill knowledge
./scripts/distill.sh runs/2026-05-27-hermes-perm-audit-001
```
