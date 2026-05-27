# Token Furnace Lab — Workflow Validators

## Overview

Three validators enforce workflow quality gates mechanically, replacing manual-only checks.

## Validators

### validate_run.py
- **Purpose**: Validate run directory completeness and safety
- **Checks**: required files, model outputs, synthesis, secret scanning
- **Layout**: Supports canonical (model_outputs/) and legacy (model-outputs/)
- **Role contract**: Warns if declared Codex role has no output

### validate_matrix_consistency.py
- **Purpose**: Validate matrix YAML consistency
- **Checks**:
  1. summary.total_cases == actual cases count
  2. summary.by_status == actual case statuses
  3. P0 fail requires follow_up
  4. PASS case has evidence
  5. No model_inference only

### validate_synthesis_evidence.py
- **Purpose**: Validate synthesis evidence completeness
- **Checks**:
  1. synthesis.md exists
  2. experiment_verdict exists
  3. target_control_verdict exists
  4. accepted findings have evidence
  5. known gaps listed when applicable

## Canonical Run Layout

```
run_directory/
  task.md
  model_outputs/
    claude-code-output.md
    gpt-reviewer-output.md
    codex-risk-reviewer-output.md  (optional)
  synthesis/
    synthesis.md
    decision-record.md  (optional)
    cost_estimate.md  (optional)
```

## Usage

```bash
# Validate a run
python3 scripts/validate_run.py runs/<experiment>/<timestamp>/

# Validate matrix consistency
python3 scripts/validate_matrix_consistency.py knowledge/matrices/<matrix>.yaml

# Validate synthesis evidence
python3 scripts/validate_synthesis_evidence.py runs/<experiment>/<timestamp>/
```

## Coverage

These validators cover the weak gates identified in workflow-quality-gate-audit-001:
- W006: pre/post status → bounded by validate_run.py warnings
- W012: matrix summary counts → validate_matrix_consistency.py
- Evidence gap → validate_synthesis_evidence.py
- Naming drift → canonical model_outputs/ with legacy compatibility
- validate_run.py drift → flexible model output / role contract
