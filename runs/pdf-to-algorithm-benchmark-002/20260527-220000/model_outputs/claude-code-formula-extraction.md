# Claude Code — Deep Formula Extraction (002)

## Scope

Full equation extraction with page numbers, figure/table references, and pseudocode generation for all 3 papers.

---

## A1: Sensorless FOC for CSI-fed PMSM (2503.22855)

### Page 2 — Mathematical Model

**Eq.1** (p.2, right col): α-axis voltage equation
$$L_s \frac{di_\alpha}{dt} = -R_s i_\alpha - e_\alpha + u_\alpha$$

**Eq.2** (p.2, right col): β-axis voltage equation
$$L_s \frac{di_\beta}{dt} = -R_s i_\beta - e_\beta + u_\beta$$

**Eq.3** (p.2, right col): α-axis back EMF
$$e_\alpha = -\frac{\sqrt{3}}{2} \psi_f P \omega_e \sin(\theta_e)$$

**Eq.4** (p.2, right col): β-axis back EMF
$$e_\beta = \frac{\sqrt{3}}{2} \psi_f P \omega_e \cos(\theta_e)$$

Variables: $i_\alpha, i_\beta$ = stator currents; $u_\alpha, u_\beta$ = stator voltages; $e_\alpha, e_\beta$ = back EMFs; $R_s$ = stator resistance; $L_s$ = synchronous inductance; $\psi_f$ = flux linkage; $P$ = pole pairs; $\omega_e$ = rotor angular speed; $\theta_e$ = rotor position

### Page 3 — dq-frame Model

**Eq.5** (p.3, left col): d-axis voltage
$$L_s \frac{di_d}{dt} = -R_s i_d + \omega_e L_s i_q + u_d$$

**Eq.6** (p.3, left col): q-axis voltage
$$L_s \frac{di_q}{dt} = -R_s i_q - \omega_e L_s i_d - \omega_e \psi_f + u_q$$

Variables: $i_d, i_q$ = dq-axis currents; $u_d, u_q$ = dq-axis voltages

### Page 3 — Startup Reference

**Eq.7** (p.3, left col): Reference angle
$$\theta_e^* = \int \omega_e^* dt$$

**Eq.8** (p.3, left col): Ramp speed command
$$\omega_e^* = K_\omega t$$

Variables: $K_\omega$ = ramp constant

### Page 3 — Current Transformation

**Eq.9** (p.3, right col): α-axis current
$$i_\alpha = i_q^* \cos\delta_e^* - i_d^* \sin\delta_e^*$$

**Eq.10** (p.3, right col): d-axis current
$$i_d = i_q^* \sin\delta_e^* + i_d^* \cos\delta_e^*$$

### Page 4 — Error Compensation

**Eq.11** (p.4, left col): Estimated q-axis voltage
$$\hat{u}_q = \omega_e L_s i_q + \omega_e \psi_f \cos(\delta_e)$$

**Eq.12** (p.4, left col): Estimated d-axis voltage
$$\hat{u}_d = -\omega_e L_s i_q + \omega_e \psi_f \sin(\delta_e)$$

Variables: $\delta_e = \theta_e - \hat{\theta}_e$ = position error

### Table I (p.4, left col) — System Parameters

| Parameter | Value |
|-----------|-------|
| $R_s$ | 2.16 Ω |
| $L_s$ | 4.56 mH |
| $R_c$ (cable) | 11.76 Ω |
| $L_c$ (cable) | 9.7 mH |
| $C_c$ (cable) | 111 nF |
| $P$ | 6 |
| $V_g$ | 480 V |
| $f_g$ | 60 Hz |
| $L_{dc}$ | 10 mH |
| $C_o$ | 50 μF |

### Figures

