# Claude Code PDF Reader Output

## Inventory

| Filename | Title | Pages | Text | Language | Keywords | Formula | Diagram | Experiment | Category |
|----------|-------|-------|------|----------|----------|---------|---------|------------|----------|
| A1-sensorless-foc-csi-pmsm-submersible-pump.pdf | Sensorless Field Oriented Control of CSI-Fed PMSM Drives Used in Submersible Pumps | 8 | ✓ | en | sensorless, FOC, CSI, PMSM, submersible, pump | ✓ | ✓ | ✓ | P1 |
| A2-pmsm-smo-sensorless-vector-control.pdf | Simulation of non-inductive vector control of permanent magnet synchronous motor based on sliding mode observer | 8 | ✓ | en | PMSM, SMO, sensorless, vector control | ✓ | ✓ | ✓ | P2 |
| A3-dc-link-ripple-harmonics-feedback.pdf | A Boost Converter Design with Low Output Ripple Based on Harmonics Feedback | 8 | ✓ | en | boost, converter, ripple, harmonics, feedback | ✓ | ✓ | ✓ | P3 |

## Selection Justification

- **A1 (P1 - Algorithm)**: CSI-fed PMSM sensorless FOC for submersible pumps. Directly relevant to pump application. Contains full algorithm: I-f startup, PLL observer, error compensation strategy. Experimental validation on TMS320F28388D.
- **A2 (P2 - Engineering)**: SMO-based sensorless PMSM vector control. Contains motor parameters (Table 1), PI regulator tuning, simulation model. 60ST-M00630 motor used.
- **A3 (P3 - Comparison)**: Boost converter with low output ripple. Focuses on DC-link voltage ripple reduction via harmonics observer. Relevant to small DC-Link capacitance problem.

---

## P1: Sensorless Field Oriented Control of CSI-Fed PMSM Drives Used in Submersible Pumps

### Metadata
- **Authors**: Milad Bahrami-Fard, Majid Ghasemi Korrani, Babak Fahimi
- **Affiliation**: University of Texas at Dallas, REVT lab
- **Reference**: IEEE, 2025
- **arXiv**: 2503.22855

### Abstract
This paper proposes a practical startup strategy for current source inverter (CSI-fed) Permanent Magnet Synchronous Motor (PMSM) drives in submersible pump applications, enabling a seamless shift from sensorless I-f startup to sensorless field-oriented control (FOC). The method effectively manages the transition to sensorless operation without requiring precise current or alignment error calculations, thereby simplifying implementation. By addressing speed and current oscillations directly during the startup and transition stages, the approach significantly enhances overall system stability and responsiveness.

### Equations

| Eq# | Formula | Description |
|-----|---------|-------------|
| (1) | L_s(di_α/dt) = -R_s i_α - e_α + u_α | α-axis voltage equation (stationary frame) |
| (2) | L_s(di_β/dt) = -R_s i_β - e_β + u_β | β-axis voltage equation (stationary frame) |
| (3) | e_α = -(√3/2) ψ_f P ω_e sin(θ_e) | α-axis back EMF |
| (4) | e_β = (√3/2) ψ_f P ω_e cos(θ_e) | β-axis back EMF |
| (5) | L_s(di_d/dt) = -R_s i_d + ω_e L_s i_q + u_d | d-axis voltage (dq frame) |
| (6) | L_s(di_q/dt) = -R_s i_q - ω_e L_s i_d - ω_e ψ_f + u_q | q-axis voltage (dq frame) |
| (7) | θ_e* = ∫ ω_e* dt | Reference angle from ramp speed command |
| (8) | ω_e* = K_ω t | Ramp speed command |
| (9) | i_α = i_q* cos δ_e* - i_d* sin δ_e* | α-axis current transformation |
| (10) | i_d = i_q* sin δ_e* + i_d* cos δ_e* | d-axis current transformation |
| (11) | û_q = ω_e L_s i_q + ω_e ψ_f cos(δ_e) | Estimated q-axis voltage |
| (12) | û_d = -ω_e L_s i_q + ω_e ψ_f sin(δ_e) | Estimated d-axis voltage |

