# GPT — Implementation Feasibility Assessment (002)

## Scope

```yaml
experiment: pdf-to-algorithm-benchmark-002
input_basis: Claude Code deep formula extraction (002)
target_platform: TMS320F28035
target_scenario: 22µF DC-link + sensorless FOC + water pump + VSI
```

---

## TMS320F28035 Platform Constraints

| Resource | Spec |
|----------|------|
| Clock | 60 MHz |
| Architecture | Fixed-point (CLA available) |
| Flash | 64 KB |
| RAM | 12 KB |
| PWM | Up to 14 channels |
| ADC | 12-bit, up to 16 channels |
| Typical PWM freq | 10-20 kHz |
| Current loop rate | 5-10 kHz |

**Critical constraint**: Fixed-point arithmetic. Floating-point operations are emulated and ~10x slower.

---

## A1: Sensorless FOC Startup — Feasibility

### Computational Analysis

| Operation | Complexity | Fixed-Point Feasibility |
|-----------|------------|------------------------|
| Clarke/Park transform | 6 multiplies, 2 adds | ✓ Easy |
| PLL tracking | PI controller + integration | ✓ Standard |
| Error compensation (eq.11-12) | 4 multiplies, 2 trig | ✓ Moderate (arctan needs lookup) |
| I-f ramp generation | 1 multiply, 1 integrate | ✓ Easy |
| SVM | Sector calculation + switching | ✓ Standard |

**Estimated cycle time**: ~15-20 µs (within 50 µs budget at 10 kHz)

### MCU Feasibility: **PASS**

- All operations are standard FOC building blocks
- Fixed-point implementations well-documented
- TMS320F28388D (used in paper) is superset of F28035

### Adaptation Required for VSI

| Aspect | CSI (Paper) | VSI (Target) | Adaptation |
|--------|-------------|--------------|------------|
| Current control | DC link current | Phase currents | Change current loop |
| Voltage modulation | SVM for CSI | SVM for VSI | Different switching |
| DC-link | Constant current source | Voltage source | Add voltage loop |
| Startup | I-f with CSI | I-f with VSI | Minor adaptation |

### Verdict: **USABLE WITH ADAPTATION**

The 3-step startup strategy is directly transferable to VSI. Main change: current control loop structure.

---

## A2: SMO Sensorless FOC — Feasibility

### Computational Analysis

| Operation | Complexity | Fixed-Point Feasibility |
|-----------|------------|------------------------|
| SMO switching (eq.6) | 2 sign operations | ✓ Easy |
| LPF (eq.8) | 2 first-order filters | ✓ Easy |
| arctan (eq.9) | Lookup table or CORDIC | ✓ Moderate |
| Speed PI (eq.16) | PI + active damping | ✓ Standard |
| Current PI (eq.21) | PI + decoupling | ✓ Standard |
| Clarke/Park | Standard | ✓ Easy |

**Estimated cycle time**: ~20-25 µs (within budget)

### MCU Feasibility: **PASS**

- SMO is simpler than EKF or other observers
- Fixed-point arctan via lookup table (256 entries = 1KB Flash)
- PI controllers are standard fixed-point

### Key Parameters for F28035

| Parameter | Paper Value | F28035 Adaptation |
|-----------|-------------|-------------------|
| SMO gain k | 145 | Tune for fixed-point |
| LPF cutoff | 30 kHz | Adjust for 10-20 kHz PWM |
| Speed PI Kpm | 0.004 | Scale for fixed-point |
| Speed PI Kim | 2 | Scale for fixed-point |
| Current PI Kpd | 120.54 | Scale for fixed-point |
| Current PI Kid | 70440 | Scale for fixed-point |

### Fixed-Point Scaling

```
// Example: Kpm = 0.004 in Q16 format
// Q16: value * 65536
Kpm_q16 = 0.004 * 65536 = 262 (fits in int16)

// Example: Kid = 70440
// Too large for int16, use Q8 or split
Kid_q8 = 70440 / 256 = 275 (fits in int16)
// Or use int32 accumulator
```

### Verdict: **USABLE**

SMO is a good choice for F28035. Simpler than EKF, robust, well-understood.

---

## A3: DC-Link Harmonic Observer — Feasibility

### Computational Analysis

| Operation | Complexity | Fixed-Point Feasibility |
|-----------|------------|------------------------|
| 7×7 matrix multiply (eq.24) | 49 multiplies, 42 adds | ⚠️ Heavy |
| Observer update (eq.25) | 7×7 + 7×1 | ⚠️ Heavy |
| Harmonic feedback (eq.29) | 6 multiplies, 6 adds | ✓ Easy |
| Discretized S_d | Pre-computed | ✓ Offline |

