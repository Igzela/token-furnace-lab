# derivation-005: Handoff Synthesis

## Verdict

`LOCAL_PASS_NEEDS_GPT_FINAL`

## What Is Accepted

- A joint simulation run exists for FOC + APD + 22uF DC-link behavior.
- GPT found material model bugs in the first result.
- The first "0/486 pass" conclusion must not be used as a design decision.
- The corrected model has regenerated sweep outputs: 336/486 overall pass, 66/162 300W pass.
- The revised local synthesis is 88/100 PASS.
- Any sealed conclusion about 300W feasibility must wait for GPT final verification.

## What Is Not Yet Accepted

- "16uF APD is insufficient for 300W"
- "16uF APD is sufficient for 300W"
- "470uF is required"
- "22uF + APD is limited to 100W"

Those may become true after verification, but they are not accepted knowledge yet.

## Evidence Chain

- `task.md` defines the required coupled simulation.
- `model_outputs/claude-code-derivation.md` records the initial simulation approach.
- `model_outputs/gpt-verification.md` records GPT's `NEEDS_MODEL_FIX` review.
- `model_outputs/simulation_model.py` and `model_outputs/sweep_results.md` record the local model and sweep output.
- `model_outputs/synthesis.md` records the latest local interpretation and should be reconciled against GPT's review.

## Next Experiment Step

Run final verification of the corrected model:

1. Confirm DC-link energy uses electrical motor power.
2. Add or inspect average power balance sanity checks.
3. Verify APD energy centering and clamping behavior.
4. Send corrected results to GPT or another judge model for final review.
5. Update the wiki only after the conclusion is accepted.