- **Fig.1** (p.2, left col): CSI-fed PMSM drive system with long cable
- **Fig.2** (p.2, right col): FOC control block diagram with proposed smooth transition
- **Fig.3** (p.3, left col): PLL with improved startup and smooth transition
- **Fig.4** (p.3, right col): Virtual synchronous d*q*-reference frame at initial startup
- **Fig.5** (p.3, right col): Virtual synchronous d*q*-reference frame during acceleration
- **Fig.6** (p.4, right col): Simulation waveform of motor speed
- **Fig.7** (p.5, left col): Estimated position, virtual synchronous position, angle error
- **Fig.8** (p.5, left col): Real position, estimated position, angle error
- **Fig.9** (p.5, right col): Three phase currents, real dq-axis currents
- **Fig.10** (p.5, right col): Estimated dq-axis currents
- **Fig.11** (p.6, left col): Experimental setup (TMS320F28388D, 1.8km cable)
- **Fig.12** (p.6, left col): Experimental motor speed during transition
- **Fig.13** (p.6, right col): Experimental position results (virtual, estimated, error)
- **Fig.14** (p.7, left col): Experimental position results (estimated, real, error)

### Experimental Results (p.6-7)

- **Processor**: TMS320F28388D
- **Cable**: 1.8 km long cable connection
- **Encoder**: Optical encoder for comparison only (not used in control)
- **Speed**: Accelerates to 300 rpm
- **Oscillation**: ~11 rpm speed oscillation, 0.09 A current oscillation
- **Transition timing**: Terminal 1→2 at t=3s, Terminal 2→3 at t=3.5s

### Pseudocode: 3-Step Startup

```
// A1: Sensorless FOC Startup for CSI-fed PMSM
// Reference: Bahrami-Fard et al., arXiv 2503.22855

INITIALIZE:
  R_s = 2.16, L_s = 4.56e-3, psi_f = [from motor datasheet]
  P = 6, K_omega = [ramp constant]
  theta_hat = 0, omega_hat = 0
  terminal = 1

// === TERMINAL 1: I-f Startup ===
WHILE terminal == 1:
  // Ramp speed command
  omega_ref = K_omega * t
  theta_ref = integral(omega_ref)

  // Current references (open-loop)
  i_d_ref = 0
  i_q_ref = I_const  // constant q-axis current

  // Transform to alpha-beta
  i_alpha_ref = i_q_ref * cos(theta_ref) - i_d_ref * sin(theta_ref)
  i_beta_ref = i_q_ref * sin(theta_ref) + i_d_ref * cos(theta_ref)

  // PLL observer
  [i_alpha_hat, i_beta_hat] = state_observer(i_alpha, i_beta, u_alpha, u_beta)
  [e_alpha_hat, e_beta_hat] = back_emf_estimate(i_alpha_hat, i_beta_hat)
  omega_hat = PLL_track(e_alpha_hat, e_beta_hat)
  theta_hat = PLL_angle()

  // Check if speed is sufficient for FOC
  IF omega_hat >= omega_threshold:
    // Compressor: align estimated frame to virtual reference
    delta_error = theta_hat - theta_ref
    COMPENSATOR_ALIGN(delta_error)
    terminal = 2

// === TERMINAL 2: Compressor Alignment ===
WHILE terminal == 2:
  // Keep i_d fixed, reduce alignment error
  delta_error = theta_hat - theta_ref
  COMPENSATOR_ALIGN(delta_error)

  // Update position estimate
  theta_hat = PLL_angle()

  IF |delta_error| < tolerance:
    terminal = 3

// === TERMINAL 3: Error Compensation ===
WHILE terminal == 3:
  // Estimate dq voltages
  u_q_hat = omega_hat * L_s * i_q + omega_hat * psi_f * cos(delta_e)
  u_d_hat = -omega_hat * L_s * i_q + omega_hat * psi_f * sin(delta_e)

  // Error compensation algorithm
  theta_c = 0
  dtheta = [initial step size]
  FOR h = 1 TO max_iterations:
    u_q_calc = omega_hat * L_s * i_q + omega_hat * psi_f * cos(delta_e)
    u_d_calc = -omega_hat * L_s * i_q + omega_hat * psi_f * sin(delta_e)

    IF u_q_calc > u_q_prev:
      dtheta[h] = dtheta[h]  // keep same
    ELSE:
      dtheta[h] = -dtheta[h]  // flip sign
      recalculate magnitudes

    theta_c = theta_c + dtheta[h]
    u_q_prev = u_q_calc

  // Apply compensation
  theta_hat = theta_hat + theta_c

  // Standard FOC control loop
  [i_d, i_q] = Clarke_Park(i_a, i_b, i_c, theta_hat)
  [u_d, u_q] = PI_controller(i_d_ref, i_q, i_q_ref, i_q)
  [u_alpha, u_beta] = Park_inverse(u_d, u_q, theta_hat)
  [S1, S2, S3] = SVM(u_alpha, u_beta)
```

