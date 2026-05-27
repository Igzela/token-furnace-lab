# Claude Code — 22µF DC-Link Energy Balance Envelope (Corrected)

## 1. System Definition

### Target System

| Parameter | Value | Notes |
|-----------|-------|-------|
| DC-link capacitance C_dc | 22 µF | Electrolytic-capacitorless |
| Nominal DC voltage V_dc | 300 Vdc | From 212 Vac single-phase |
| Input topology | Single-phase | Worst case (derivation-001) |
| Grid frequency f_grid | 50 Hz | 100 Hz ripple |
| Motor type | PMSM | Surface-mounted, water pump |
| Control | Sensorless FOC | SMO-based |
| Platform | TMS320F28035 | 60 MHz, fixed-point |

### Why Energy-Based (Not Small-Ripple)

Derivation-001 showed that ΔV = I/(2fC) gives 545V > 300V, meaning the small-ripple assumption collapses. The energy approach works for ANY ripple magnitude because it tracks stored energy directly.

---

## 2. Single-Phase Input Power Model

### 2.1 Instantaneous Input Power

For single-phase rectifier with power factor correction (or assuming sinusoidal input current in phase with voltage):

$$P_{in}(t) = V_{ac}(t) \cdot i_{ac}(t) = V_{peak} \sin(\omega t) \cdot I_{peak} \sin(\omega t)$$

$$P_{in}(t) = \frac{V_{peak} I_{peak}}{2} [1 - \cos(2\omega t)]$$

$$P_{in}(t) = P_{avg} [1 - \cos(2\omega_{grid} t)]$$

Where:
- P_avg = V_peak · I_peak / 2 = V_rms · I_rms (average input power)
- ω_grid = 2π · f_grid
- 2ω_grid = 100 Hz (for 50 Hz grid)

**Key insight**: Single-phase input power pulsates at 100 Hz with amplitude equal to the average power. The instantaneous power swings between 0 and 2·P_avg.

### 2.2 Energy Input per Cycle

Energy delivered in one 100 Hz cycle (T = 1/100 = 10 ms):

$$E_{in,cycle} = P_{avg} \cdot T = P_{avg} / 100$$

But the energy is not constant — it pulsates. The **excess** energy during the positive half-cycle must be stored in C_dc, and the **deficit** during the negative half-cycle must be supplied from C_dc.

---

## 3. DC-Link Capacitor Energy Equation

### 3.1 Stored Energy

$$E_c(t) = \frac{1}{2} C_{dc} V_{dc}(t)^2$$

At nominal voltage:
$$E_{c,nom} = \frac{1}{2} \times 22 \times 10^{-6} \times 300^2 = 0.99 \text{ J}$$

### 3.2 Energy Balance

The fundamental energy balance is:

$$\frac{dE_c}{dt} = P_{in}(t) - P_{out}(t)$$

Where:
- P_in(t) = P_avg · [1 - cos(2ω_grid t)] (single-phase input)
- P_out(t) = motor output power + losses (assumed approximately constant over 100 Hz cycle for high-inertia loads)

### 3.3 Energy Swing per 100 Hz Cycle

The energy swing ΔE over one cycle is determined by the integral of the power difference:

$$\Delta E = \int_0^{T/2} [P_{in}(t) - P_{out}] dt$$

For the worst case where P_out = P_avg (constant load):

$$\Delta E = \int_0^{T/2} P_{avg} [1 - \cos(2\omega t)] - P_{avg} \, dt$$

$$\Delta E = P_{avg} \int_0^{T/2} [-\cos(2\omega t)] dt$$

$$\Delta E = P_{avg} \left[-\frac{\sin(2\omega t)}{2\omega}\right]_0^{T/2}$$

$$\Delta E = P_{avg} \cdot \frac{1}{2\omega} [\sin(0) - \sin(\omega T)]$$

Since ωT = 2π (one full cycle of 2ω):

$$\Delta E = P_{avg} \cdot \frac{1}{2 \cdot 2\pi f_{grid}} [0 - 0] = 0$$

