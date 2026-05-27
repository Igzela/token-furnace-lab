# Claude Code — FOC Voltage Requirement and Saturation Envelope (derivation-003, Corrected)

## 1. System Definition

### Motor Parameters

| Parameter | Symbol | Value | Units | Notes |
|-----------|--------|-------|-------|-------|
| Pole pairs | p | 4 | - | |
| Phase resistance | R_s | 2.0 | Ω | |
| Phase inductance | L_s | 5.0 | mH | L_d = L_q (surface PMSM) |
| Back-EMF constant | ψ_f | 0.08 | V/(rad/s) | Revised — see §1.1 |
| Torque constant | k_t | 0.48 | N·m/A | k_t = 1.5 × p × ψ_f |
| Rated current | I_rated | 3.0 | A (rms) | Motor continuous rating |
| Rated speed | n_rated | 4000 | rpm | |
| Moment of inertia | J | 0.001 | kg·m² | |

**Revision note (ψ_f)**: Original used ψ_f = 0.15, giving back-EMF = 188.5V at 4000rpm — exceeding Vlim = 155.9V at Vdc=300V. Motor cannot spin to 4000rpm. Revised to ψ_f = 0.08 (back-EMF = 134V at 4000rpm, below Vlim at Vdc=300V).

**Torque formula**: For 3-phase surface PMSM with id=0:
$$T_e = \frac{3}{2} \cdot p \cdot \psi_f \cdot I_q = 1.5 \times 4 \times 0.08 \times I_q = 0.48 \cdot I_q$$

At I_rated = 3A: T_rated = 0.48 × 3 = 1.44 N·m

### DC-Link & SVPWM Parameters

| Parameter | Symbol | Value | Units |
|-----------|--------|-------|-------|
| DC-link capacitance | C_dc | 22 | µF |
| Nominal DC voltage (212Vac) | V_nom | 300 | V |
| Low-line DC voltage (168Vac) | V_nom_low | 237 | V |
| High-line DC voltage (250Vac) | V_nom_high | 354 | V |
| Modulation limit | m_limit | 0.90 | - |
| Voltage limit | V_lim | m_limit × V_dc / √3 | V |

---

## 2. Steady-State dq Voltage Model

### 2.1 PMSM Voltage Equations (dq frame)

For surface-mounted PMSM (L_d = L_q = L_s), with FOC (I_d* = 0):

$$V_d = -\omega_e \cdot L_s \cdot I_q$$

$$V_q = R_s \cdot I_q + \omega_e \cdot \psi_f$$

Where ω_e = p · ω_m (electrical speed).

### 2.2 Required Phase Voltage Magnitude

$$V_{req} = \sqrt{V_d^2 + V_q^2} = \sqrt{(\omega_e L_s I_q)^2 + (R_s I_q + \omega_e \psi_f)^2}$$

### 2.3 SVPWM Voltage Limit

$$V_{lim} = m_{limit} \cdot \frac{V_{dc}}{\sqrt{3}}$$

| Vdc (V) | V_lim (V) | V_lim² |
|---------|-----------|--------|
| 216 | 112.2 | 12,589 |
| 237 | 123.0 | 15,129 |
| 300 | 155.9 | 24,301 |
| 354 | 184.0 | 33,856 |

### 2.4 Voltage Saturation Condition

$$V_d^2 + V_q^2 \leq V_{lim}^2$$

---

## 3. Maximum Feasible Speed (Back-EMF Limit)

At Iq=0, motor can operate only if back-EMF ≤ Vlim:

$$\omega_{e,max} = \frac{V_{lim}}{\psi_f} = \frac{m_{limit} \cdot V_{dc}}{\sqrt{3} \cdot \psi_f}$$

$$\omega_{m,max} = \frac{\omega_{e,max}}{p}$$

| Vdc (V) | ω_e,max (rad/s) | ω_m,max (rad/s) | n_max (rpm) |
|---------|-----------------|-----------------|-------------|
| 216 | 1402.5 | 350.6 | 3349 |
| 237 | 1537.5 | 384.4 | 3670 |
| 300 | 1949.4 | 487.3 | 4655 |
| 354 | 2299.3 | 574.8 | 5490 |

