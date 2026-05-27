# Run Status: small-dc-link-foc-derivation-005

## Status

`NEEDS_FINAL_VERIFICATION`

## Summary

This run created a low-order joint simulation for FOC + APD + 22uF DC-link behavior.

The first result reported 0/486 passing configurations, but GPT identified model bugs and rejected the core conclusion. The most important bug was using mechanical motor power in the DC-link energy balance instead of electrical motor power.

The later synthesis says the model was corrected and ideal APD behavior was recovered, but the practical APD clamping conclusion is not yet final. A follow-up GPT verification or independent model review is required before accepting any design decision from derivation-005.

Follow-up code note: `model_outputs/simulation_model.py` was corrected after the sweep to define APD-loss-inclusive `Pavg_total` before the FOC current calculation. Treat existing `sweep_results.md` and `sweep_raw.json` as pre-rerun outputs until the simulation is rerun with that correction.

## Current Handoff

Read in this order:

1. `task.md`
2. `model_outputs/claude-code-derivation.md`
3. `model_outputs/gpt-verification.md`
4. `model_outputs/simulation_model.py`
5. `model_outputs/sweep_results.md`
6. `model_outputs/synthesis.md`
7. `synthesis/synthesis.md`

## Next Required Step

Reconcile the corrected simulation model with GPT's `NEEDS_MODEL_FIX` review:

- verify the electrical-power DC-link balance
- verify mean power balance checks
- verify APD energy centering and clamping behavior
- rerun the sweep if needed
- regenerate `sweep_results.md` and `sweep_raw.json` if the corrected model changes outputs
- write a final GPT or independent verification note
- update `knowledge/wiki/small-dc-link-foc-technical-route.md` only after the result is accepted

## Boundary

Do not treat "300W infeasible with 16uF APD" or "300W feasible with 16uF APD" as accepted yet. The accepted status is only: derivation-005 is in progress and needs final verification.