### Figures
- **Fig. 1**: CSI-fed PMSM drive system with long cable connection for submersible pumps
- **Fig. 2**: FOC control with proposed smooth transition strategy (block diagram)
- **Fig. 3**: PLL with improved startup and smooth transition to sensorless FOC
- **Fig. 4**: Diagram of virtual synchronous d*q*-reference frame at initial startup
- **Fig. 5**: Diagram of virtual synchronous d*q*-reference frame during acceleration
- **Fig. 6**: Simulation waveform of motor speed with proposed startup strategy
- **Fig. 7-10**: Simulation results (position, currents)
- **Fig. 11**: Experimental setup (TMS320F28388D, 1.8km cable)
- **Fig. 12-14**: Experimental results (speed, position, currents)

### Algorithm Description

**Three-step startup strategy:**

1. **Terminal 1 (I-f startup)**: Activates motor from standstill with controlled acceleration. q*-axis current constant, d*-axis current zero. Reference angle from integrating ramp speed command. Synchronous frame lags actual rotor by 90 degrees.

2. **Terminal 2 (Compressor alignment)**: At target speed (~300 rpm), compressor reduces error between estimated and virtual reference frames to zero. Position information updates while i_d remains fixed.

3. **Terminal 3 (Error compensation)**: Transitioning introduces initial position error from compressor. Error is systematically reduced using error compensation strategy (Equations 11-12). Estimated θ_e' is adjusted using compensation factor.

**Error compensation algorithm:**
- Initialize θ_c with variable step size dθ
- Calculate amplitudes of û_q and û_d
- If û_q increases, dθ[h] remains constant
- Otherwise, sign of dθ[h] is altered and recalculated
- Guarantees position error compensation without complex models

### Experimental Results
- **Setup**: TMS320F28388D processor, 1.8km long cable, optical encoder for comparison only
- **Speed**: Accelerates to 300 rpm, minimal speed oscillation (~11 rpm)
- **Transition**: Terminal 1→2 at t=3s (no oscillations), Terminal 2→3 at t=3.5s
- **Current**: Minimal oscillation in current (0.09 A) during transition
- **Position error**: Effectively eliminated after compensation

### Applicability
- **Works when**: CSI-fed PMSM, submersible pump, long cable, medium-to-high speed range
- **Fails when**: Very low speed (back EMF too low), VSI drives (different topology)
- **Assumptions**: Surface-mounted PMSM, known motor parameters, 60Hz grid
- **Risks**: Dead-time effects at high speed, cable impedance effects

---

## P2: Simulation of non-inductive vector control of PMSM based on sliding mode observer

### Metadata
- **Authors**: Caiyue Zhang, Zipin Liu, Bowen Xu
- **Affiliation**: Guilin University of Electronic Technology, Xi'an University of Science and Technology, Harbin Institute of Technology Shenzhen
- **Reference**: arXiv 2305.04046

### Abstract
Permanent magnet synchronous motors (PMSM) are extensively utilized in industries. This study develops a mathematical model for sensorless control of a PMSM using SMO (Sliding Mode Observer) vector control. PMSM's sliding mode observer model is built in matlab/simulink environment. Experiments demonstrate that the system can track the rotor position and speed of the motor precisely and fulfill the requirements of sensorless vector control of PMSM.

### Equations

