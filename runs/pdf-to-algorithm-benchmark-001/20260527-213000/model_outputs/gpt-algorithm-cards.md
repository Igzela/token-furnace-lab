# GPT Algorithm Card Extraction

## Scope

```yaml
experiment: pdf-to-algorithm-benchmark-001
corpus_source: public_arxiv_seed
benchmark_scope: pipeline_validation
input_basis: Claude Code PDF reader output
papers:
  - A1: Sensorless FOC / CSI-fed PMSM / submersible pump
  - A2: SMO sensorless vector control / PMSM
  - A3: DC-link ripple / harmonics feedback / boost converter
```

**Important limitation**: this extraction is based on Claude Code's extracted titles, abstracts, equation lists, figure descriptions, algorithm summaries, and experiment summaries. It is good enough for structured algorithm cards, comparison, and relevance ranking, but not yet enough for final engineering implementation.

---

## Algorithm Card A1

### Paper

```yaml
paper_id: A1
title: Sensorless Field Oriented Control of CSI-Fed PMSM Drives Used in Submersible Pumps
arxiv: 2503.22855
role: main_application_algorithm
category: P1
pages: 8
text_extractable: yes
```

### Problem

This paper addresses sensorless startup and transition to sensorless FOC for CSI-fed PMSM drives used in submersible pump applications. The main engineering issue is the transition from open-loop or I-f startup into sensorless FOC without large speed/current oscillations or complex alignment-error calculation. The paper is directly relevant to pump motor startup and sensorless FOC, but its topology is CSI-fed PMSM, not the user's likely small-DC-link VSI water-pump inverter.

### Core Algorithm

```yaml
algorithm_name: Three-step sensorless startup and transition strategy
control_type: sensorless FOC startup transition
motor_type: PMSM
power_stage: current source inverter
main_components:
  - I-f startup
  - virtual synchronous reference frame
  - PLL observer
  - compressor alignment stage
  - error compensation strategy
```

**Terminal 1**: I-f startup. The motor starts from standstill with controlled acceleration. The q-axis current reference is constant, d-axis current is zero, and the reference angle is obtained by integrating a ramp speed command.

**Terminal 2**: Compressor alignment. At about 300 rpm, the system reduces the error between the estimated frame and the virtual reference frame.

**Terminal 3**: Error compensation. Initial position error introduced during transition is reduced using estimated d/q-axis voltage relations and a compensation factor.

### Key Equations

```yaml
stationary_frame_model:
  - alpha-axis voltage equation (eq.1)
  - beta-axis voltage equation (eq.2)
  - alpha/beta back-EMF model (eq.3-4)

dq_frame_model:
  - d-axis voltage equation (eq.5)
  - q-axis voltage equation (eq.6)

startup_reference:
  - theta_e* = integral of omega_e* (eq.7)
  - omega_e* = K_omega * t (eq.8)

error_compensation:
  - estimated q-axis voltage (eq.11)
  - estimated d-axis voltage (eq.12)
```

Equations (1)–(6) describe αβ and dq PMSM voltage/back-EMF relationships. Equations (7)–(10) describe ramp-speed reference angle and current transformations. Equations (11)–(12) provide estimated q/d-axis voltage terms used in error compensation.

### Implementation Details

```yaml
required_sensors:
  - phase current sensing
  - voltage/current information for sensorless observer
  - encoder only for experimental comparison
requires_encoder_for_control: no
controller_platform: TMS320F28388D
special_hardware:
  - CSI-fed PMSM drive
  - 1.8 km long cable in experiment
```

### System Parameters

```yaml
R_s: 2.16 ohm
L_s: 4.56 mH
R_c: 11.76 ohm
L_c: 9.7 mH
C_c: 111 nF
P: 6 pole pairs
V_g: 480 V
f_g: 60 Hz
L_dc: 10 mH
C_o: 50 uF
```

### Experimental Results

- Speed oscillation: ~11 rpm
- Current oscillation: 0.09 A during transition
- Terminal 1→2 at t=3s, Terminal 2→3 at t=3.5s
- Acceleration to 300 rpm stable

