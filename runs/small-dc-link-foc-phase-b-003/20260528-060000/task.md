# Phase B-003: Three-Threshold Blend + Anti-Chatter

## Goal

Apply GPT's Phase B-002 corrections: three-threshold observer-gated blend and anti-chatter transition rule.

## GPT Corrections to Apply

1. **Three thresholds**: detect(45°)/blend(30°)/FOC handover(15-20° for N samples)
2. **Anti-chatter**: freeze/rollback α if θ_err increases during blend
3. **RSS refinement**: linear sum for systematic errors, RSS for random
4. **Clarify where max error occurs**: pre-blend vs during blend

## Corrected Blend Logic

```
if θ_err < 45°:
    observer_detected = true

if observer_detected and θ_err < 30°:
    blend_allowed = true
    α += Δα (advance blend)

if θ_err > 35° during blend:
    freeze α (anti-chatter)
    or rollback α by small amount

if θ_err < 20° for N consecutive samples:
    FOC_handover_complete = true
    α = 1.0 (full observer)
```

## Required Outputs

1. Updated simulation with three-threshold blend
2. Anti-chatter logic verification
3. Sweep with refined parameters
4. GPT final review