| Eq# | Formula | Description |
|-----|---------|-------------|
| (1) | [u_α; u_β] = [R+L_s(d/dt), -ω_e(L_d-L_q); ω_e(L_d-L_q), R+L_s(d/dt)] [i_α; i_β] + [e_α; e_β] | Motor voltage equation (αβ frame) |
| (2) | [e_α; e_β] = [(L_d-L_q)(ω_e i_d - di_q/dt) + ω_e ψ_f] [-sin θ_e; cos θ_e] | Extended back EMF |
| (3) | [di_α/dt; di_β/dt] = (1/L_s)[-R, -(L_d-L_q)ω_e; (L_d-L_q)ω_e, -R][i_α; i_β] + (1/L_s)[u_α; u_β] - (1/L_s)[e_α; e_β] | Observer current equation |
| (4) | [dĩ_α/dt; dĩ_β/dt] = (1/L_s)[-R, -(L_d-L_q)ω_e; (L_d-L_q)ω_e, -R][ĩ_α; ĩ_β] - (1/L_s)[ē_α; ē_β] | Error equation |
| (5) | [dĩ_α/dt; dĩ_β/dt] = (1/L_s)[-R, -(L_d-L_q)ω_e; (L_d-L_q)ω_e, -R][ĩ_α; ĩ_β] - (1/L_s)[ē_α; ē_β] | Current measurement inaccuracy |
| (6) | [v_α; v_β] = [k·sgn(ĩ_α - i_α); k·sgn(ĩ_β - i_β)] | Sliding mode control rule |
| (7) | [ē_α; ē_β] = [v_α; v_β]_eq = [k·sgn(ĩ_α); k·sgn(ĩ_β)] | Equivalent control quantity |
| (8) | [dē_α/dt; dē_β/dt] = [(-ē_α + k·gn(ĩ_α))/τ_0; (-ē_β + k·gn(ĩ_β))/τ_0] | Low-pass filter for back EMF |
| (9) | θ̂_ex = -arctan(ē_α / ē_β) + arctan(ω̂_r / ω_0) | Position estimation with angle compensation |
| (10) | T_e = 3P[ψ_f i_q + (L_d - L_q)i_d i_q] / 2 | Electromagnetic torque |
| (11) | J(dω_m/dt) = T_e - T_L - ξω_m | Mechanical equation |
| (12) | i_q = i_q* - ξω_m | Active damping principle |
| (13) | dω_m/dt = (1.5P_p ψ_f/J)i_q - (1.5P_p ψ_f/J)ξω_m - (ξ/J)ω_m | Motor dynamics |
| (14) | ω_m(s) = (1.5P_p ψ_f)/(J(s+β)) i_q(s) | Transfer function |
| (15) | ξ_r = (Jβ - ξ)/(1.5P_p ψ_f) | Active power damping coefficient |
| (16) | i_q* = (K_pm + K_im/s)(ω_m* - ω_m) - ξ_r ω_m | Speed loop PI controller |
| (17) | K_pm = Jβ/(1.5P_p ψ_f), K_im = βK_pm | PI regulator parameters |
| (18-27) | Various | Current loop regulator, internal model control |

### Figures
- **Fig. 1**: Overall control block diagram based on SMO
- **Fig. 2**: Equivalent transformation block diagram for internal model control
- **Fig. 3**: Block diagram of closed loop regulation controller
- **Fig. 4**: PMSM vector control system simulation model based on SMO
- **Fig. 5**: Comparison of speed curves (SMO vs PI vs open-loop)
- **Fig. 6**: Speed curves at different speed values (1000, 800, 600 rpm)
- **Fig. 7-10**: Speed variation, dq-axis voltage/current during acceleration/deceleration
- **Fig. 11**: Torque curve during sudden load application
- **Fig. 12**: Motor speed curve during sudden load application

### Algorithm Description

**SMO-based sensorless control:**
1. Clark/Park transformation of stator currents
2. SMO estimates back EMF using sliding mode control rule (eq. 6)
3. Low-pass filter extracts continuous back EMF estimates (eq. 8)
4. Position estimated via arctan function with angle compensation (eq. 9)
5. Speed inner loop PI regulator with active damping (eq. 16-17)
6. Current inner loop with feed-forward decoupling (eq. 21)

**SMO gain**: k = 145 (after several adjustments)

**Low-pass filter**: τ_0 cutoff frequency ~30kHz (adjusted from 20kHz)

**PI parameters**: β=500, ξ_r=0, K_pm=0.004, K_im=2 (after plugging in motor parameters)

### Simulation Results
- **Motor**: 60ST-M00630 (Table 1)
- **SMO overshoot**: 70%, adjustment time: 0.007s
- **PI controller overshoot**: 71.6%, adjustment time: 0.011s
- **Open-loop overshoot**: 83.2%, adjustment time: 0.011s
- **Load disturbance**: Rated torque 0.637 N·M applied at t=0.035s, speed stabilizes around preset value

### Applicability
- **Works when**: PMSM sensorless control, medium-to-high speed range
- **Fails when**: Very low speed (SMO chattering), unknown motor parameters
- **Assumptions**: Known R, L_d, L_q, ψ_f, symmetrical three-phase current
- **Risks**: SMO chattering (mitigated by low-pass filter), high-frequency jitter

---

## P3: A Boost Converter Design with Low Output Ripple Based on Harmonics Feedback

### Metadata
- **Authors**: Haifeng Wang
- **Affiliation**: Penn State University New Kensington
- **Reference**: arXiv 1901.10020

