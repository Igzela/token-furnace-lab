# Task: derivation-004 — APD Sizing for 300W/22µF Single-Phase Drive

## Goal

Size the Active Power Decoupling (APD) branch to absorb 100Hz power pulsation in a 300W single-phase PMSM drive with 22µF DC-link.

## Context

derivation-001/002/003 established:
- 300W + 22µF + single-phase + mechanical inertia alone is infeasible
- Torque ripple is binding constraint (30% rated-torque ripple)
- APD is the required solution path (solution fork A)

## Deliverables

1. Energy calculation: ΔE_peak and ΔE_pp at 300W/50Hz
2. APD capacitor sizing: C_apd vs voltage swing table
3. APD topology comparison: H-bridge vs bidirectional buck-boost
4. APD peak power and current estimation
5. Decoupling target analysis: 80%, 90%, 95% reduction
6. Residual DC-link ripple after APD
7. Control architecture: power feedforward + voltage loop + current loop
8. Component stress: capacitor voltage rating, RMS current, inductor current

## Model Assignment

- **Claude Code**: Derive APD sizing, topology comparison, control architecture
- **GPT**: Verify formulas, check component stress, identify edge cases
