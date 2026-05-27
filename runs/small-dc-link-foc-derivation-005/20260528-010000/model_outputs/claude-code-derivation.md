# derivation-005: FOC + APD + 22µF Joint Dynamic Simulation (REVISED)

## Model Description

Energy-balance simulation of coupled DC-link, APD, FOC voltage saturation, and motor torque.

### Components
1. **Input**: Single-phase rectified: Pin(t) = Pavg · [1 - cos(2ω_grid t)]
2. **DC-link**: dE_dc/dt = Pin - Pmotor_elec - Papd, E_dc = 0.5·Cdc·Vdc²
3. **APD**: dE_apd/dt = Papd - Ploss, Vapd = √(2·E_apd/Capd), clamped to voltage window
4. **APD power command**: Papd = -D·Pavg·cos(2ωt) (absorb when Pin > Pavg, source when Pin < Pavg)
5. **FOC voltage limit**: Vlim = m·Vdc/√3, Vmargin = Vlim - ωe·ψf
6. **Iq from electrical power command**: Quadratic solution of Pavg = 1.5·(Rs·Iq + ωe·ψf)·Iq
7. **Electrical power**: Pmotor_elec = 1.5·Vq·Iq (3-phase, includes copper losses)
8. **Motor torque**: Te = Kt·Iq where Kt = 1.5·p·ψf

### Parameters
- Motor: p=2, Rs=0.5Ω, Ls=1.5mH, ψf=0.08Wb, I_rated=3A
- DC-link: Cdc=22µF, Vnom=300V
- APD: Capd=16µF, D=0.90, Vapd window=250-450V
- Speed: 4000rpm (ω=418.9 rad/s, ωe=837.8 rad/s)

### Model Corrections (after GPT verification)
1. **Electrical power**: Changed from Pmotor = Te·ω (mechanical) to Pmotor = 1.5·Vq·Iq (electrical, 3-phase)
2. **Iq computation**: Changed from fixed I_rated to quadratic solution from power command
3. **APD initial condition**: Changed from voltage midpoint to energy center: Vapd_center = √((Vmin²+Vmax²)/2)

## Verification: Ideal APD

With D=1.0 and unlimited APD voltage window:
- Vdc = 300.0V, 0.0%pp ripple
- Pmotor = 300.0W (exact match to Pavg)
- **Model is correct for ideal case** ✓

## Key Finding: APD Clamping Asymmetry Limits Power Transfer

### Updated Root Cause

The Vdc collapse is NOT due to APD energy storage insufficiency (16µF/250-450V has 1.12J, needs 0.955J for 100% decoupling). It's due to **APD voltage window clamping asymmetry**:

1. During absorption (Pin > Pavg): APD absorbs power until hitting Vapd_max (450V). Excess power goes to DC-link → Vdc rises
2. During release (Pin < Pavg): APD releases from lower energy state, can't release full commanded power → DC-link must supply deficit → Vdc drops
3. Net effect: APD gains ~4.7W average (should be ~0), DC-link loses ~1.9W average → Vdc collapses

This is a real physical effect: the APD's finite voltage window creates asymmetric energy flow that drains the DC-link.

### Simulation Results (Corrected)

| Config | Vdc avg | Vdc ripple | Torque ripple | Vapd | Pass? |
|--------|---------|------------|---------------|------|-------|
| 22µF, D=0.90, 16µF APD | 142V | 35.3%pp | 23.1% | 250-410V | FAIL |
| 22µF, D=0.95, 16µF APD | 133V | 17.1%pp | 25.1% | 250-408V | FAIL |
| 22µF, no APD | 234V | 87.9%pp | — | — | FAIL |
| 22µF, D=1.0, ideal APD | 300V | 0.0%pp | 0.0% | unlimited | PASS |
| 470µF, no APD | 297V | 3.2%pp | — | — | PASS |
| 100W, 22µF, D=0.9, 22µF APD | ~237V | 2.6%pp | — | — | PASS |

### Sweep Results
- **0/162** 300W configs pass (all fail due to APD clamping asymmetry)
- **62/324** 100W configs pass (lower power reduces clamping severity)
- **0/486** total pass for 200W and 300W

### Comparison: Analytical vs Simulation

| Metric | Analytical (derivation-004) | Simulation (derivation-005) |
|--------|---------------------------|---------------------------|
| APD energy sufficient? | Yes (16µF/250-450V: 1.12J > 0.955J) | Yes, but clamping limits实际transfer |
| 90% decoupling achievable? | Yes (residual 4.8%pp) | No (Vdc collapses) |
| 300W feasible with 22µF? | Yes (with 16µF APD) | No (clamping asymmetry) |
| Binding constraint | Voltage ripple | APD clamping asymmetry |

The analytical model assumes ideal APD power source (unlimited voltage swing). The simulation reveals that finite voltage window creates asymmetric energy flow that the analytical model cannot capture.

## Implications

1. **300W with 22µF DC-link is NOT achievable** with practical APD (16-47µF, 250-450V window)
2. **100W is achievable** with 22µF + APD (62 passing configs)
3. **Solution fork needs revision**: Path A (22µF + APD) works for ≤100W but not 300W
4. **Path B (larger Cdc)**: 470µF works without APD (3.2%pp ripple)

## Recommended Next Steps

1. **Accept 100W target** with 22µF + APD, OR
2. **Increase Cdc to ≥470µF** for 300W (abandon APD approach), OR
3. **Wider APD voltage** (100-500V) or **larger APD cap** (≥50µF) for 300W — needs further simulation
4. **Send corrected results to GPT** for final verification