### Abstract
Conventional boost converters are essential to connect low-voltage energy source such as battery with high voltage DC bus in Electric Vehicles due to its simple construction and high conversion efficiency. However, large output capacitor banks must be used in order to reduce the output voltage ripples when an inverter is connected to a boost converter. This paper proposes a new control strategy for ripple reduction in the dc-link of power electronic converters. An observer is designed to adaptively estimate the dc-link voltage and current harmonics. The harmonic terms are multiplied by optimized gains to control the converter's duty cycle by negative feedback law.

### Equations

| Eq# | Formula | Description |
|-----|---------|-------------|
| (11) | v_dc(t) = v_a + Σ b_n cos(nβt + φ_n) | DC-link voltage decomposition |
| (12) | v_dc(t) = v_a + b_1 cos(βt + φ_1) + b_2 cos(2βt + φ_2) + b_3 cos(3βt + φ_3) | First three harmonics |
| (13) | S = 7×7 matrix with β, 2β, 3β | System matrix for 7th order LTI |
| (14) | G = [1 1 0 1 0 1 0] | Output matrix |
| (15) | v_dc = Gx, ẋ = Sx, x(0) = x_0 | State-space representation |
| (20) | ż = (S - LG)z + Lv_dc | Observer equation |
| (21) | D = D_0 + k_1(i_L - i_L0) + k_2(v_dc - v_ref) + k_3∫(v_dc - v_ref)dt | Duty cycle feedback |
| (22) | D = D_0 + k_1(i_L - i_L0) + k_2(v_dc - v_ref) + k_3∫(v_dc - v_ref)dt + Kz | Feedback with harmonics |
| (23) | v_dc[k] = Gx[k], x[k+1] = S_d x[k] | Discretized system |
| (24) | S_d = e^(S·ω/10000)^T | Discretized state matrix |
| (25) | z[k] = S_d z[k] + L_d(v_dc[k] - Gz[k]) | Discretized observer |
| (26) | D = D_0 - 0.08(i_L - i_L0) - 0.06(v_dc - v_ref) + f∫(v_dc - v_ref)dt | Feedback control (1st) |
| (27) | S_d = 7×7 matrix with cos/sin terms | Discretized S_d matrix |
| (28) | L_d = [0.0981; 0.0195; 0.0019; 0.0192; 0.0051; 0.0189; 0.0047] | Observer gain |
| (29) | D = D_0 - 0.08(i_L - i_L0) - 0.06(v_dc - v_ref) + f∫(v_dc - v_ref)dt - 0.3z_2 + 0.2z_3 - 0.1z_4 + 0.2z_5 - 0.03z_6 + 0.14z_7 | Final feedback with harmonics |

### Figures
- **Fig. 1**: EV power conversion architecture
- **Fig. 2**: Circuit topology for BLDC motor driver powered by boost converter
- **Fig. 3**: Block diagram for entire control system
- **Fig. 4**: Expanded block diagram of low harmonics boost converter-inverter motor control model
- **Fig. 5**: Estimated dc-link voltage and its harmonics
- **Fig. 6**: Reconstructed dc-link voltage vs original

### Algorithm Description

**Observer-based harmonics extraction:**
1. Model DC-link voltage as 7th order LTI system (eq. 13-15)
2. Design observer to estimate harmonics (eq. 20)
3. Discretize observer for digital implementation (eq. 23-25)
4. Use estimated harmonics in duty cycle feedback (eq. 29)

**Key parameters:**
- Sampling frequency: 18 kHz
- Real ripple frequency: 400 Hz (β = 2π×400 = 2512 rad/s)
- Nominal operating: V_s = 12V, V_dc = 28V, D_0 = 0.42
- Inductor current: i_L0 = 0.9A

**Feedback gains (eq. 26):**
- k_1 = -0.08 (inductor current)
- k_2 = -0.06 (voltage error)
- k_3 = f (integrator, trial-and-error)
- Harmonic gains: z_2=-0.3, z_3=0.2, z_4=-0.1, z_5=0.2, z_6=-0.03, z_7=0.14

### Simulation Results
- **Ripple reduction**: Significant reduction in voltage/current ripple magnitude
- **Observer accuracy**: Reconstructed v_dc matches original with negligible error
- **7th order model**: Sufficient for DC-link voltage harmonics

### Applicability
- **Works when**: Boost converter with inverter load, known ripple frequency, DC-link voltage control
- **Fails when**: Unknown ripple frequency, very fast load transients
- **Assumptions**: Steady-state ripple frequency known, 7th order model sufficient
- **Risks**: Observer gain tuning, computational load of 7×7 matrix