This shows that over a full cycle, net energy transfer is zero. But within the cycle, energy swings. The **peak energy swing** occurs at the quarter-cycle point:

$$\Delta E_{peak} = \int_0^{T/4} P_{avg} [-\cos(2\omega t)] dt$$

$$= P_{avg} \cdot \frac{1}{2\omega} [-\sin(2\omega t)]_0^{T/4}$$

$$= P_{avg} \cdot \frac{1}{4\pi f_{grid}} [-\sin(\pi) + \sin(0)]$$

$$= P_{avg} \cdot \frac{1}{4\pi f_{grid}}$$

For f_grid = 50 Hz:

$$\Delta E_{peak} = \frac{P_{avg}}{4\pi \times 50} = \frac{P_{avg}}{628.3}$$

**This is the energy that must be absorbed by C_dc (or alternatives) during each half-cycle.**

### 3.4 Numerical Values

| P_avg (W) | ΔE_peak (J) | % of E_c,nom |
|-----------|-------------|---------------|
| 50 | 0.080 | 8.0% |
| 150 | 0.239 | 24.1% |
| 300 | 0.477 | 48.2% |
| 450 | 0.716 | 72.3% |

**Critical finding**: At 300W, the energy swing is 48% of total stored energy. At 450W, it's 72%. The capacitor alone cannot absorb this without extreme voltage variation.

---

## 4. Vdc Envelope from Energy Balance

### 4.1 Voltage from Energy

From E = ½CV²:

$$V_{dc}(t) = \sqrt{\frac{2 E_c(t)}{C_{dc}}}$$

### 4.2 Minimum Voltage

The minimum voltage occurs when stored energy is at its minimum:

$$E_{c,min} = E_{c,nom} - \Delta E_{peak}$$

$$V_{dc,min} = \sqrt{\frac{2(E_{c,nom} - \Delta E_{peak})}{C_{dc}}}$$

$$= \sqrt{V_{dc,nom}^2 - \frac{2\Delta E_{peak}}{C_{dc}}}$$

### 4.3 Numerical Vdc_min

| P_avg (W) | ΔE_peak (J) | Vdc_min (V) | % of 300V |
|-----------|-------------|-------------|-----------|
| 50 | 0.080 | 286 | 95.3% |
| 150 | 0.239 | 246 | 82.0% |
| 300 | 0.477 | 216 | 72.0% |
| 450 | 0.716 | 54 | 18.0% |

**CORRECTION**: Previous version listed 173V for 300W. Correct value is 216V. The 173V figure corresponds to ~490W, not 300W.

### 4.4 Maximum Voltage

Similarly, maximum voltage occurs at peak energy:

$$V_{dc,max} = \sqrt{V_{dc,nom}^2 + \frac{2\Delta E_{peak}}{C_{dc}}}$$

| P_avg (W) | Vdc_max (V) | % of 300V |
|-----------|-------------|-----------|
| 50 | 314 | 104.7% |
| 150 | 354 | 118.0% |
| 300 | 365 | 121.7% |
| 450 | 462 | 154.0% |

**CORRECTION**: Previous version listed 415V for 300W. Correct value is 365V.

---

## 5. Maximum Allowed Output Power

### 5.1 Constraint: Vdc_min ≥ Vdc_required

The motor needs a minimum DC voltage to produce the required back-EMF and current:

$$V_{dc,min} \geq V_{dc,required}(\omega_m)$$

For PMSM: V_dc,required ≈ k_e · ω_e + I_q · R_s + margin

Where:
- k_e = back-EMF constant (V/Hz or V/(rad/s))
- ω_e = electrical speed = p · ω_m (p = pole pairs)
- R_s = phase resistance
- margin = dead-time + switching + control margin (~10-20V)

### 5.2 From Vdc_min Constraint

$$V_{dc,nom}^2 - \frac{2\Delta E_{peak}}{C_{dc}} \geq V_{dc,required}^2$$

