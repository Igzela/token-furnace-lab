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
2. ~~**22µF ripple model**: Papers assume large capacitance~~ → **RESOLVED** (derivation-001+002): energy-based model shows 22µF feasible at 300W with 50%pp Vdc swing, but torque ripple limits to ~170W
3. ~~**Torque ripple coupling~~ → **PARTIALLY RESOLVED** (derivation-002): speed ripple <0.5% OK, but torque ripple = 100% at full power (binding constraint). GPT final: constraint is "T_ripple < 30% × T_rated" (not T_avg)
4. ~~**Sensorless FOC under large ripple**: Robustness assessment needed~~ → **RESOLVED** (derivation-001): <10%pp conservative, 10-20%pp attemptable with Vdc feedforward
5. **Input topology**: Single-phase or three-phase? — must be confirmed before proceeding
6. **APD energy buffer sizing**: ~~APD not required if J is sufficient~~ → **REVISED** (derivation-002): APD required for 300W → **RESOLVED** (derivation-004): 16µF/500V H-bridge, 90% decoupling, enables 300W → **RESOLVED** (derivation-005): 300W achievable with 22µF+APD, 66/162 configs pass, best 2.3%pp ripple
7. **FOC baseline validation**: Phase A design complete, needs implementation and hardware test
8. ~~**Low-line 4 missing checks** (GPT final)~~ → **RESOLVED** (derivation-003): Vreq(speed,Iq) derived, Iq_max quadratic solved, max speed table, high-line overvoltage checked
9. **ψ_f must be ≤ 0.103** for 300V/4000rpm (revised from 0.15 to 0.08)
10. **300W requires ≥6632rpm** under 30% rated-torque ripple limit (66% above rated speed)

## Experiment Progress

| ID | Type | Status | Score | Key Finding |
|----|------|--------|-------|-------------|
| derivation-001 | ripple model | COMPLETE | 90/100 | Single-phase infeasible as stable bus |
| derivation-002 | energy balance | COMPLETE | 85/100 | Torque ripple binding, 300W needs APD, GPT final: rated-torque distinction |
| derivation-003 | FOC voltage envelope | COMPLETE | 82/100 | ψ_f≤0.103, 300W needs ≥6632rpm, high-line 240W limit |
| derivation-004 | APD sizing | COMPLETE | 78/100 | 16µF/500V H-bridge, 90% decoupling enables 300W |
| derivation-005 | joint simulation | COMPLETE | 86/100 | GPT final: PASS_WITH_NOTES. 300W conditionally feasible (44% pass). Recommended baseline: 22µF+22µF/500V APD, robust=200W, stretch=300W |
| derivation-006 | APD HW sizing | COMPLETE | 84/100 | 650V MOSFET sufficient (Case A), 1.5-6.8mH inductor, 3-6W total APD loss |
| phase-a-001 | FOC design | COMPLETE | - | F28035 budget OK, modules defined |
| phase-a-002 | FOC interface | COMPLETE | 86/100 | GPT PASS_WITH_NOTES. v3: theta mux, IqLimiter, split omega scaling, applied voltage SMO |
| phase-a-003 | FOC hw test | PENDING | - | Next: validate on 1360µF hardware |
| phase-b-001 | I-f startup | COMPLETE | 76/100 | GPT PASS_WITH_NOTES. 168/216 pass. Observer model weak, ke/ψf unresolved, blend needs gating |
| phase-b-002 | I-f startup corrected | COMPLETE | 82/100 | GPT PASS_WITH_NOTES. All B-001 corrections applied. 252/252 pass. ψ_f=0.08Wb, expanded observer, observer-gated blend |
| phase-b-003 | Three-threshold blend | COMPLETE | 90/100 | GPT PASS. Three-threshold blend + anti-chatter. 189/189 pass (100%), max blend error 5°, implementation-ready |
| phase-b-004 | State machine impl spec | COMPLETE | 78/100 | GPT PASS_WITH_NOTES. 7 states, gated transitions, 2KB trace, angle_t, 15 faults, retry escalation. Corrected trace RAM and angle type |
| phase-c-001 | DC-link ripple mgmt | COMPLETE | 82/100 | GPT PASS_WITH_NOTES. 22µF+90% APD not robust across medium-load. 48/192 pass (25%). Don't conclude three-phase required yet |
| phase-c-002 | 1ph vs 3ph comparison | COMPLETE | 88/100 | GPT PASS_WITH_NOTES. DC-link feasibility closed. 269/288 pass (93.4%). Three-phase 22µF no APD, single-phase needs 90% APD |

## References

- A1: arXiv 2503.22855
- A2: arXiv 2305.04046
- A3: arXiv 1901.10020
- E1: derivation-001 — Pavg_ref + ripple model (score 90/100, PASS)
- E2: derivation-002 — Energy balance envelope (score 85/100, PASS_WITH_NOTES)
- E2-final: derivation-002 GPT final verification — rated-torque distinction, low-line 4 gaps, derivation-003 recommended
- E3: derivation-003 — FOC voltage/saturation envelope (score 82/100, PASS_WITH_NOTES)
- E3-final: derivation-003 GPT verification — all formulas pass, solution fork recommended
- E4: derivation-004 — APD sizing (score 78/100, PASS_WITH_TWO_CORRECTIONS)
- E4-final: derivation-004 GPT verification — C_apd factor-of-2 correction, torque ripple conclusion corrected
- E5: phase-a-001 — FOC baseline design (COMPLETE)
- E5b: derivation-005 — Joint simulation (86/100 PASS_WITH_NOTES, COMPLETE)
- E5b-final: GPT final verification — PASS_WITH_NOTES, 300W conditionally feasible, recommended baseline 22µF+22µF/500V APD
- E6: derivation-006 — APD hardware sizing (84/100 PASS_WITH_NOTES, COMPLETE): 650V MOSFET (Case A unipolar), 1.56mH inductor, 3.65W loss, 160 configs swept
- E7: phase-b-001 — I-f startup + FOC transition (76/100 PASS_WITH_NOTES, COMPLETE): 168/216 configs pass, 300ms startup, observer model needs expansion, ke/ψf convention unresolved
- E8: phase-b-002 — Corrected I-f startup (82/100 PASS_WITH_NOTES, COMPLETE): All B-001 corrections applied, ψ_f=0.08Wb, expanded observer, 252/252 pass, 35.5° max error needs three thresholds
- E9: phase-b-003 — Three-threshold blend + anti-chatter (90/100 PASS, COMPLETE): 189/189 pass, max blend error 5°, implementation-ready state machine with logging and fallback profiles
- E10: phase-b-004 — State machine implementation spec (78/100 PASS_WITH_NOTES, COMPLETE): C header+impl, 2KB trace, angle_t, 15 faults, retry escalation. GPT corrected trace RAM (56KB→2KB) and angle type
- E11: phase-c-001 — DC-link ripple management (82/100 PASS_WITH_NOTES, COMPLETE): 22µF+90% APD not robust across medium-load, 48/192 pass. GPT: don't conclude three-phase required yet, explore adaptive APD and capacitance threshold
- E12: phase-c-002 — Single-phase vs three-phase comparison (88/100 PASS_WITH_NOTES, COMPLETE): DC-link feasibility closed. 269/288 pass. Three-phase 22µF works without APD, single-phase needs 90% APD
