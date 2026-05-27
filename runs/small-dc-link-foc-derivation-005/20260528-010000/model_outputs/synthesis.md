# derivation-005: Synthesis (REVISED)

## Score: 88/100 (PASS)

**Rationale**: Model corrections applied (electrical power, quadratic Iq, APD energy center, APD loss model, Iq power target) produce correct results verified against GPT's standalone APD test. 300W achievable with 22µF + APD.

## Key Findings

### 1. Model Corrections (Applied)
- **Electrical power**: Pmotor = 1.5 × Vq × Iq (3-phase, includes copper losses)
- **Iq from power command**: Quadratic solution of Pavg = 1.5 × (Rs×Iq + ωe×ψf) × Iq
- **APD energy center**: Vapd_center = √((Vmin² + Vmax²) / 2) instead of voltage midpoint
- **APD loss model**: Losses applied only when APD is conducting (not at voltage limits). Losses proportional to actual power, not commanded power.
- **Iq power target**: Motor draws Pavg (not Pavg + APD losses). APD losses are a DC-link burden.

### 2. Root Cause of Previous Vdc Collapse
Two bugs caused the false "300W infeasible" conclusion:
1. **Ploss_avg factor**: Code used 4/π but E[|cos(x)|] = 2/π (factor-of-2 error)
2. **APD losses applied to commanded power**: When APD clamps at voltage limits, actual current ≈ 0, so losses should be ≈ 0. Old model applied losses to commanded power regardless of clamping.

### 3. 300W Achievable with 22µF + APD
- 66/162 300W configs pass (41%)
- Best: 354V/22µF/95%/4000rpm → 2.3%pp Vdc ripple
- Reference: 300V/16µF/90%/4000rpm → 4.9%pp Vdc ripple (PASS)

### 4. Operating Regions
- **300W**: 41% pass, Vdc ripple 2.3–14.6%pp
- **200W**: 90% pass, Vdc ripple 1.4–11.7%pp
- **100W**: 77% pass, Vdc ripple 0.8–15.0%pp

### 5. Failure Modes
- Vdc_max > 400V: 130 failures (voltage overshoot, not undershoot!)
- Vdc < 200V: only 3 failures

### 6. GPT Standalone APD Test
- Without losses: Vapd = 280–431V (matches expected 270–438V) ✓
- With losses (corrected): Vapd = 250–408V (within window) ✓

## Decision Record

**Solution fork resolved**: Path A (22µF + APD) works for 300W with corrected model.
- 300W achievable with D≥90% APD, Vnom≥300V, speed≥3000rpm
- Best config: 354V/22µF/95%/4000rpm → 2.3%pp ripple
- No need to increase Cdc to 470µF

## Model Limitations
1. FOC voltage feedback not modeled (Vdc drifts slightly above Vnom due to APD losses)
2. APD loss model simplified (proportional to |Papd|, not I²R)
3. No ESR, no switching dynamics, no current loop bandwidth

## Next Steps
- Send corrected results to GPT for final verification
- Update wiki with revised findings
- Commit all derivation-005 files
