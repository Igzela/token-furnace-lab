# Run Status: small-dc-link-foc-derivation-005

## Status

`GPT_FINAL_PASS_WITH_NOTES`

## Summary

This run created a low-order joint simulation for FOC + APD + 22uF DC-link behavior.

The first result reported 0/486 passing configurations, but GPT identified model bugs and rejected the core conclusion. The most important bug was using mechanical motor power in the DC-link energy balance instead of electrical motor power.

The revised local synthesis scores the corrected model at 88/100 PASS. The regenerated sweep reports passing configurations, including conditional 300W feasibility.

GPT final verification is recorded as `PASS_WITH_NOTES` (86/100). Energy conservation and APD sanity checks pass. 100-200W is robust; 300W is conditional and needs high nominal bus plus high APD decoupling.

## Current Handoff

Read in this order:

1. `task.md`
2. `model_outputs/claude-code-derivation.md`
3. `model_outputs/gpt-verification.md`
4. `model_outputs/simulation_model.py`
5. `model_outputs/sweep_results.md`
6. `model_outputs/synthesis.md`
7. `model_outputs/gpt-final-verification.md`
8. `synthesis/synthesis.md`

## Next Required Step

Proceed to the next experiment recommended by GPT:

- APD branch current, inductor, and switching-device sizing
- capacitor tolerance and RMS/thermal checks
- high-line overvoltage and device margin checks
- eventually replace voltage-margin derating with mechanical speed dynamics and pump load

## Boundary

Treat derivation-005 as conditionally accepted research evidence, not a production design. Do not claim robust 300W operation without the follow-on APD branch and device-sizing checks.