**Estimated cycle time**: ~30-40 µs (marginal at 10 kHz)

### MCU Feasibility: **WARNING**

- 7×7 matrix multiply is computationally expensive
- At 18 kHz sampling (paper), needs ~55 µs per cycle
- At 10 kHz PWM on F28035, budget is 100 µs — feasible but tight
- Fixed-point 7×7 multiply: 49 multiplications × ~10 cycles = ~490 cycles = ~8 µs at 60 MHz

### Optimization Options

1. **Reduce observer order**: Use 3rd or 5th order instead of 7th
2. **Use CLA**: Offload observer to Control Law Accelerator
3. **Pre-compute S_d**: Store as constants, only update z
4. **Reduce sampling**: Run observer at half PWM rate

### Verdict: **MARGINAL — REQUIRES OPTIMIZATION**

The 7th-order observer is too heavy for standard F28035 implementation. Need to either:
- Reduce to 5th order (ignore 3rd harmonic)
- Use CLA for parallel execution
- Run at reduced rate

---

## Project Mapping: 22µF DC-Link + Sensorless FOC + Pump

### Which Fragments Apply

| Algorithm Fragment | Source | Applicability | Adaptation Needed |
|--------------------|--------|---------------|-------------------|
| I-f startup | A1 | HIGH | Change CSI→VSI current control |
| Smooth transition | A1 | HIGH | Direct transfer |
| Error compensation | A1 | HIGH | Direct transfer |
| SMO observer | A2 | HIGH | Tune for F28035 fixed-point |
| Speed PI + damping | A2 | HIGH | Standard fixed-point |
| Current PI + decoupling | A2 | HIGH | Standard fixed-point |
| DC-link harmonic model | A3 | MEDIUM | Reduce order, adapt topology |
| Harmonic feedback | A3 | MEDIUM | Simplify for VSI |

### What Must Be Custom-Derived

1. **Pavg_ref calculation**: Not found in any paper. Need to derive from power balance:
   $$P_{avg} = \frac{1}{T}\int_0^T v_{dc}(t) \cdot i_{dc}(t) dt$$

2. **22µF DC-link voltage ripple model**: Papers assume large capacitance. Need to model:
   $$\Delta v_{dc} = \frac{\Delta Q}{C} = \frac{1}{C}\int i_{dc}(t) dt$$
   With C = 22µF, ripple will be significant.

3. **Torque ripple coupling**: Small DC-link → voltage ripple → current distortion → torque ripple. Need to model this chain.

4. **Sensorless FOC under large voltage ripple**: SMO assumes relatively stable DC-link. Need to assess robustness.

### Recommended Technical Roadmap

```
Phase A: Core FOC (from A2)
  ├── SMO observer on F28035
  ├── Speed PI with active damping
  ├── Current PI with decoupling
  └── Clarke/Park transforms

Phase B: Startup (from A1)
  ├── I-f startup for VSI
  ├── Smooth transition to sensorless FOC
  └── Error compensation

Phase C: DC-Link Management (from A3, custom)
  ├── 22µF ripple model
  ├── Pavg_ref calculation
  ├── Harmonic observer (reduced order)
  └── Ripple-aware current control

Phase D: Integration & Testing
  ├── Combined simulation
  ├── F28035 code generation
  ├── Hardware-in-loop testing
  └── Experimental validation
```

---

## Extraction Quality Report

```yaml
evidence_depth:
  score: 27/30
  reason: All equations have page numbers, figure numbers, and variable definitions

implementability:
  score: 24/30
  reason: Pseudocode generated for all 3 papers, MCU feasibility assessed

project_mapping:
  score: 22/25
  reason: Clear fragment mapping, custom derivation gaps identified

gap_identification:
  score: 13/15
  reason: Pavg_ref, 22µF ripple model, torque ripple coupling identified

total_score: 86/100
verdict: PASS
```

## Conclusion

Phase 4 Run 002 achieves PASS. The deep extraction provides:
1. Full equations with page-level evidence
2. Pseudocode for all 3 algorithms
3. MCU feasibility assessment for TMS320F28035
4. Clear project mapping with adaptation requirements
5. Identified gaps requiring custom derivation

**Key finding**: A1 (startup) and A2 (SMO FOC) are directly usable. A3 (harmonic observer) needs significant simplification. The critical missing piece is Pavg_ref calculation and 22µF ripple modeling, which require custom derivation.
