# Token Furnace Lab — Workflow Quality Gates

## Overview

Token Furnace Lab v1 workflow is structurally sound (26/30 strong gates) but not yet mechanically enforced. The 5 weak gates create risks for false PASS, evidence gaps, and naming inconsistency.

## Gate Categories

### Strong Gates (26/30)

1. **Experiment Definition (5/5)**: type, target separation, scope, non-goals, healthy failure
2. **Evidence (4/5)**: evidence_path, evidence_type, model inference check, secret scanning
3. **Matrix/Verdict (5/6)**: matrix exists, P0 follow-up, path-aware, verdicts separated, triple closeout
4. **Agent Handoff (4/5)**: Claude Code bounded, GPT bounded, uncertainty preserved, evidence resolution
5. **Fix/Regression (5/5)**: narrow scope, no unrelated refactor, regression exists, tests run, behavior preserved
6. **Closeout/Knowledge (4/5)**: synthesis exists, knowledge deposited, known gaps recorded, tag/commit

### Weak Gates (5/30)

1. **W006: pre/post git status** — Not explicitly recorded in runs
2. **W012: matrix summary counts** — No automated checker; rules defined but not enforced
3. **W019: Codex not consistently used** — Some phases skip third-model review
4. **Naming inconsistency** — model-outputs/ vs model_outputs/, different scripts expect different names
5. **validate_run.py drift** — Hardcoded filenames don't match actual run structure

## Key Risks

1. **False PASS risk**: Matrix summary counts unchecked → could declare PASS with mismatched totals
2. **Evidence gap risk**: Accepted findings without evidence_path → could pass on model inference alone
3. **Naming inconsistency risk**: Different scripts expect different directory names → validation failures

## Recommendations

1. **Unified naming**: Canonical `model_outputs/` (underscore), update templates and scripts
2. **Matrix consistency validator**: `scripts/validate_matrix_consistency.py` to enforce 7 consistency checks
3. **Synthesis evidence validator**: `scripts/validate_synthesis_evidence.py` to enforce evidence_path
4. **Update validate_run.py**: Use canonical layout, not hardcoded filenames
5. **Codex role contract**: Required if declared in experiment.yaml, optional otherwise

## Methodology Insight

"Token Furnace Lab v1 has methodology. Phase 3 validates whether methodology can be mechanically enforced, not just documented."