### Applicability

```yaml
works_when:
  - CSI-fed PMSM drive
  - submersible pump
  - long cable
  - medium-to-high speed range

fails_or_weak_when:
  - very low speed, because back-EMF is too low
  - VSI topology without adaptation
  - high speed with dead-time effects
  - significant cable impedance effects

assumptions:
  - surface-mounted PMSM
  - known motor parameters
  - 60 Hz grid
```

### Relevance

```yaml
relevance_to_22uF_small_dc_link_water_pump: medium_high
sensorless_foc_relevance: high
small_dc_link_relevance: low
pump_application_relevance: high
implementation_relevance: medium
```

Most useful: Three-stage startup strategy, smooth transition from I-f to sensorless FOC, error compensation method.

Not directly solved: 22µF DC-link constraint, DC-link power ripple suppression, VSI-specific implementation, Pavg_ref calculation.

### Extraction Quality

```yaml
accuracy_risk: low
completeness: medium_high
implementability_signal: high
evidence_quality: high
project_relevance: high_for_startup_sensorless_foc
```

---

## Algorithm Card A2

### Paper

```yaml
paper_id: A2
title: Simulation of non-inductive vector control of PMSM based on sliding mode observer
arxiv: 2305.04046
role: sensorless_control_algorithm
category: P2
pages: 8
text_extractable: yes
```

### Problem

This paper builds a PMSM sensorless vector-control model using a sliding mode observer. The stated goal is to estimate rotor position and speed accurately enough to satisfy sensorless vector-control requirements. It is mainly a simulation/algorithm paper rather than a hardware implementation paper.

### Core Algorithm

```yaml
algorithm_name: SMO-based sensorless PMSM vector control
control_type: sensorless vector control / FOC
observer: sliding mode observer
control_loops:
  - speed PI loop with active damping
  - current inner loop with feed-forward decoupling
  - back-EMF estimation through SMO
```

**Algorithm sequence:**
1. Clarke/Park transform stator currents
2. Build PMSM αβ-frame model
3. Use SMO switching law to estimate back EMF
4. Apply low-pass filter to obtain continuous back-EMF estimate
5. Estimate position using arctan with angle compensation
6. Use speed PI controller with active damping
7. Use current loop with feed-forward decoupling

### Key Equations

```yaml
motor_model:
  - alpha/beta voltage equation (eq.1)
  - extended back-EMF (eq.2)
  - current differential equation (eq.3)

observer:
  - observer current equation (eq.4)
  - current error equation (eq.5)
  - sliding mode control rule (eq.6)
  - equivalent back-EMF extraction (eq.7)
  - low-pass filtered back-EMF (eq.8)

position_estimation:
  - theta_hat = arctan relation plus compensation (eq.9)

mechanical_model:
  - electromagnetic torque (eq.10)
  - rotor dynamics (eq.11)
  - active damping (eq.12-15)

controllers:
  - speed-loop PI parameters (eq.16-17)
  - current-loop regulator (eq.18-21)
  - internal model control (eq.22-27)
```

### Key Parameters

```yaml
SMO_gain_k: 145
low_pass_filter_cutoff: about 30 kHz
beta: 500
xi_r: 0
K_pm: 0.004
K_im: 2
K_pd_K_pq: 120.54
K_id_K_iq: 70440
```

### Motor Parameters (Table 1)

```yaml
motor: 60ST-M00630
rated_voltage: 220 V
rated_power: 200 W
rated_speed: 3000 rpm
rated_torque: 0.637 N·m
rated_current: 1.5 A
rotor_inertia: 0.17e-4 kg·m²
permanent_magnet_flux: 0.3477 Wb
stator_resistance: 11.6 ohm
stator_inductance: 0.022 H
switching_frequency: 10 kHz
pole_pairs: 4
```

### Simulation Results