---

## A2: SMO-based Sensorless PMSM (2305.04046)

### Page 2 — Motor Model

**Eq.1** (p.2, left col): Motor voltage equation (αβ frame)
$$\begin{bmatrix} u_\alpha \\ u_\beta \end{bmatrix} = \begin{bmatrix} R + L_s\frac{d}{dt} & -\omega_e(L_d - L_q) \\ \omega_e(L_d - L_q) & R + L_s\frac{d}{dt} \end{bmatrix} \begin{bmatrix} i_\alpha \\ i_\beta \end{bmatrix} + \begin{bmatrix} e_\alpha \\ e_\beta \end{bmatrix}$$

**Eq.2** (p.2, left col): Extended back EMF
$$\begin{bmatrix} e_\alpha \\ e_\beta \end{bmatrix} = \left[(L_d - L_q)\left(\omega_e i_d - \frac{di_q}{dt}\right) + \omega_e \psi_f\right] \begin{bmatrix} -\sin\theta_e \\ \cos\theta_e \end{bmatrix}$$

**Eq.3** (p.2, right col): Observer current equation
$$\begin{bmatrix} \frac{di_\alpha}{dt} \\ \frac{di_\beta}{dt} \end{bmatrix} = \frac{1}{L_s}\begin{bmatrix} -R & -(L_d-L_q)\omega_e \\ (L_d-L_q)\omega_e & -R \end{bmatrix}\begin{bmatrix} i_\alpha \\ i_\beta \end{bmatrix} + \frac{1}{L_s}\begin{bmatrix} u_\alpha \\ u_\beta \end{bmatrix} - \frac{1}{L_s}\begin{bmatrix} e_\alpha \\ e_\beta \end{bmatrix}$$

### Page 3 — SMO Design

**Eq.4** (p.3, left col): Observer with measured currents
$$\begin{bmatrix} \frac{d\hat{i}_\alpha}{dt} \\ \frac{d\hat{i}_\beta}{dt} \end{bmatrix} = \frac{1}{L_s}\begin{bmatrix} -R & -(L_d-L_q)\omega_e \\ (L_d-L_q)\omega_e & -R \end{bmatrix}\begin{bmatrix} \hat{i}_\alpha \\ \hat{i}_\beta \end{bmatrix} + \frac{1}{L_s}\begin{bmatrix} u_\alpha \\ u_\beta \end{bmatrix} - \frac{1}{L_s}\begin{bmatrix} v_\alpha \\ v_\beta \end{bmatrix}$$

**Eq.5** (p.3, left col): Error equation
$$\begin{bmatrix} \frac{d\tilde{i}_\alpha}{dt} \\ \frac{d\tilde{i}_\beta}{dt} \end{bmatrix} = \frac{1}{L_s}\begin{bmatrix} -R & -(L_d-L_q)\omega_e \\ (L_d-L_q)\omega_e & -R \end{bmatrix}\begin{bmatrix} \tilde{i}_\alpha \\ \tilde{i}_\beta \end{bmatrix} - \frac{1}{L_s}\begin{bmatrix} e_\alpha \\ e_\beta \end{bmatrix}$$

