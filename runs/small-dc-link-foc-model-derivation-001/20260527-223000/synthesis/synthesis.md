# Synthesis — Small DC-Link FOC Model Derivation Run 001

## Metadata

- Experiment: small-dc-link-foc-model-derivation-001
- Date: 2026-05-27
- Status: COMPLETE
- Models: Claude Code (derivation), GPT (verification)

## Experiment Verdict

```yaml
experiment_verdict: COMPLETE
derivation_verdict: PASS
verification_verdict: PASS_WITH_REFINEMENTS
```

## Score

| Dimension | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Mathematical correctness | 35 | 32/35 | Formulas correct, arithmetic verified, small-ripple collapse identified |
| Engineering practicality | 30 | 26/30 | Good feasibility matrix, GPT adds energy buffer analysis |
| Completeness | 20 | 18/20 | All 5 objectives addressed; Pavg_ref refinement needed |
| Evidence quality | 15 | 14/15 | Assumptions stated, derivations traceable, dual-model audit |
| **Total** | | **90/100** | **PASS** |

## Key Findings

### Dual-Model Agreement

Both Claude Code and GPT agree on:
1. Single-phase 22µF at 360W is physically infeasible as stable DC bus
2. Ripple formulas are mathematically correct but collapse when ΔV > V_dc
3. Pump P ∝ ω³ is valid first-order model
4. Three-phase is better but still problematic at 22µF / 360W
5. Active power decoupling is possible but requires real energy buffer

### GPT Refinements (not in Claude Code derivation)

1. **Pavg_ref should include loss offset**: P_avg_ref(ω) = P₀ + k·ω³, not just k·ω³/η. P₀ covers friction, iron losses, controller losses.

2. **Energy buffer analysis**: For 360W single-phase, E_buf ≈ 0.57J but E_usable ≈ 0.099J. Deficit of ~6x. APD cannot work without real energy path (extra capacitor, PFC, mechanical inertia, or power limiting).

3. **Linear division warning**: Cannot apply 20dB reduction (÷10) to 545V because formula is already in failure zone. More accurate: "tens of volts" bus ripple after APD.

4. **Vdc_min is more critical than SMO robustness**: If minimum bus voltage drops below required back-EMF, current loop saturates before SMO fails.

5. **SMO ripple tolerance grading**: <10%pp conservative, 10-20%pp attemptable with care, 20-30%pp high risk, >30%pp not recommended.

### Critical Engineering Conclusion

The system as specified (22µF + single-phase + 360W) is physically infeasible as a stable DC bus. The viable configurations are:

| Configuration | Feasibility | Required Changes |
|---------------|-------------|-----------------|
| Single-phase + passive rectification | INFEASIBLE | Would need C ≥ 400µF |
| Single-phase + APD | MARGINAL (18%pp) | Extra energy buffer, real-time Vdc sampling, power limiting |
| Three-phase + passive rectification | MARGINAL (61%pp at full load) | Better but still needs control work |
| Three-phase + APD | FEASIBLE (6%pp) | Most practical path |
| Any topology + power derating | FEASIBLE | Limit to ~20W for 22µF without APD |

## Deliverables Completed

- [x] Pavg_ref derivation (3 methods) + GPT refinement (P₀ offset)
- [x] 22µF ripple model (analytical) + GPT energy buffer analysis
- [x] Ripple magnitude table (vs speed/load, single-phase + three-phase)
- [x] Sensorless FOC robustness assessment + GPT ripple tolerance grading
- [x] Design rules for capacitor selection

## Knowledge Impact

### Wiki Updates Required

- `small-dc-link-foc-technical-route.md`: Update Phase C feasibility from MARGINAL to CONDITIONAL — requires three-phase input OR active power decoupling with real energy buffer

### New Rules

1. **Formula validity range**: When a derived value exceeds the variable it's derived from (ΔV > V_dc), the formula's assumptions have collapsed. The collapse itself is engineering-significant — it proves the configuration is physically infeasible under stated assumptions.

2. **Energy conservation in APD**: Active power decoupling cannot eliminate ripple without a real energy path. Software alone cannot remove 100Hz energy from a single-phase system.

3. **Pavg_ref practical form**: For centrifugal pumps, use P_avg_ref = P₀ + k·ω³ rather than P_avg_ref = k·ω³/η. The P₀ term captures losses that dominate at low speed.

## Next Experiment

The derivation confirms the 22µF constraint fundamentally changes the system architecture. Next steps:

1. **Confirm input topology**: Single-phase or three-phase? This determines whether 22µF is viable at all.
2. **If three-phase**: Proceed to implementation with reduced ripple expectations
3. **If single-phase**: Must budget for APD hardware + energy buffer, or accept power derating
4. **Proceed with core FOC** (Phase A from A2) regardless — topology-independent
