# Phase B-001: I-f Startup + Smooth FOC Transition

## Goal

Design and verify the I-f startup algorithm and smooth transition to sensorless FOC for TMS320F28035.

## Baseline

- FOC interface: complete (phase-a-002, 86/100)
- theta_source_mux: THETA_OPEN_LOOP / THETA_SENSORLESS / THETA_BLEND (defined in foc_interface_design.md)
- Motor: p=4, Rs=2Ω, Ls=5mH, ke=0.15 V/(rad/s), I_rated=3A, 4000rpm
- APD: 22µF/500V, 650V MOSFETs, 40kHz switching
- DC-link: 22µF, Vnom=300V
- Fixed-point: q15_t (I_base=5A, V_base=400V), omega_m_base=500 rad/s, omega_e_base=2000 rad/s

## Paper A1: Startup Strategy (arXiv 2503.22855)

### I-f Ramp Generation (eq.7-8)

```
ω_ref(k) = ω_ref(k-1) + Δω          (ramp)
θ(k) = θ(k-1) + ω_ref(k) × Ts       (angle integration)
```

Where:
- ω_ref: electrical angular velocity reference
- Δω: acceleration increment per step
- Ts: sample time

### Current Command in I-f Mode

```
Id_ref = 0                            (no flux building after alignment)
Iq_ref = I_start × min(1, t/T_ramp)   (ramp current to limit)
```

Or alternatively:
```
Id_ref = I_start × cos(β)
Iq_ref = I_start × sin(β)
```
Where β is the torque angle (typically 90° for max torque per amp).

### Virtual Synchronous Reference Frame

During I-f, the controller uses θ from the ramp generator (not observer):
- Clarke transform uses θ_ramp for α→d rotation
- Park transform uses θ_ramp for q-axis current control
- Observer is frozen or running in background for angle estimation

### Transition: I-f → Sensorless FOC

From paper A1, the transition strategy:

1. **Speed threshold**: Transition when ω_est ≥ ω_threshold (typically 5-10% of rated)
2. **Angle blending**: Blend θ_ramp and θ_observer during transition
   ```
   θ_blend = α × θ_observer + (1-α) × θ_ramp
   α = min(1, (ω_est - ω_start) / (ω_end - ω_start))
   ```
3. **Current reference handoff**: Switch from Iq_ref (I-f) to speed PI output
4. **Observer activation**: Start observer before transition, validate convergence

### Alignment Phase (Pre-startup)

Before I-f ramp:
1. Apply DC current to align rotor to known position
2. Id_ref = I_align (e.g., 0.5×I_rated) for T_align (e.g., 100ms)
3. Hold angle θ_align = 0 (or known position)
4. Then begin I-f ramp

## Required Outputs

1. **I-f ramp generator**: Δω vs acceleration time, ω vs time profile
2. **Alignment procedure**: I_align, T_align, angle
3. **Transition logic**: Speed threshold, angle blending formula, current handoff
4. **Fixed-point implementation**: All variables in q15_t/q12_t/angle_t, overflow protection
5. **Simulation model**: Python model of startup sequence (alignment → I-f → transition → FOC)
6. **Parameter sweep**: Sweep Δω, I_start, transition speed, blend rate
7. **Stability assessment**: What causes instability during transition?

## Key Questions to Answer

1. How fast can we ramp? (Δω limits from voltage/current constraints)
2. What is the minimum transition speed for observer lock?
3. How to handle the current transient at transition?
4. What happens if observer angle is wrong at transition? (angle error tolerance)
5. How does 22µF DC-link affect startup? (voltage sag during current ramp)