**Eq.6** (p.3, left col): Sliding mode control rule
$$\begin{bmatrix} v_\alpha \\ v_\beta \end{bmatrix} = \begin{bmatrix} k \cdot \text{sgn}(\hat{i}_\alpha - i_\alpha) \\ k \cdot \text{sgn}(\hat{i}_\beta - i_\beta) \end{bmatrix}$$

**Eq.7** (p.3, left col): Equivalent control (back EMF extraction)
$$\begin{bmatrix} e_\alpha \\ e_\beta \end{bmatrix} = \begin{bmatrix} v_\alpha \\ v_\beta \end{bmatrix}_{eq} = \begin{bmatrix} k \cdot \text{sgn}(\tilde{i}_\alpha) \\ k \cdot \text{sgn}(\tilde{i}_\beta) \end{bmatrix}$$

**Eq.8** (p.3, left col): Low-pass filter
$$\begin{bmatrix} \frac{d\hat{e}_\alpha}{dt} \\ \frac{d\hat{e}_\beta}{dt} \end{bmatrix} = \begin{bmatrix} \frac{-\hat{e}_\alpha + k \cdot \text{gn}(\tilde{i}_\alpha)}{\tau_0} \\ \frac{-\hat{e}_\beta + k \cdot \text{gn}(\tilde{i}_\beta)}{\tau_0} \end{bmatrix}$$

**Eq.9** (p.3, left col): Position estimation with compensation
$$\hat{\theta}_{ex} = -\arctan\left(\frac{\hat{e}_\alpha}{\hat{e}_\beta}\right) + \arctan\left(\frac{\hat{\omega}_r}{\omega_0}\right)$$

### Page 3-4 — Mechanical Model

**Eq.10** (p.3, right col): Electromagnetic torque
$$T_e = \frac{3P}{2}\left[\psi_f i_q + (L_d - L_q)i_d i_q\right]$$

**Eq.11** (p.3, right col): Mechanical equation
$$J\frac{d\omega_m}{dt} = T_e - T_L - \xi\omega_m$$

**Eq.12** (p.3, right col): Active damping
$$i_q = i_q^* - \xi_r \omega_m$$

**Eq.13** (p.3, right col): Motor dynamics
$$\frac{d\omega_m}{dt} = \frac{1.5P_p\psi_f}{J}i_q - \frac{1.5P_p\psi_f}{J}\xi_r\omega_m - \frac{\xi}{J}\omega_m$$

**Eq.14** (p.3, right col): Transfer function
$$\omega_m(s) = \frac{1.5P_p\psi_f}{J(s+\beta)}i_q(s)$$

**Eq.15** (p.3, right col): Damping coefficient
$$\xi_r = \frac{J\beta - \xi}{1.5P_p\psi_f}$$

**Eq.16** (p.3, right col): Speed loop PI
$$i_q^* = \left(K_{pm} + \frac{K_{im}}{s}\right)(\omega_m^* - \omega_m) - \xi_r\omega_m$$

**Eq.17** (p.3, right col): PI parameters
$$K_{pm} = \frac{J\beta}{1.5P_p\psi_f}, \quad K_{im} = \beta K_{pm}$$

### Page 4-5 — Current Loop

**Eq.18-21** (p.4-5): Current loop with feed-forward decoupling
$$u_d^* = (K_{pd} + \frac{K_{id}}{s})(i_d^* - i_d) - \omega_e L_q i_q$$
$$u_q^* = (K_{pq} + \frac{K_{iq}}{s})(i_q^* - i_q) - \omega_e(L_d i_d + \psi_f)$$

**Eq.22-27** (p.5): Internal model control
$$F(s) = \left[I - C(s)\hat{G}(s)\right]^{-1}C(s)$$
$$K_{pd} = aL_d, \quad K_{id} = aR$$
$$K_{pq} = aL_q, \quad K_{iq} = aR$$

### Table 1 (p.6) — Motor Parameters