```yaml
SMO_overshoot: 70%
SMO_adjustment_time: 0.007 s
PI_overshoot: 71.6%
PI_adjustment_time: 0.011 s
open_loop_overshoot: 83.2%
open_loop_adjustment_time: 0.011 s
load_disturbance: 0.637 N·m at t=0.035 s
```

### Applicability

```yaml
works_when:
  - PMSM sensorless vector control
  - medium-to-high speed
  - known motor parameters

fails_or_weak_when:
  - very low speed
  - strong SMO chattering
  - unknown motor parameters
  - high-frequency jitter-sensitive systems

assumptions:
  - known R, Ld, Lq, flux linkage
  - symmetric three-phase current
```

### Relevance

```yaml
relevance_to_22uF_small_dc_link_water_pump: medium
sensorless_foc_relevance: high
small_dc_link_relevance: low
pump_application_relevance: low
implementation_relevance: medium_high
```

Most useful: SMO observer structure, back-EMF estimation and filtering, position estimation with angle compensation, PI tuning formulas using motor parameters.

Not directly solved: Small DC-link ripple suppression, Pavg_ref or power-balance reference, low-capacitance DC bus constraints, pump-specific startup under load.

### Extraction Quality

```yaml
accuracy_risk: low_medium
completeness: high_for_simulation_algorithm
implementability_signal: medium_high
evidence_quality: high
project_relevance: medium
```

---

## Algorithm Card A3

### Paper

```yaml
paper_id: A3
title: A Boost Converter Design with Low Output Ripple Based on Harmonics Feedback
arxiv: 1901.10020
role: dc_link_ripple_reference
category: P3
pages: 8
text_extractable: yes
```

### Problem

This paper addresses DC-link voltage ripple reduction in power-electronic converters. Large output capacitor banks are conventionally used to reduce DC-link ripple when an inverter is connected to a boost converter. The proposed method uses an observer to estimate DC-link voltage/current harmonics, then feeds harmonic terms back into duty-cycle control.

### Core Algorithm

```yaml
algorithm_name: Observer-based harmonic feedback for DC-link ripple reduction
control_type: converter duty-cycle feedback
plant: boost converter feeding inverter/motor load
observer: 7th-order LTI harmonic observer
feedback_target: duty cycle D
main_goal: reduce DC-link voltage/current ripple
```

**Algorithm sequence:**
1. Decompose DC-link voltage into average component plus harmonics
2. Model the first three harmonics using a 7th-order LTI system
3. Build an observer to estimate harmonic states
4. Discretize the observer for digital implementation
5. Add estimated harmonic states into duty-cycle feedback

### Key Equations

```yaml
dc_link_decomposition:
  - vdc(t) = average + harmonic sum (eq.11-12)

state_space_harmonic_model:
  - 7x7 system matrix S (eq.13)
  - output matrix G (eq.14)
  - vdc = Gx (eq.15)

observer:
  - z_dot = (S - LG)z + L vdc (eq.20)
  - discrete observer z[k] (eq.25)

duty_feedback:
  - baseline duty feedback (eq.21)
  - feedback with harmonics (eq.22)
  - final harmonic feedback gains (eq.29)
```

### Key Parameters

```yaml
sampling_frequency: 18 kHz
ripple_frequency: 400 Hz
beta: 2512 rad/s
Vs: 12 V
Vdc: 28 V
D0: 0.42
iL0: 0.9 A
k1: -0.08
k2: -0.06
k3: trial-and-error integrator gain
harmonic_gains:
  z2: -0.3
  z3: 0.2
  z4: -0.1
  z5: 0.2
  z6: -0.03
  z7: 0.14
observer_gain_Ld:
  - 0.0981
  - 0.0195
  - 0.0019
  - 0.0192
  - 0.0051
  - 0.0189
  - 0.0047
```

### Simulation Results

```yaml
reported_result:
  - significant voltage/current ripple reduction
  - reconstructed vdc matches original with negligible error
  - 7th-order model sufficient for DC-link voltage harmonics
```

### Applicability

