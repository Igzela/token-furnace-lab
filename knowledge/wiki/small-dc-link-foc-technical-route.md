# Small DC-Link FOC Technical Route

## Overview

Technical roadmap for 22µF DC-link + sensorless FOC + water pump + TMS320F28035.

## Source Papers

| Paper | Role | Key Contribution |
|-------|------|------------------|
| A1: 2503.22855 | Startup strategy | 3-step I-f → sensorless FOC transition |
| A2: 2305.04046 | Sensorless FOC | SMO observer, speed/current PI |
| A3: 1901.10020 | DC-link ripple | Harmonic observer concept |

## Technical Phases

### Phase A: Core FOC (from A2)

**Goal**: Implement SMO-based sensorless FOC on TMS320F28035

**Components**:
- SMO observer (eq.6-9)
- Speed PI with active damping (eq.16-17)
- Current PI with feed-forward decoupling (eq.21)
- Clarke/Park transforms

**Feasibility**: PASS — all operations fit F28035 fixed-point budget

**Key parameters**:
- SMO gain k = 145 (tune for fixed-point)
- LPF cutoff ~30 kHz (adjust for 10-20 kHz PWM)
- Speed PI: Kpm=0.004, Kim=2
- Current PI: Kpd=120.54, Kid=70440

### Phase B: Startup (from A1)

**Goal**: Implement I-f startup with smooth transition to sensorless FOC

**Components**:
- I-f ramp generation (eq.7-8)
- Virtual synchronous reference frame
- Compressor alignment
- Error compensation (eq.11-12)

**Feasibility**: PASS — direct transfer from CSI to VSI with minor adaptation

**Adaptation**: Change current control from CSI (DC link current) to VSI (phase currents)

### Phase C: DC-Link Management (from A3 + custom)

**Goal**: Manage 22µF DC-link voltage ripple

**Components**:
- 22µF ripple model (CUSTOM — not in any paper)
- Pavg_ref calculation (CUSTOM — not in any paper)
- Reduced-order harmonic observer (adapted from A3)
- Ripple-aware current control

**Feasibility**: CONDITIONAL — derived in model-derivation-001, verified by GPT

**Derivation Results** (experiment 001, score 90/100):
- Single-phase + 22µF + 360W: **INFEASIBLE** (ΔV = 545V > V_dc = 300V)
- Three-phase + 22µF + 360W: **MARGINAL** (ΔV = 182V, 61%pp)
- With APD (20dB): feasible if real energy buffer exists
- Pavg_ref = P₀ + k·ω³ (not just k·ω³/η — GPT refinement)
- SMO tolerance: <10%pp conservative, 10-20%pp attemptable with Vdc feedforward

**Risks**:
1. A3's 7th-order observer too heavy for F28035 → reduce to 3rd or 5th order
2. Single-phase input requires APD with real energy buffer (extra capacitor/inductor)
3. Minimum bus voltage (Vdc_min = Vdc_avg - ΔVpp/2) may cause voltage saturation before SMO fails

### Phase D: Integration & Testing

**Goal**: Combine all components and validate

**Steps**:
1. Combined simulation (Matlab/Simulink)
2. F28035 code generation (CCS)
3. Hardware-in-loop testing
4. Experimental validation on 22µF hardware

## Critical Gaps

1. ~~**Pavg_ref**: Power reference calculation method not in any paper~~ → **RESOLVED** (derivation-001): P_avg_ref = P₀ + k·ω³
2. ~~**22µF ripple model**: Papers assume large capacitance~~ → **RESOLVED** (derivation-001): single-phase infeasible, three-phase marginal
3. **Torque ripple coupling**: Voltage ripple → current → torque chain — still open
4. ~~**Sensorless FOC under large ripple**: Robustness assessment needed~~ → **RESOLVED** (derivation-001): <10%pp conservative, 10-20%pp attemptable with Vdc feedforward
5. **Input topology**: Single-phase or three-phase? — must be confirmed before proceeding
6. **APD energy buffer sizing**: If single-phase, what hardware is needed for 0.57J buffer?

## References

- A1: arXiv 2503.22855
- A2: arXiv 2305.04046
- A3: arXiv 1901.10020
- E1: small-dc-link-foc-model-derivation-001 — Pavg_ref + ripple model derivation (score 90/100, PASS)
