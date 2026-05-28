# derivation-005: Synthesis (Final)

## Score: 86/100 (PASS_WITH_NOTES)

**Rationale**: Model fully corrected per GPT feedback. Energy conservation verified: ideal APD shows correct Vdc~300V with slight decline from losses. 300W achievable with 22µF + APD (conditionally). 81.5% pass rate across 486 configurations. GPT final verdict: PASS_WITH_NOTES — 300W is conditionally feasible, not robust.

## Key Findings

### 1. Model Corrections (Final)
- **Electrical power**: Pmotor = 1.5 × Vq × Iq (3-phase, includes copper losses)
- **Iq from power command**: Quadratic solution of Ptarget = 1.5 × (Rs×Iq + ωe×ψf) × Iq
- **APD energy center**: Vapd_center = √((Vmin² + Vmax²) / 2)
- **APD loss model**: Losses as separate DC-link burden (dE_dc/dt includes -Ploss)
- **Voltage margin scaling**: Ptarget = Pavg × min(1, Vmargin/Vmargin_nom)
- **Sanity checks**: All 4 GPT-required checks pass

### 2. Root Causes of Previous Failures (3 iterations)
1. **v1**: Pmotor used mechanical power (Te×ω) instead of electrical (1.5×Vq×Iq)
2. **v2**: APD losses applied to commanded power + Ploss_avg factor 4/π vs 2/π
3. **v3**: APD losses embedded in APD power flow (sign asymmetry) + no Vdc-dependent power scaling

### 3. GPT Sanity Checks (All Pass)
- mean(Papd) ≈ 0 ✓
- Energy conservation: d(Edc+Eapd)/dt = Pin - Pmotor - Ploss ✓
- D=1.0 lossless: Vdc = 300.0V, 0%pp ✓
- D=1.0 with losses: Vdc = 296-297V, 0.3%pp, slight decline ✓

### 4. 300W Achievable with 22µF + APD
- 72/162 300W configs pass (44%)
- Best: 354V/12µF/95%/4000rpm → 1.8%pp Vdc ripple
- Reference: 300V/16µF/90%/4000rpm → 4.7%pp (PASS)

### 5. Operating Regions
- **100W**: 162/162 (100%) pass
- **200W**: 162/162 (100%) pass
- **300W**: 72/162 (44%) pass

### 6. Failure Modes
- Vdc ripple > 15%pp: 90 failures
- Vdc_max > 400V: 81 failures
- No Vdc_min failures (voltage-margin scaling prevents collapse)

## GPT Final Verdict (PASS_WITH_NOTES, 86/100)

### Verdict Components
- Energy conservation: PASS
- APD sanity tests: PASS
- Voltage margin derating: PASS_WITH_NOTES
- 300W feasibility: CONDITIONALLY_PASS
- 100-200W feasibility: PASS

### GPT Notes on Voltage Margin Scaling
Voltage-margin power scaling (Ptarget = Pavg × min(1, Vmargin/Vmargin_nom)) is:
- **Accepted for feasibility simulation** — models FOC voltage-saturation derating
- **NOT a physical pump load model** — real pump: Pload ≈ P0 + kω³
- Next required model: mechanical speed dynamics with pump load

### GPT Recommended Engineering Baseline
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

### GPT Config Ranking
1. **First priority**: 300V / 16-22µF APD / 90-95% / 4000rpm — no high-line dependency, overvoltage risk more可控
2. **Cautious**: 354V / 12µF / 95% — high-line near 400V device boundary, need to check Vdc_max < 400V, Vapd_max < 500V, capacitor tolerance, surge

### GPT Remaining Model Issues (not blocking PASS)
1. Pin(t) is ideal single-phase power model (not real rectifier conduction angle)
2. APD is average power model (no H-bridge inductor, current loop, switching ripple)
3. APD capacitor ESR, RMS current, thermal not modeled
4. Capacitor tolerance not swept (-20% → 16µF becomes 12.8µF)
5. FOC current loop, SMO observer dynamics not modeled
6. Ptarget voltage scaling is not pump mechanical dynamics
7. High-line overvoltage needs surge and device voltage margin check

### GPT Next Step Recommendation
If continuing to derivation-006: APD branch current / inductor / switching device sizing (not more energy model refinement)

## Decision Record

**Solution fork FINAL**: Path A (22µF + APD) works — conditionally.
- 300W: conditionally feasible (72/162 pass, 44%) with D≥90% APD, Vnom≥300V, speed≥4000rpm
- 200W: robust (162/162 pass, 100%)
- 100W: robust (162/162 pass, 100%)
- First demo target: 100-200W
- Recommended baseline: 22µF DC-link + 22µF/500V APD
- No need to increase Cdc to 470µF
- Voltage-margin power scaling prevents Vdc collapse

## Model Limitations (Accepted)
1. FOC modeled as power command (not full current/speed PI loops)
2. APD loss model simplified (proportional to |Papd|, not I²R)
3. Single-phase input idealized as Pavg×[1-cos(2ωt)]
4. No ESR, no switching dynamics, no current loop bandwidth

## Iteration History
- v1 (score 72): Pmotor bug → Vdc collapse
- v2 (score 78): APD loss bugs → Vdc collapse
- v3 (score 88): APD loss sign + no Vdc scaling → ideal APD drift
- v4 (score 92 local): All fixes applied, sanity checks pass
- GPT final (score 86): PASS_WITH_NOTES — 300W conditionally feasible, not robust
