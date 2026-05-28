# Phase C-001: DC-Link Voltage Ripple Management

## Goal

Design the DC-link voltage ripple management system for 22µF capacitor + APD, building on derivation-001/002/005 results.

## Known Results (from derivations)

- **derivation-001**: Single-phase infeasible as stable bus. Three-phase marginal (ΔV=182V, 61%pp)
- **derivation-002**: Torque ripple binding at full power. 300W needs APD.
- **derivation-005**: 300W conditionally feasible (44% pass). Best: 22µF+22µF/500V APD, 2.3%pp ripple
- **derivation-006**: APD hardware: 650V MOSFET, 1.56mH inductor, 3.65W loss

## Design Tasks

1. **Vdc feedforward model**: How to estimate Vdc ripple from P_avg and ω
2. **Pavg_ref calculation**: P₀ + k·ω³ (from derivation-001)
3. **APD control strategy**: How APD actively decouples ripple
4. **Vdc limits for SMO**: Map Vdc_min/Max to observer stability
5. **IqLimiter interaction**: How Vdc variation limits Iq command
6. **SVPWM saturation handling**: Overmodulation when Vdc dips

## Required Outputs

1. DC-link voltage model (ripple equation + APD decoupling)
2. Vdc feedforward for SMO observer
3. IqLimiter design (Vdc-aware)
4. SVPWM saturation strategy
5. Integration with startup state machine (B-004)
6. GPT review