| Parameter | Value |
|-----------|-------|
| Rated voltage | 220 V |
| Rated power | 200 W |
| Rated speed | 3000 rpm |
| Rated torque | 0.637 N·m |
| Rated current | 1.5 A |
| Rotor inertia $J$ | 0.17 × 10⁻⁴ kg·m² |
| PM flux $\psi_f$ | 0.3477 Wb |
| Stator resistance $R_s$ | 11.6 Ω |
| Stator inductance $L_s$ | 0.022 H |
| Switching frequency $f_s$ | 10 kHz |
| Pole pairs $P$ | 4 |

### Key Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| SMO gain $k$ | 145 | p.3, "after several adjustments" |
| LPF cutoff $\omega_0$ | ~30 kHz | p.3, "adjusted from 20kHz" |
| $\beta$ | 500 | p.5, "after plugging in motor parameters" |
| $\xi_r$ | 0 | p.5 |
| $K_{pm}$ | 0.004 | p.5 |
| $K_{im}$ | 2 | p.5 |
| $K_{pd}=K_{pq}$ | 120.54 | p.5 |
| $K_{id}=K_{iq}$ | 70440 | p.5 |

### Simulation Results (p.6-7)

- **Fig.5** (p.6): Speed comparison: SMO overshoot 70%, PI overshoot 71.6%, open-loop overshoot 83.2%
- **Fig.6** (p.7): Speed profiles at 1000, 800, 600 rpm
- **Fig.7** (p.7): Speed variation during acceleration/deceleration
- **Fig.8** (p.7): dq-axis voltage changes
- **Fig.9** (p.7): dq-axis current variation
- **Fig.10** (p.7): Position following curve
- **Fig.11** (p.8): Torque curve during sudden load (0.637 N·m at t=0.035s)
- **Fig.12** (p.8): Motor speed during sudden load

### Pseudocode: SMO Sensorless FOC

```
// A2: SMO-based Sensorless PMSM Vector Control
// Reference: Zhang et al., arXiv 2305.04046

INITIALIZE:
  R = 11.6, L_s = 0.022, psi_f = 0.3477
  P = 4, J = 0.17e-4, xi = 0
  k_smo = 145, tau_0 = 1/(2*pi*30e3)
  K_pm = 0.004, K_im = 2
  K_pd = 120.54, K_id = 70440
  beta = 500, xi_r = 0

// === Main Control Loop (at each PWM interrupt) ===
WHILE running:
  // 1. Clarke Transform
  i_alpha = i_a
  i_beta = (i_a + 2*i_b) / sqrt(3)

  // 2. SMO: Estimate back EMF
  // Observer dynamics
  di_alpha_hat = (1/L_s)*(-R*i_alpha_hat - (L_d-L_q)*omega_e*i_beta_hat + u_alpha - v_alpha)
  di_beta_hat = (1/L_s)*((L_d-L_q)*omega_e*i_alpha_hat - R*i_beta_hat + u_beta - v_beta)

  // Sliding mode control
  v_alpha = k_smo * sign(i_alpha_hat - i_alpha)
  v_beta = k_smo * sign(i_beta_hat - i_beta)

  // Low-pass filter for back EMF
  de_alpha_hat = (-e_alpha_hat + v_alpha) / tau_0
  de_beta_hat = (-e_beta_hat + v_beta) / tau_0

  // 3. Position estimation
  theta_hat = -arctan(e_alpha_hat / e_beta_hat) + arctan(omega_hat / omega_0)

  // 4. Speed estimation
  omega_hat = sqrt(e_alpha_hat^2 + e_beta_hat^2) / psi_f

  // 5. Clarke-Park Transform
  [i_d, i_q] = Park(i_alpha, i_beta, theta_hat)

  // 6. Speed loop PI with active damping
  omega_error = omega_ref - omega_hat
  i_q_ref = K_pm * omega_error + K_im * integral(omega_error) - xi_r * omega_hat

  // 7. Current loop PI with decoupling
  i_d_error = 0 - i_d  // d-axis current reference = 0
  i_q_error = i_q_ref - i_q
  u_d = K_pd * i_d_error + K_id * integral(i_d_error) - omega_e * L_q * i_q
  u_q = K_pq * i_q_error + K_iq * integral(i_q_error) - omega_e * (L_d * i_d + psi_f)

  // 8. Inverse Park + SVM
  [u_alpha, u_beta] = Park_inverse(u_d, u_q, theta_hat)
  [S1, S2, S3] = SVM(u_alpha, u_beta)
```