$$\Delta E_{peak} \leq \frac{C_{dc}}{2}(V_{dc,nom}^2 - V_{dc,required}^2)$$

$$\frac{P_{avg}}{4\pi f_{grid}} \leq \frac{C_{dc}}{2}(V_{dc,nom}^2 - V_{dc,required}^2)$$

$$P_{avg,max} = 2\pi f_{grid} \cdot C_{dc} \cdot (V_{dc,nom}^2 - V_{dc,required}^2)$$

### 5.3 Numerical P_max vs Speed

Assuming k_e = 0.15 V/(rad/s), p = 4, R_s = 2Ω, margin = 15V:

| Speed (rpm) | ω_m (rad/s) | V_dc,req (V) | P_avg,max (W) | Feasible? |
|-------------|-------------|--------------|---------------|-----------|
| 1000 | 104.7 | 82 | 984 | YES |
| 2000 | 209.4 | 149 | 893 | YES |
| 3000 | 314.2 | 216 | 696 | YES |
| 4000 | 418.9 | 283 | 321 | MARGINAL |

**Low-line (Vnom = 237V)**:

| Speed (rpm) | V_dc,req (V) | P_avg,max (W) | 300W feasible? |
|-------------|--------------|---------------|----------------|
| 1000 | 82 | 670 | YES |
| 2000 | 149 | 579 | YES |
| 3000 | 216 | 383 | MARGINAL |
| 4000 | 283 | 107 | NO — derate to 107W |

**Note**: At 4000rpm low-line, Pmax drops to 107W — system cannot deliver 300W. Power derating is mandatory for low-line operation at high speed.

---

## 6. Three-Branch Absorption Analysis

### 6.1 Branch 1: Capacitor Absorption

22µF can absorb ΔE_peak = 0.477J at 300W. This causes Vdc to swing from 300V to 216V (28% drop) and up to 365V (22% rise). Total swing: 149V peak-to-peak (49.7%pp).

**Verdict**: Capacitor alone is insufficient for stable bus. Voltage swing is too large for standard FOC.

### 6.2 Branch 2: Mechanical Inertia Absorption

If the motor/pump system absorbs the 100Hz power pulsation, the speed will oscillate:

$$J \frac{d\omega_m}{dt} = T_e - T_L$$

The speed ripple amplitude:

$$\Delta\omega_m \approx \frac{\Delta E_{peak}}{J \cdot \omega_m}$$

For J = 0.001 kg·m² (typical small pump), ω_m = 3000 rpm = 314 rad/s:

$$\Delta\omega_m \approx \frac{0.477}{0.001 \times 314} = 1.52 \text{ rad/s} = 14.5 \text{ rpm}$$

Speed ripple: 14.5 / 3000 = 0.48% — **acceptable for pump application**.

**Verdict**: Mechanical inertia can absorb significant 100Hz pulsation with minimal speed ripple. This is the most promising branch for 22µF operation.

### 6.3 Branch 3: Active Power Decoupling

APD requires additional hardware (capacitor/inductor + converter) to absorb the 100Hz energy. As shown in derivation-001, 22µF alone has E_usable ≈ 0.099J (for ±15V), far less than the 0.477J needed at 300W.

**Verdict**: APD is possible but requires dedicated energy storage hardware. Cannot be done with 22µF alone.

---

## 7. Safe Operating Envelope

### 7.1 Envelope Definition

The safe operating envelope is defined by:

1. **Vdc_min constraint**: Vdc_min ≥ Vdc_required(ω_m)
2. **Vdc_max constraint**: Vdc_max ≤ Vdc_rated (capacitor/inverter voltage rating)
3. **Speed ripple constraint**: Δω_m / ω_m < 2% (pump application)
4. **Torque ripple constraint**: T_ripple/T_avg < 30% (acoustic/noise limit)
5. **Current limit**: I_q_peak ≤ I_max at all times

### 7.2 Operating Region

For single-phase + 22µF + mechanical inertia absorption (J=1e-3 kg·m²):

