# derivation-005: Handoff Synthesis

## Verdict

`GPT_FINAL_PASS_WITH_NOTES`

## What Is Accepted

- A joint simulation run exists for FOC + APD + 22uF DC-link behavior.
- GPT found material model bugs in the first result.
- The first "0/486 pass" conclusion must not be used as a design decision.
- The corrected model has regenerated sweep outputs with 100-200W robust and 300W conditional on high nominal bus plus high APD decoupling.
- The revised local synthesis is 88/100 PASS.
- GPT final verification is `PASS_WITH_NOTES` (86/100): energy conservation and APD sanity checks pass, while voltage-margin derating remains an approximation.

## What Is Not Accepted As Robust Yet

- "16uF APD is insufficient for 300W"
- "16uF APD is robustly sufficient for 300W"
- "470uF is required"
- "22uF + APD is limited to 100W"

The accepted result is narrower: 22uF DC-link plus APD remains viable, 100-200W is the first-demo target, and 300W is a stretch target requiring the next device-sizing experiment.

## Evidence Chain

- `task.md` defines the required coupled simulation.
- `model_outputs/claude-code-derivation.md` records the initial simulation approach.
- `model_outputs/gpt-verification.md` records GPT's `NEEDS_MODEL_FIX` review.
- `model_outputs/simulation_model.py` and `model_outputs/sweep_results.md` record the local model and sweep output.
- `model_outputs/gpt-final-verification.md` records GPT's final `PASS_WITH_NOTES` review.
- `model_outputs/synthesis.md` records the latest local interpretation.

## Next Experiment Step

Run APD/device sizing:

1. APD branch current and inductor sizing.
2. Switching-device voltage/current stress.
3. Capacitor tolerance, RMS current, and thermal checks.
4. High-line surge and 500V film capacitor margin.
5. Later model upgrade: mechanical speed dynamics with pump load instead of voltage-margin derating.