---

## A3: Boost Converter Low Ripple (1901.10020)

### Page 2 — DC-link Harmonics Model

**Eq.11** (p.2, right col): DC-link voltage decomposition
$$v_{dc}(t) = v_a + \sum_{n=1}^{3} b_n \cos(n\beta t + \phi_n)$$

**Eq.12** (p.2, right col): First three harmonics
$$v_{dc}(t) = v_a + b_1\cos(\beta t + \phi_1) + b_2\cos(2\beta t + \phi_2) + b_3\cos(3\beta t + \phi_3)$$

### Page 2 — State-Space Model

**Eq.13** (p.2, right col): 7th-order system matrix
$$S = \begin{bmatrix} 0 & 0 & 0 & 0 & 0 & 0 & 0 \\ 0 & 0 & -\beta & 0 & 0 & 0 & 0 \\ 0 & \beta & 0 & 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 & -2\beta & 0 & 0 \\ 0 & 0 & 0 & 2\beta & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 & 0 & 0 & -3\beta \\ 0 & 0 & 0 & 0 & 0 & 3\beta & 0 \end{bmatrix}$$

**Eq.14** (p.2, right col): Output matrix
$$G = \begin{bmatrix} 1 & 1 & 0 & 1 & 0 & 1 & 0 \end{bmatrix}$$

**Eq.15** (p.2, right col): State-space representation
$$v_{dc} = Gx, \quad \dot{x} = Sx, \quad x(0) = x_0$$

### Page 3 — Observer Design

**Eq.20** (p.3, left col): Observer equation
$$\dot{z} = (S - LG)z + Lv_{dc}$$

**Eq.21** (p.3, left col): Duty cycle feedback (baseline)
$$D = D_0 + k_1(i_L - i_{L0}) + k_2(v_{dc} - v_{ref}) + k_3\int(v_{dc} - v_{ref})dt$$

**Eq.22** (p.3, left col): Feedback with harmonics
$$D = D_0 + k_1(i_L - i_{L0}) + k_2(v_{dc} - v_{ref}) + k_3\int(v_{dc} - v_{ref})dt + Kz$$

### Page 3-4 — Discretization

**Eq.23** (p.3, right col): Discretized system
$$v_{dc}[k] = Gx[k], \quad x[k+1] = S_d x[k]$$

**Eq.24** (p.3, right col): Discretized state matrix
$$S_d = e^{S \cdot \frac{\omega}{10000}T}$$

**Eq.25** (p.3, right col): Discretized observer
$$z[k] = S_d z[k] + L_d(v_{dc}[k] - Gz[k])$$

### Page 4 — Final Parameters

**Eq.26** (p.4, left col): Feedback control (first version)
$$D = D_0 - 0.08(i_L - i_{L0}) - 0.06(v_{dc} - v_{ref}) + f\int(v_{dc} - v_{ref})dt$$

**Eq.27** (p.4, left col): Discretized $S_d$ matrix (numerical values)

**Eq.28** (p.4, left col): Observer gain
$$L_d = \begin{bmatrix} 0.0981 \\ 0.0195 \\ 0.0019 \\ 0.0192 \\ 0.0051 \\ 0.0189 \\ 0.0047 \end{bmatrix}$$