| Speed (rpm) | P_max_volt (W) | P_max_torque (W) | P_max_actual (W) | Speed ripple (%) | Torque ripple (%) | Status |
|-------------|----------------|------------------|------------------|------------------|-------------------|--------|
| 1000 | 670 | 57 | 57 | 0.15% | 30% | LIMITED |
| 2000 | 579 | 113 | 113 | 0.04% | 30% | LIMITED |
| 3000 | 383 | 170 | 170 | 0.02% | 30% | LIMITED |
| 4000 | 107 | 226 | 107 | 0.03% | 30% | LIMITED |

**P_max_torque** = 0.3 × ω_m × k_t × I_rated (torque ripple constraint: T_ripple/T_avg < 30%)
**P_max_actual** = min(P_max_volt, P_max_torque)

**Key finding**: Torque ripple is the binding constraint, not voltage. At 3000rpm, voltage allows 383W but torque ripple limits to 170W. **300W is NOT achievable with mechanical inertia absorption alone** at any speed — APD or larger capacitance required for full power.

### 7.3 Derating at Low Speed

At low speed, Vdc_required is lower, so more energy swing is allowed. But mechanical inertia absorption is less effective (lower ω_m → larger speed ripple per ΔE). The crossover occurs around 1500-2000 rpm.

### 7.4 Low-Line Analysis (168Vac Critical Finding)

At low-line input 168Vac → Vdc_peak = 168 × √2 = 237V:

| Speed (rpm) | Vdc_req (V) | Pmax at Vnom=237V (W) | 300W feasible? | Action |
|-------------|-------------|----------------------|----------------|--------|
| 1000 | 82 | 670 | YES | Full power |
| 2000 | 149 | 579 | YES | Full power |
| 3000 | 216 | 383 | YES | Full power |
| 4000 | 283 | 107 | NO | Derate to 107W |

**Critical**: At 4000rpm low-line, maximum power is only 107W — system cannot deliver 300W. Even at 3000rpm, the margin is thin (383W vs 300W required).

With stricter Vdc_req (e.g., Vreq = 216V to maintain 72% Vdc margin):

| Speed (rpm) | Pmax at Vnom=237V, Vreq=216V (W) | 300W feasible? |
|-------------|-----------------------------------|----------------|
| 1000 | 670 | YES |
| 2000 | 579 | YES |
| 3000 | 138 | NO |
| 4000 | — | NO (Vreq > Vnom) |

**Verdict**: 300W is NOT feasible at low-line 168Vac for speeds ≥ 3000rpm with 22µF. Power derating is mandatory.

### 7.5 Pmax vs Vnom vs Vreq Lookup Table

Formula: P_max = 2π × 50 × 22e-6 × (Vnom² - Vreq²) = 6.908e-3 × (Vnom² - Vreq²)

**Vnom = 300V (212Vac input)**:

| Vreq (V) | Pmax (W) | Vswing (V) | Vswing (%pp) |
|-----------|----------|------------|---------------|
| 173 | 488 | 173-415 | 80.7% |
| 200 | 391 | 200-383 | 60.9% |
| 216 | 321 | 216-365 | 49.7% |
| 250 | 166 | 250-341 | 30.3% |
| 270 | 83 | 270-325 | 18.2% |

**Vnom = 237V (168Vac low-line)**:

| Vreq (V) | Pmax (W) | Vswing (V) | Vswing (%pp) |
|-----------|----------|------------|---------------|
| 150 | 587 | 150-303 | 67.0% |
| 173 | 488 | 173-285 | 44.8% |
| 200 | 253 | 200-263 | 26.7% |
| 216 | 138 | 216-254 | 16.2% |

**Vnom = 354V (250Vac high-line)**:

| Vreq (V) | Pmax (W) | Vswing (V) | Vswing (%pp) |
|-----------|----------|------------|---------------|
| 173 | 842 | 173-497 | 95.5% |
| 200 | 745 | 200-473 | 81.9% |
| 216 | 675 | 216-456 | 72.1% |
| 250 | 521 | 250-430 | 53.0% |
| 283 | 337 | 283-410 | 38.7% |

