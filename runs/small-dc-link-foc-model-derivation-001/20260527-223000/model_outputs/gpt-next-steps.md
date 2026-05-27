# GPT Next Steps — Post derivation-001 Plan

## Metadata

- Source: GPT (ChatGPT conversation 6a16bbf4)
- Date: 2026-05-27
- Context: After derivation-001 score 90/100

## Recommended Parallel Structure

### Main Line: derivation-002 — Energy Balance Envelope

**Goal**: Derive 22µF DC-Link energy balance under single-phase input.

**Core outputs**:
1. Single-phase input power model
2. DC-link capacitor energy equation
3. Vdc(t) or Vdc_min envelope
4. Pout_avg_ref(ω) upper limit
5. 100Hz power pulsation absorption demand
6. APD / mechanical inertia / derating branch judgment
7. Safe operating envelope

**Key formulas**:
```
E_c(t) = 1/2 Cdc Vdc(t)^2
dE_c/dt = Pin(t) - Pout(t)
Pin(t) ≈ Pavg · [1 - cos(2ωgrid t)]    # single-phase UPF approximation
Pout_avg(ωm) ≈ P0 + kωm³
```

**Critical question**: Given Cdc=22µF, Vdc_nom≈300V, Vdc_min_limit → what is max ΔE? What Pout_avg does this correspond to?

**Why energy-based**: Better than ΔV = I/(2fC) for large-ripple region because it doesn't assume small ripple.

### Parallel Line: Phase A — Core FOC Baseline

**Goal**: Build stable PMSM FOC baseline independent of 22µF strategy.

**Phase A scope**:
1. dq current loop
2. Clarke/Park transforms
3. SVPWM with real-time Vdc feedforward
4. Current limit
5. Speed loop (optional)
6. SMO/PLL observer baseline, mid-high speed first
7. Fixed-point feasibility checklist for TMS320F28035

**Explicitly NOT doing**:
1. No APD
2. No Pavg_ref power limiting strategy
3. No large-ripple closed loop
4. No 22µF final stability claims

**Acceptance criteria**: FOC runs stably on stable DC supply or existing 1360µF baseline.

**First task**: Design phase (Phase A-001), not code. Define interfaces, modules, acceptance signals.

### Critical Interface

**derivation-002 → Phase A / Phase C**:
```yaml
dc_link_constraints:
  Vdc_min_allowed:
  Vdc_max_allowed:
  ripple_pp_allowed:
  Pout_avg_max_by_speed:
  Iq_limit_by_vdc:
  derating_curve:
  observer_valid_region:
```

**Phase A → derivation-002**:
```yaml
foc_constraints:
  min_required_vdc_by_speed:
  max_iq:
  current_loop_bandwidth:
  observer_min_speed:
  voltage_saturation_margin:
  estimated_efficiency:
```

### Key Engineering Insight

The 22µF question is NOT "can SMO tolerate 18% ripple?" but rather:

**Who absorbs the 100Hz power deficit from single-phase input?**

Three candidates:
1. **Capacitor** — 22µF clearly insufficient for traditional stable bus
2. **Motor/pump mechanical system** — allow torque/speed 100Hz pulsation
3. **Active decoupling / front-end power control** — requires extra hardware or strong control

derivation-002 must quantify all three paths. Phase A only handles FOC foundation.

## Suggested Execution Order

1. Open `small-dc-link-foc-derivation-002` (energy balance envelope)
2. Simultaneously open `small-dc-link-foc-phase-a-001` (FOC baseline design)