**Eq.29** (p.4, right col): Final feedback with harmonics
$$D = D_0 - 0.08(i_L - i_{L0}) - 0.06(v_{dc} - v_{ref}) + f\int(v_{dc} - v_{ref})dt - 0.3z_2 + 0.2z_3 - 0.1z_4 + 0.2z_5 - 0.03z_6 + 0.14z_7$$

### Table 1 (p.2, left col): Fundamental and harmonics

| Component | $v_a$ |
|-----------|-------|
| Fundamental | $v_a$ |
| 1st harmonic | $b_1\cos\phi_1$ |
| 1st harmonic derivative | $b_1\sin\phi_1$ |
| 2nd harmonic | $b_2\cos\phi_2$ |
| 2nd harmonic derivative | $b_2\sin\phi_2$ |
| 3rd harmonic | $b_3\cos\phi_3$ |
| 3rd harmonic derivative | $b_3\sin\phi_3$ |

### Key Parameters (p.4)

| Parameter | Value | Source |
|-----------|-------|--------|
| Sampling frequency | 18 kHz | p.4, left col |
| Ripple frequency $\beta$ | 400 Hz → 2512 rad/s | p.4, left col |
| $V_s$ | 12 V | p.4, right col |
| $V_{dc}$ | 28 V | p.4, right col |
| $D_0$ | 0.42 | p.4, right col |
| $i_{L0}$ | 0.9 A | p.4, left col |
| $k_1$ | -0.08 | p.4, left col |
| $k_2$ | -0.06 | p.4, left col |
| $z_2$ gain | -0.3 | p.4, right col |
| $z_3$ gain | 0.2 | p.4, right col |
| $z_4$ gain | -0.1 | p.4, right col |
| $z_5$ gain | 0.2 | p.4, right col |
| $z_6$ gain | -0.03 | p.4, right col |
| $z_7$ gain | 0.14 | p.4, right col |

### Figures

- **Fig.1** (p.1, left col): EV power conversion architecture
- **Fig.2** (p.2, left col): Circuit topology for BLDC motor driver
- **Fig.3** (p.3, right col): Block diagram for entire control system
- **Fig.4** (p.3, right col): Expanded block diagram
- **Fig.5** (p.4, left col): Estimated dc-link voltage and harmonics
- **Fig.6** (p.4, left col): Reconstructed vs original dc-link voltage

### Pseudocode: Harmonic Feedback Observer

```
// A3: Observer-based Harmonic Feedback for DC-Link Ripple
// Reference: Wang, arXiv 1901.10020

INITIALIZE:
  // System matrices
  beta = 2*pi*400  // ripple frequency
  S = [7x7 matrix from Eq.13]
  G = [1 1 0 1 0 1 0]
  L_d = [0.0981; 0.0195; 0.0019; 0.0192; 0.0051; 0.0189; 0.0047]

  // Operating point
  V_s = 12, V_dc_ref = 28, D_0 = 0.42, i_L0 = 0.9
  k1 = -0.08, k2 = -0.06

  // Harmonic feedback gains
  K_harm = [0, -0.3, 0.2, -0.1, 0.2, -0.03, 0.14]

  // Observer state
  z = [0; 0; 0; 0; 0; 0; 0]

  // Sampling
  T = 1/18000  // 18 kHz

// === Main Control Loop ===
WHILE running:
  // 1. Measure DC-link voltage and inductor current
  v_dc = ADC_read_voltage()
  i_L = ADC_read_current()

  // 2. Update observer
  v_dc_hat = G * z
  innovation = v_dc - v_dc_hat
  z = S_d * z + L_d * innovation

  // 3. Calculate duty cycle with harmonic feedback
  D = D_0
  D += k1 * (i_L - i_L0)           // inductor current feedback
  D += k2 * (v_dc - V_dc_ref)      // voltage error feedback
  D += k3 * integral(v_dc - V_dc_ref)  // integrator
  D += K_harm' * z                   // harmonic feedback

  // 4. Saturate duty cycle
  D = max(0, min(0.8, D))

  // 5. Apply to PWM
  PWM_set_duty(D)
```