**Key insight**: At high-line (354V), 300W is feasible even at 4000rpm (Vreq=283V → Pmax=337W). At low-line (237V), 300W is only feasible below ~2500rpm.

### 7.6 Speed Ripple vs Inertia Lookup Table

Formula: Δω_m/ω_m = ΔE_peak / (J × ω_m²) × 100%

For P_out = P2 (100Hz ripple amplitude = average power):

| J (kg·m²) | Speed (rpm) | P2=100W | P2=200W | P2=300W |
|-----------|-------------|---------|---------|---------|
| 1e-4 | 1000 | 1.45% | 2.90% | 4.34% |
| 1e-4 | 2000 | 0.36% | 0.72% | 1.09% |
| 1e-4 | 3000 | 0.16% | 0.32% | 0.48% |
| 1e-4 | 4000 | 0.09% | 0.18% | 0.27% |
| 5e-4 | 1000 | 0.29% | 0.58% | 0.87% |
| 5e-4 | 2000 | 0.07% | 0.14% | 0.22% |
| 5e-4 | 3000 | 0.03% | 0.06% | 0.10% |
| 5e-4 | 4000 | 0.02% | 0.04% | 0.05% |
| 1e-3 | 1000 | 0.15% | 0.29% | 0.43% |
| 1e-3 | 2000 | 0.04% | 0.07% | 0.11% |
| 1e-3 | 3000 | 0.02% | 0.03% | 0.05% |
| 1e-3 | 4000 | 0.01% | 0.02% | 0.03% |

**Acceptability thresholds** (pump application):
- < 0.5%: Acceptable
- 0.5% - 1.0%: Marginal — audible noise possible
- > 1.0%: Unacceptable — significant acoustic/vibration issues

**Key finding**: For J ≥ 5e-4 kg·m² and speed ≥ 2000rpm, speed ripple stays below 0.5% even at 300W. For J = 1e-4 (very small motor), 300W at 1000rpm gives 4.34% — unacceptable.

### 7.7 Torque Ripple Cost of Mechanical Inertia Absorption

**Hidden cost**: When mechanical inertia absorbs the 100Hz power pulsation, the torque and current must ripple proportionally.

Torque ripple amplitude:
$$T_2 = \frac{P_2}{\omega_m}$$

For P2 = 300W (worst case, full power as ripple):

| Speed (rpm) | ω_m (rad/s) | T2 (N·m) | T_avg (N·m) | Tripple/Tavg |
|-------------|-------------|----------|-------------|---------------|
| 1000 | 104.7 | 2.87 | 2.87 | 100% |
| 2000 | 209.4 | 1.43 | 1.43 | 100% |
| 3000 | 314.2 | 0.95 | 0.95 | 100% |
| 4000 | 418.9 | 0.72 | 0.72 | 100% |

**The torque ripple amplitude equals the average torque.** This means:

1. **q-axis current ripple**: I_q must ripple by the same ratio as torque
   - At 3000rpm: I_q_avg = 0.95/0.15 = 6.3A, I_q_ripple = 6.3A (100% modulation)
   - Peak I_q = 12.6A — exceeds rated 3A by 4x

2. **Copper losses**: RMS current increases by √(1 + 0.5²) = 1.12x → 12% more losses

3. **Acoustic noise**: 100Hz torque ripple audible in pump

4. **Current limiting pressure**: Peak current may trigger protection

**Verdict**: Mechanical inertia absorption is NOT free — it converts the bus energy problem into a torque/current/acoustic problem. The 100% torque ripple at full power is severe. In practice, this means:
- The system cannot operate at full 300W with 22µF and mechanical inertia absorption alone
- Actual sustainable power with mechanical absorption: ~50-100W (where Tripple/Tavg < 30%)
- For full 300W, APD or larger capacitance is required

---

## 8. dc_link_constraints Interface

