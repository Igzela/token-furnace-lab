# derivation-005: GPT Final Verification

## Verdict: PASS_WITH_NOTES (86/100)

**Date**: 2026-05-28
**Model**: GPT (via ChatGPT)
**Input**: Corrected v4 simulation model + sweep results

## Review Components

| Component | Status | Notes |
|-----------|--------|-------|
| Energy conservation | PASS | d(Edc+Eapd)/dt = Pin - Pmotor - Ploss verified |
| APD sanity tests | PASS | mean(Papd)≈0, D=1 lossless stable, losses cause decline |
| Voltage margin derating | PASS_WITH_NOTES | Acceptable for feasibility, not physical pump model |
| 300W feasibility | CONDITIONALLY_PASS | 72/162 pass (44%), needs high Vnom + high D |
| 100-200W feasibility | PASS | 100% pass rate |

## GPT Recommended Engineering Baseline

```yaml
recommended_baseline:
  Cdc: 22µF
  Capd: 22µF / 500V film
  APD_decoupling_target: 90-95%
  nominal_bus: 300V
  target_power:
    robust: 200W
    stretch: 300W
  first_demo: 100-200W
```

## GPT Config Ranking

1. **First priority**: 300V / 16-22µF APD / 90-95% / 4000rpm — no high-line dependency
2. **Cautious**: 354V / 12µF / 95% — high-line near 400V device boundary

## GPT Notes on Voltage Margin Scaling

Ptarget = Pavg × min(1, Vmargin/Vmargin_nom) is a controller derating approximation, not a physical pump load model.

Real pump behavior under voltage sag:
1. FOC limits Iq
2. Electromagnetic torque insufficient
3. Speed drops
4. Pump power drops with speed
5. New mechanical equilibrium

Voltage-margin scaling is acceptable for feasibility simulation but must be documented as approximation. Next required model: mechanical speed dynamics with pump load P ∝ ω³.

## Remaining Model Issues (not blocking PASS)

1. Pin(t) is ideal single-phase power model (not real rectifier conduction angle)
2. APD is average power model (no H-bridge inductor, current loop, switching ripple)
3. No capacitor ESR, RMS current, thermal modeling
4. No capacitor tolerance sweep (-20% → 16µF becomes 12.8µF)
5. No FOC current loop, SMO observer dynamics
6. Ptarget voltage scaling is not pump mechanical dynamics
7. High-line overvoltage needs surge and device voltage margin check

## GPT Recommendation for Next Step

derivation-006: APD branch current / inductor / switching device sizing
(Not more energy model refinement)