```yaml
works_when:
  - boost converter with inverter load
  - known ripple frequency
  - DC-link voltage control objective
  - harmonic model sufficient

fails_or_weak_when:
  - unknown ripple frequency
  - very fast load transients
  - observer gain tuning is poor
  - MCU cannot handle 7x7 matrix update at sampling rate

assumptions:
  - steady-state ripple frequency known
  - first three harmonics dominate
  - 7th-order model sufficient
```

### Relevance

```yaml
relevance_to_22uF_small_dc_link_water_pump: medium_high
sensorless_foc_relevance: low
small_dc_link_relevance: high
pump_application_relevance: low
implementation_relevance: medium
```

Most useful: DC-link harmonic decomposition, observer-based harmonic estimation, duty-cycle feedback using estimated harmonic components, conceptual model for ripple-aware control.

Not directly solved: PMSM sensorless FOC, small DC-link inverter without boost stage, input power reference Pavg_ref, torque/speed ripple coupling, TMS320F28035 computational feasibility.

### Extraction Quality

```yaml
accuracy_risk: low
completeness: medium_high
implementability_signal: medium
evidence_quality: high
project_relevance: medium_for_dc_link_ripple
```

---

## Cross-Paper Comparison

| Paper | Role | Sensorless FOC | Small DC-Link | Pump App | MCU Feasibility | Extraction Confidence |
|-------|------|:-:|:-:|:-:|:-:|:-:|
| A1 | main_application_algorithm | High | Low | High | Medium | High |
| A2 | sensorless_control_algorithm | High | Low | Low | Medium | High |
| A3 | dc_link_ripple_reference | Low | High | Low | Medium-low | High |

## Project-Relevance Matrix

| Requirement | A1 | A2 | A3 | Notes |
|-------------|:--:|:--:|:--:|-------|
| Sensorless FOC | High | High | Low | A1 and A2 are primary |
| Pump application | High | Low | Low | A1 is the only pump-specific paper |
| Startup strategy | High | Low-medium | None | A1 dominates |
| Observer design | Medium | High | High | A2 for rotor/back-EMF, A3 for DC-link harmonics |
| Small DC-link / ripple | Low | Low | High | A3 dominates |
| MCU feasibility | Medium | Medium | Medium-low | A3's 7x7 observer may be heavier |
| Direct 22µF relevance | Low | Low | Medium | None directly validates 22µF |
| Pavg_ref calculation | Not found | Not found | Not found | Need separate source |

## Candidate Ranking

1. **A1** — Best for sensorless FOC startup and transition. Directly targets submersible pump PMSM drives with a concrete three-step startup strategy.
2. **A2** — Best for generic PMSM sensorless vector control. Provides usable SMO structure, low-pass filter, position estimation, and PI tuning path.
3. **A3** — Best for DC-link ripple thinking. Provides harmonic observer and feedback strategy, but is a boost converter paper, not a PMSM FOC paper.

## Extraction Quality Report

```yaml
accuracy:
  score: 24/30
  reason: extracted claims tied to reader-provided equations, algorithm summaries, figures, and experiment summaries

completeness:
  score: 16/20
  reason: problem, method, equations, figures, experiments, applicability captured for all papers; full page-level evidence still missing

implementability:
  score: 18/25
  reason: A1 and A2 provide actionable control-loop structure; A3 provides implementable harmonic feedback loop; full code-level pseudocode not yet generated

evidence_quality:
  score: 12/15
  reason: equations and figures referenced; page numbers implicit through equation numbering; some claims could use more specific figure/table citations

project_relevance:
  score: 7/10
  reason: A1 directly relevant to pump startup, A3 relevant to DC-link ripple, but no paper covers 22µF small DC-link sensorless FOC pump scenario fully

total_score: 77/100
verdict: PASS_WITH_NOTES
```

## Next Step

Recommended next stage: **Full-text algorithm extraction** with page-level evidence for equations, figures, and experimental data.

Required inputs:
- Full extracted text with page numbers
- Figure captions with figure numbers
- Equation numbers with full LaTeX
- Table data with table numbers
- Experimental conditions with specific values
