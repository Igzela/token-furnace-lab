# GPT Verification — 22µF DC-Link Energy Balance Envelope

## Metadata

- Experiment: small-dc-link-foc-derivation-002
- Model: GPT (ChatGPT)
- Role: Independent mathematical verification
- Date: 2026-05-27

## Verdict

**Formula is correct. Numerical results had error. Low-line analysis reveals 300W not feasible at 168Vac.**

## 1. Energy Model Formula Verification

$$P_{max} = 2\pi f_{grid} C_{dc} (V_{nom}^2 - V_{req}^2)$$

**Verdict: CORRECT** under assumptions:
- Vnom is energy-center voltage (not necessarily arithmetic average)
- Vreq is allowed minimum bus voltage
- Pout approximately constant
- Pin is ideal single-phase unity power factor
- Ignores rectifier conduction, source impedance, diode drops

## 2. Corrected Voltage Envelope

For P=300W, C=22µF, f=50Hz, Vnom=300V:

Energy term: P/(2πfC) = 300/(2π×50×22e-6) ≈ 43,405 V²

Vmin = √(300² - 43,405) = √46,595 ≈ **216V**
Vmax = √(300² + 43,405) = √133,405 ≈ **365V**

**Previous 173-415V was WRONG** — that corresponds to ~490W, not 300W.

## 3. Low-Line Analysis (Critical Finding)

At 168Vac input → Vdc_peak = 237V:

- Same 300W: Vmin ≈ 113V (infeasible for FOC)
- With Vreq=173V: Pmax ≈ 181W
- With Vreq=216V: Pmax ≈ 66W

**300W is NOT feasible at low-line 168Vac with 22µF.** Power derating required.

## 4. Mechanical Inertia Absorption

Formula: Δω_m/ω_m = P2 / (Ω · J · ω_m²)

At 4000rpm, P2=300W:
- For 0.48% amplitude: J ≈ 5.7e-4 kg·m²
- For 0.48% peak-peak: J ≈ 1.1e-3 kg·m²

**0.48% depends entirely on J.** Without measuring J, cannot conclude.

### Hidden Cost: Torque/Current Ripple

T2 = P2/ω_m = 300/419 ≈ 0.72 N·m (amplitude)
Tavg = 300/419 ≈ 0.72 N·m

**Torque ripple amplitude equals average torque.** This means:
- q-axis current ripple is significant
- Copper losses increase
- Acoustic noise and vibration
- Current limiting pressure

Mechanical inertia absorption is NOT free — it converts bus energy problem into torque/current/acoustic problem.

## 5. Engineering Conclusion

```yaml
energy_model:
  verdict: valid
  formula: P_max = 2π f C (Vnom² - Vreq²)

300W_22uF_300V:
  corrected_voltage_envelope: 216V-365V
  verdict: energy-feasible only if large Vdc swing acceptable

low_line_168Vac:
  verdict: not feasible at 300W
  Pmax_at_173Vreq: 181W
  Pmax_at_216Vreq: 66W

mechanical_inertia_absorption:
  verdict: plausible but unverified
  hidden_cost: torque ripple amplitude ≈ average torque
  required_input: total inertia J
```

## 6. Required Corrections

1. Fix voltage envelope: 216-365V (not 173-415V)
2. Add low-line analysis table
3. Add Pmax vs Vnom vs Vreq table
4. Add speed ripple vs inertia table
5. Document torque ripple cost of mechanical absorption
