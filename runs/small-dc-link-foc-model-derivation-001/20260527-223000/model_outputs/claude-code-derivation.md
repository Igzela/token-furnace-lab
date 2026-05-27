# Claude Code — Pavg_ref and 22µF DC-Link Ripple Derivation

## 1. System Definition

### Target System

| Parameter | Value | Notes |
|-----------|-------|-------|
| DC-link capacitance $C_{dc}$ | 22 µF | Very small, electrolytic-capacitorless |
| Input voltage range | 168-250 Vac | Single-phase rectified |
| Rectified DC voltage | 237-354 Vdc | $V_{dc} = \sqrt{2} \cdot V_{ac}$ |
| Motor type | PMSM | Surface-mounted, water pump |
| Control | Sensorless FOC | SMO-based |
| Platform | TMS320F28035 | 60 MHz, fixed-point |
| Baseline | 1360 µF at 4000 rpm, 300 Vdc | Light load |

### Operating Points

| Speed (rpm) | Load | Power (W) | Current (A) |
|-------------|------|-----------|-------------|
| 1000 | Light | ~50 | ~0.2 |
| 2000 | Medium | ~150 | ~0.6 |
| 3000 | Full | ~300 | ~1.2 |
| 4000 | Over | ~450 | ~1.8 |

---

## 2. Pavg_ref Derivation

### 2.1 Power Balance Principle

For a PMSM drive, the average power drawn from the DC-link equals the mechanical power output plus losses:

$$P_{avg} = P_{mech} + P_{cu} + P_{core} + P_{inv}$$

Where:
- $P_{mech} = T_e \cdot \omega_m$ = mechanical output power
- $P_{cu} = 3 \cdot I_{rms}^2 \cdot R_s$ = copper losses
- $P_{core}$ = core losses (typically 2-5% of rated)
- $P_{inv}$ = inverter losses (typically 1-3% of rated)

### 2.2 Simplified Pavg_ref

For control purposes, we need the **reference** average power, not the actual. The reference is:

$$P_{avg,ref} = \frac{P_{mech,ref}}{\eta}$$

Where $\eta$ is the estimated efficiency (typically 0.85-0.92 for PMSM).

### 2.3 From Speed Reference

Given speed reference $\omega_m^*$ and load torque $T_L$:

$$P_{avg,ref} = \frac{T_L \cdot \omega_m^*}{\eta}$$

For a water pump, load torque follows affinity laws:

$$T_L = k_T \cdot \omega_m^2$$

Where $k_T$ is the torque constant (depends on pump geometry).

So:

$$P_{avg,ref} = \frac{k_T \cdot \omega_m^{*3}}{\eta}$$

### 2.4 From Current Reference

Alternatively, from FOC current references:

$$P_{avg,ref} = \frac{3}{2} \cdot (u_d \cdot i_d^* + u_q \cdot i_q^*)$$

In steady state with $i_d^* = 0$ (FOC):

$$P_{avg,ref} = \frac{3}{2} \cdot u_q \cdot i_q^*$$

Where $u_q \approx \omega_e \psi_f$ (back-EMF dominated).

### 2.5 Practical Implementation

For the TMS320F28035 implementation:

```
// Pavg_ref calculation
// Method 1: From speed and load
P_avg_ref = k_T * omega_ref^3 / eta

// Method 2: From current references
P_avg_ref = 1.5 * u_q * i_q_ref

// Method 3: From DC-link voltage and current
P_avg_ref = V_dc * I_dc_avg

// Recommended: Use Method 1 for feedforward,
// Method 2 for feedback, Method 3 for monitoring
```

---

## 3. 22µF DC-Link Ripple Model

### 3.1 Fundamental Ripple Mechanism

In a single-phase rectified system, the DC-link voltage has a ripple at twice the grid frequency (100 Hz for 50 Hz, 120 Hz for 60 Hz).

For a single-phase full-bridge rectifier with capacitor $C_{dc}$:

$$\Delta V_{dc} = \frac{I_{load}}{2 \cdot f_{grid} \cdot C_{dc}}$$

Where:
- $\Delta V_{dc}$ = peak-to-peak voltage ripple
- $I_{load}$ = DC-link load current
- $f_{grid}$ = grid frequency (50 or 60 Hz)
- $C_{dc}$ = DC-link capacitance

### 3.2 Numerical Calculation

For $C_{dc} = 22\mu F$, $f_{grid} = 50 Hz$ (worst case), $I_{load} = 1.2 A$ (full load):

$$\Delta V_{dc} = \frac{1.2}{2 \times 50 \times 22 \times 10^{-6}} = \frac{1.2}{2.2 \times 10^{-3}} = 545 V$$

**This is larger than the DC voltage itself!** This means 22µF is far too small for a simple rectifier-capacitor topology.

### 3.3 Active Power Decoupling Required

With 22µF, the system **must** use active power decoupling (APD) or a similar technique. The capacitor cannot passively filter the 100/120 Hz ripple.

### 3.4 Ripple Model with Active Decoupling

With APD, the ripple is actively compensated. The remaining ripple depends on the APD bandwidth and gain.

For a well-designed APD:

$$\Delta V_{dc,actual} = \frac{\Delta V_{dc,open}}{1 + G_{APD}(j\omega) \cdot H(j\omega)}$$

Where:
- $G_{APD}(j\omega)$ = APD controller gain at ripple frequency
- $H(j\omega)$ = plant transfer function