**Critical**: At Vdc=216V, max speed = 3349 rpm (no-load). At Vdc=237V, max = 3670 rpm. **4000rpm NOT feasible at Vdc ≤ 237V**.

---

## 4. I_q Maximum from Voltage Constraint

### 4.1 Quadratic Inequality

$$A \cdot I_q^2 + B \cdot I_q + C' \leq 0$$

Where:
- A = (ω_e · L_s)² + R_s²
- B = 2 · R_s · ω_e · ψ_f
- C' = (ω_e · ψ_f)² - V_lim²

Positive root:

$$I_{q,max} = \frac{-B + \sqrt{B^2 - 4 A C'}}{2A}$$

If B² - 4AC' < 0 → infeasible (back-EMF > Vlim).

### 4.2 Corrected I_q_max Table

| Speed (rpm) | Vdc=216V | Vdc=237V | Vdc=300V | Vdc=354V |
|-------------|----------|----------|----------|----------|
| 1000 | 3.0A | 3.0A | 3.0A | 3.0A |
| 2000 | 3.0A | 3.0A | 3.0A | 3.0A |
| 2500 | 3.0A | 3.0A | 3.0A | 3.0A |
| 3000 | 3.0A | 3.0A | 3.0A | 3.0A |
| 3119 | 3.0A (limit) | 3.0A | 3.0A | 3.0A |
| 3349 | 0A (infeasible) | 3.0A | 3.0A | 3.0A |
| 3500 | INFEASIBLE | 2.28A | 3.0A | 3.0A |
| 4000 | INFEASIBLE | INFEASIBLE | 3.0A | 3.0A |

**Key**: At Vdc=216V, Iq_max = 3.0A up to ~3119 rpm, then drops. At 3349rpm, Iq_max = 0 (back-EMF = Vlim).

**Verification at 3000rpm/Vdc=216V**:
- Back-EMF = 1256.6 × 0.08 = 100.5V < Vlim = 112.2V ✓
- Iq_max = 4.24A > I_rated → limited to 3.0A ✓

**Verification at 4000rpm/Vdc=216V**:
- Back-EMF = 1675.5 × 0.08 = 134.0V > Vlim = 112.2V → **INFEASIBLE** ✓

**Verification at 4000rpm/Vdc=300V**:
- Back-EMF = 134.0V < Vlim = 155.9V ✓
- Iq_max = 6.33A > I_rated → limited to 3.0A ✓

---

## 5. Vreq(speed, Iq) Function

### 5.1 Formula

$$V_{req}(\omega_m, I_q) = \sqrt{(\omega_e L_s I_q)^2 + (R_s I_q + \omega_e \psi_f)^2}$$

### 5.2 Numerical Vreq Table

| Speed (rpm) | Iq=1A | Iq=2A | Iq=3A |
|-------------|-------|-------|-------|
| 1000 | 36.0V | 39.5V | 44.8V |
| 2000 | 70.0V | 75.2V | 83.2V |
| 3000 | 104.5V | 111.5V | 122.0V |
| 4000 | 139.5V | 148.2V | 160.8V |

---

## 6. Operating Region Map

### 6.1 Three Constraints

$$P_{max,actual} = \min(P_{max,voltage}, P_{max,torque}, P_{max,thermal})$$

Where:
- P_max_voltage = I_q_max × ω_m × k_t (voltage saturation limit)
- P_max_torque = 0.3 × T_rated × ω_m (30% rated-torque ripple limit)
- P_max_thermal = I_rated × ω_m × k_t (motor thermal limit)

### 6.2 Constraint Values

**P_max_torque** (30% rated-torque ripple limit):
T_rated = 1.44 N·m, 30% = 0.432 N·m

| Speed (rpm) | P_max_torque (W) |
|-------------|------------------|
| 1000 | 45.2W |
| 2000 | 90.4W |
| 3000 | 135.7W |
| 3500 | 157.9W |
| 4000 | 180.9W |

**P_max_thermal** = 3.0 × ω_m × 0.48

| Speed (rpm) | P_max_thermal (W) |
|-------------|-------------------|
| 1000 | 143.9W |
| 2000 | 287.8W |
| 3000 | 431.7W |
| 4000 | 575.6W |

**P_max_voltage** = I_q_max × ω_m × 0.48

| Speed (rpm) | Vdc=216V | Vdc=237V | Vdc=300V | Vdc=354V |
|-------------|----------|----------|----------|----------|
| 1000 | 143.9W | 143.9W | 143.9W | 143.9W |
| 2000 | 287.8W | 287.8W | 287.8W | 287.8W |
| 3000 | 452.4W | 452.4W | 452.4W | 452.4W |
| 3500 | INFEASIBLE | 331.6W | 452.4W | 452.4W |
| 4000 | INFEASIBLE | INFEASIBLE | 603.2W | 603.2W |

### 6.3 Actual Operating Region

$$P_{max,actual} = \min(P_{max,voltage}, P_{max,torque}, P_{max,thermal})$$

| Speed (rpm) | Vdc=216V | Vdc=237V | Vdc=300V | Vdc=354V | Binding |
|-------------|----------|----------|----------|----------|---------|
| 1000 | 45.2W | 45.2W | 45.2W | 45.2W | Torque ripple |
| 2000 | 90.4W | 90.4W | 90.4W | 90.4W | Torque ripple |
| 3000 | 135.7W | 135.7W | 135.7W | 135.7W | Torque ripple |
| 3500 | INFEASIBLE | 157.9W | 157.9W | 157.9W | Torque ripple |
| 4000 | INFEASIBLE | INFEASIBLE | 180.9W | 180.9W | Torque ripple |

**Torque ripple is ALWAYS the binding constraint** where the motor can operate.

### 6.4 300W Feasibility Under 30% Rated-Torque Ripple

To deliver 300W at 3000rpm:
Need: 0.432 × 314.2 ≥ 300 → 135.7 ≥ 300 → **NOT FEASIBLE**

To deliver 300W at any speed:
Need: 0.432 × ω_m ≥ 300 → ω_m ≥ 694.4 rad/s → n ≥ 6632 rpm

**300W requires ≥ 6632 rpm under 30% rated-torque ripple limit with mechanical absorption.** This is far above the motor's rated speed (4000 rpm).

---

## 7. High-Line Overvoltage Check

### 7.1 Vmax at Vnom=354V

From derivation-002: At 300W, Vnom=354V:

$$V_{max} = \sqrt{V_{nom}^2 + \frac{P}{2\pi f C}} = \sqrt{354^2 + \frac{300}{2\pi \times 50 \times 22 \times 10^{-6}}}$$

$$= \sqrt{125316 + 43406} = \sqrt{168722} = 410.8V$$

### 7.2 Component Voltage Ratings

- Typical electrolytic capacitor: 400V or 450V rated
- Typical IGBT/MOSFET: 600V rated

**Vmax = 410.8V > 400V capacitor rating!**

### 7.3 Safe High-Line Power

For Vmax ≤ 400V:

$$P_{max} = 2\pi f C (400^2 - V_{nom}^2)$$

| Vnom (V) | P_max (W) | Vmax at Pmax |
|----------|-----------|--------------|
| 300 | 588W | 400V |
| 354 | 240W | 400V |
| 380 | 82W | 400V |

At Vnom=354V (250Vac): Maximum safe power = 240W (limited by 400V capacitor rating).

---

## 8. dc_link_constraints Updated YAML

```yaml
dc_link_constraints:
  # Motor parameters (corrected)
  motor:
    p: 4                    # pole pairs
    psi_f: 0.08             # V/(rad/s) — back-EMF constant
    k_t: 0.48               # N·m/A — torque constant (= 1.5 × p × ψ_f)
    L_s: 0.005              # H — phase inductance
    R_s: 2.0                # Ω — phase resistance
    I_rated: 3.0            # A (rms) — motor continuous rating
    T_rated: 1.44           # N·m — rated torque (= k_t × I_rated)

  # SVPWM limits
  svpwm:
    m_limit: 0.90
    Vlim_formula: "m_limit × Vdc / sqrt(3)"

  # Maximum feasible speed (back-EMF limit, Iq=0)
  max_speed_by_vdc:
    216V: 3349rpm
    237V: 3670rpm
    300V: 4655rpm
    354V: 5490rpm

  # Voltage saturation: Iq_max(Vdc, speed)
  # From quadratic: A·Iq² + B·Iq + C' ≤ 0
  Iq_max_by_speed_and_vdc:
    1000rpm:
      216V: 3.0A
      237V: 3.0A
      300V: 3.0A
      354V: 3.0A
    2000rpm:
      216V: 3.0A
      237V: 3.0A
      300V: 3.0A
      354V: 3.0A
    3000rpm:
      216V: 3.0A
      237V: 3.0A
      300V: 3.0A
      354V: 3.0A
    3500rpm:
      216V: INFEASIBLE
      237V: 2.28A
      300V: 3.0A
      354V: 3.0A
    4000rpm:
      216V: INFEASIBLE
      237V: INFEASIBLE
      300V: 3.0A
      354V: 3.0A

  # Power limits (three-constraint minimum)
  # Torque ripple always binding: 30% rated-torque ripple limit
  Pout_avg_max_by_speed:
    1000rpm: 45.2W
    2000rpm: 90.4W
    3000rpm: 135.7W
    3500rpm: 157.9W
    4000rpm: 180.9W
  note: "300W requires ≥ 6632rpm under 30% rated-torque ripple limit"

  # High-line overvoltage
  highline_overvoltage:
    Vnom_354V:
      Pmax_300W_Vmax: 410.8V   # EXCEEDS 400V rating
      Pmax_safe_400V: 240W     # limited by capacitor voltage rating

  # Low-line feasibility
  lowline_derating:
    Vnom_237V:
      max_speed: 3670rpm
      3000rpm: 135.7W
      3500rpm: 157.9W
      4000rpm: INFEASIBLE
```

---

## 9. Key Findings

### Finding 1: ψ_f Must Be ≤ 0.103 for 300V/4000rpm

With ψ_f = 0.15 (original), back-EMF at 4000rpm = 188.5V > Vlim = 155.9V. Motor cannot operate.
Maximum ψ_f for 300V/4000rpm: ψ_f ≤ Vlim/ωe = 155.9/1675.5 = 0.093 V/(rad/s) (with m_limit=0.90).

### Finding 2: Maximum Speed Limited by Vdc

| Vdc (V) | Max Speed (rpm) |
|---------|-----------------|
| 216 | 3349 |
| 237 | 3670 |
| 300 | 4655 |
| 354 | 5490 |

At Vdc=216V (300W energy minimum), motor cannot exceed 3349 rpm. At Vdc=237V, cannot exceed 3670 rpm.

### Finding 3: Torque Ripple Always Binds

With ψ_f = 0.08 and mechanical absorption:
- P_max_torque: 45-181W (30% rated-torque ripple limit)
- P_max_voltage: 144-603W (where feasible)
- P_max_thermal: 144-576W

Torque ripple is always the binding constraint.

### Finding 4: 300W Requires ≥ 6632 rpm

Under 30% rated-torque ripple limit with mechanical absorption:
P_max = 0.432 × ω_m ≥ 300 → ω_m ≥ 694 rad/s → n ≥ 6632 rpm

This is 66% above the motor's rated speed (4000 rpm). **300W is not achievable at rated speed under this constraint.**

### Finding 5: High-Line Overvoltage

At Vnom=354V (250Vac), 300W: Vmax = 410.8V > 400V capacitor rating.
Maximum safe power at high-line: 240W.

### Finding 6: Low-Line 4000rpm Infeasible

At Vdc=237V (168Vac), 4000rpm: Back-EMF (134V) > Vlim (123V). Motor cannot operate.
Maximum speed at low-line: 3670 rpm.

---

## 10. Recommendations

1. **300W requires APD or higher speed**: Under 30% rated-torque ripple limit, 300W needs ≥ 6632 rpm. Either add APD to absorb 100Hz power pulsation, or accept higher torque ripple.
2. **Use 450V capacitor**: For high-line (250Vac) operation, 400V rating is insufficient at 300W.
3. **Low-line derating**: At 168Vac, maximum speed is 3670 rpm. 4000rpm operation requires Vdc ≥ 260V.
4. **Consider three-phase input**: Reduces 100Hz energy swing by ~3x, making 22µF more practical.
5. **Proceed with Phase A-002**: FOC implementation with corrected ψ_f = 0.08.