```yaml
dc_link_constraints:
  # Voltage limits
  Vdc_min_allowed:
    1000rpm: 237V
    2000rpm: 237V
    3000rpm: 237V
    4000rpm: 283V
  Vdc_max_allowed: 400V  # capacitor/inverter rating
  ripple_pp_allowed: "not applicable — energy-based, not ripple-based"

  # Power limits (single-phase, 22µF, torque ripple constrained)
  # Torque ripple is binding: T_ripple/T_avg < 30%
  Pout_avg_max_by_speed:
    1000rpm: 57W
    2000rpm: 113W
    3000rpm: 170W
    4000rpm: 107W
  note: "300W NOT achievable with mechanical inertia absorption alone"

  # Current limits
  Iq_limit_by_vdc:
    300V: 15A
    250V: 12A
    200V: 9A

  # Derating curve (power vs Vdc)
  derating_curve:
    type: "Vdc-dependent with mechanical inertia absorption"
    formula: "P_max = 2π·f_grid·Cdc·(Vdc_nom² - Vdc_req²)"

  # Observer valid region
  observer_valid_region:
    min_speed: 1500rpm  # SMO needs sufficient back-EMF
    max_ripple_pct: "N/A — energy-based envelope"
    vdc_min_for_observer: "depends on speed and back-EMF constant"
```

---

## 9. Comparison: Energy-Based vs Small-Ripple

| Aspect | Small-Ripple (derivation-001) | Energy-Based (derivation-002) |
|--------|-------------------------------|-------------------------------|
| Formula | ΔV = I/(2fC) | ΔE = P/(4πf), V = √(2E/C) |
| Valid range | ΔV << V_dc | Any ΔV |
| At 300W, 22µF | 545V (collapsed) | Vdc_min = 216V, Vdc_max = 365V |
| Engineering meaning | "Infeasible" | "Feasible with 50% pp voltage swing" |
| Actionable? | No — formula fails | Yes — defines operating envelope |

**The energy-based approach reveals that 22µF at 300W is feasible ONLY if:**
1. The system accepts ~50%pp Vdc swing (216-365V) — voltage constraint
2. Torque ripple constraint is relaxed or APD is added — torque constraint is binding at ~170W
3. FOC is designed for wide Vdc variation (real-time feedforward)
4. Low-line operation requires derating below 2500rpm

**Bottom line**: 22µF + 300W + single-phase + mechanical inertia alone is NOT sufficient. Need APD, three-phase input, or larger capacitance.

---

## 10. Critical Assumptions

1. **Single-phase input**: Worst case. Three-phase would reduce ΔE by ~3x.
2. **Constant output power over 100 Hz cycle**: Valid for high-inertia loads (pumps).
3. **No APD**: Pure capacitor + mechanical inertia absorption.
4. **Ideal rectifier**: No diode drops, no source impedance.
5. **Constant efficiency**: η = 0.9 for all operating points.
6. **Mechanical inertia sufficient**: J = 0.001 kg·m² assumed.

---

## 11. Recommendations

1. **300W requires APD or larger capacitance**: Mechanical inertia absorption alone limits power to ~170W at 3000rpm due to torque ripple constraint (T_ripple/T_avg < 30%). For full 300W, active power decoupling or larger DC-link capacitor is mandatory.
2. **Low-line derating is mandatory**: At 168Vac input, 300W is only feasible below ~2500rpm. At 4000rpm low-line, maximum power is 107W.
3. **Three-phase input is the strongest lever**: Reduces 100Hz energy swing by ~3x, making 22µF much more practical for 300W.
4. **Test Vdc feedforward**: SVPWM must use real-time Vdc measurement for voltage commands — critical for wide Vdc swing operation.
5. **Design current limiter**: Must reduce I_q when Vdc drops to prevent voltage saturation.
6. **Measure actual J**: Speed ripple depends on J. Larger J reduces speed ripple but does NOT reduce torque ripple (which is the binding constraint).
7. **Proceed with Phase A FOC baseline**: Independent of 22µF — validate on stable supply first.