### 3.5 Alternative: Single-Phase Inverter Topology

For single-phase input, the DC-link ripple is inherent. The system may use:

1. **Active Power Decoupling (APD)**: Separate converter to absorb ripple
2. **Phase-shifted interleaving**: Multiple stages with phase shift
3. **Large capacitor**: Not feasible with 22µF
4. **High switching frequency**: Reduces high-frequency ripple, not fundamental

### 3.6 Three-Phase Input Alternative

If the system uses three-phase input, the ripple is much smaller:

$$\Delta V_{dc} = \frac{I_{load}}{6 \cdot f_{grid} \cdot C_{dc}}$$

For three-phase, $f_{grid} = 50 Hz$, $I_{load} = 1.2 A$:

$$\Delta V_{dc} = \frac{1.2}{6 \times 50 \times 22 \times 10^{-6}} = \frac{1.2}{6.6 \times 10^{-3}} = 182 V$$

Still large, but more manageable with active control.

---

## 4. Ripple Magnitude Table

### 4.1 Single-Phase Input (No APD)

| Speed (rpm) | Power (W) | I_dc (A) | ΔV_dc (V) | % of 300V | Feasible? |
|-------------|-----------|----------|-----------|-----------|-----------|
| 1000 | 50 | 0.22 | 100 | 33% | NO |
| 2000 | 150 | 0.67 | 303 | 101% | NO |
| 3000 | 300 | 1.33 | 606 | 202% | NO |
| 4000 | 450 | 2.00 | 909 | 303% | NO |

### 4.2 Three-Phase Input (No APD)

| Speed (rpm) | Power (W) | I_dc (A) | ΔV_dc (V) | % of 300V | Feasible? |
|-------------|-----------|----------|-----------|-----------|-----------|
| 1000 | 50 | 0.22 | 33 | 11% | MARGINAL |
| 2000 | 150 | 0.67 | 101 | 34% | NO |
| 3000 | 300 | 1.33 | 202 | 67% | NO |
| 4000 | 450 | 2.00 | 303 | 101% | NO |

### 4.3 With Active Power Decoupling

Assuming APD with 20 dB gain at 100 Hz:

| Speed (rpm) | Open-loop ΔV | With APD (÷10) | % of 300V | Feasible? |
|-------------|--------------|----------------|-----------|-----------|
| 1000 | 100 V | 10 V | 3.3% | YES |
| 2000 | 303 V | 30 V | 10% | YES |
| 3000 | 606 V | 61 V | 20% | MARGINAL |
| 4000 | 909 V | 91 V | 30% | MARGINAL |

---

## 5. Sensorless FOC Robustness Under Ripple

### 5.1 Impact on SMO

The sliding mode observer estimates back-EMF from current measurements. DC-link voltage ripple affects:

1. **Current measurement**: Ripple causes current distortion
2. **Voltage command**: Inverter output affected by DC-link variation
3. **Position estimation**: Error increases with ripple

### 5.2 Robustness Condition

For stable sensorless FOC, the voltage ripple should satisfy:

$$\frac{\Delta V_{dc}}{V_{dc}} < \frac{1}{SNR_{min}}$$

Where $SNR_{min}$ is the minimum signal-to-noise ratio for the observer.

Typical requirement: $\frac{\Delta V_{dc}}{V_{dc}} < 10\%$

### 5.3 Assessment

| Scenario | Ripple % | Observer Stability |
|----------|----------|-------------------|
| No APD, single-phase | 33-303% | UNSTABLE |
| No APD, three-phase | 11-101% | UNSTABLE at high load |
| With APD (20dB) | 3-30% | STABLE at low load, MARGINAL at high |

---

## 6. Design Rules

### 6.1 Capacitor Selection

For 22µF to be feasible:
1. **Must use three-phase input** (reduces ripple by 3x)
2. **Must use active power decoupling** (reduces ripple by 10-20x)
3. **Or**: Use larger capacitance (but violates electrolytic-capacitorless goal)

### 6.2 Pavg_ref Control Strategy

1. **Feedforward**: $P_{avg,ref} = k_T \cdot \omega_m^{*3} / \eta$
2. **Feedback**: Adjust based on DC-link voltage error
3. **Ripple compensation**: Add harmonic injection based on observer

### 6.3 Acceptable Ripple Limits

| Parameter | Limit | Rationale |
|-----------|-------|-----------|
| Voltage ripple | < 10% of V_dc | Observer stability |
| Current ripple | < 5% of I_rated | Torque quality |
| Speed ripple | < 2% of speed | Pump performance |

---

## 7. Critical Assumptions

1. **Three-phase input assumed**: Single-phase with 22µF is not feasible without APD
2. **APD available**: Active power decoupling is required
3. **Steady-state analysis**: Transient behavior not modeled
4. **Ideal SMO**: Observer dynamics not coupled to DC-link dynamics
5. **Constant efficiency**: η = 0.9 assumed for all operating points

---

## 8. Recommendations

1. **Confirm input topology**: Is it single-phase or three-phase?
2. **If single-phase**: APD is mandatory, budget for additional converter
3. **If three-phase**: 22µF may work with careful design
4. **Derive Pavg_ref**: Use speed-cube relationship for pump load
5. **Model ripple coupling**: Include DC-link dynamics in FOC simulation
6. **Test robustness**: Validate SMO under predicted ripple conditions
