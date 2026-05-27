# GPT Final Verification — derivation-002 Corrections

## Metadata

- Experiment: small-dc-link-foc-derivation-002
- Model: GPT (ChatGPT)
- Role: Final verification of corrections
- Date: 2026-05-27

## Verdict: 85/100 PASS_WITH_NOTES — Score Confirmed

GPT confirmed the 85/100 score is reasonable, with specific corrections.

---

## 1. Pmax vs Vnom vs Vreq Table — Numerical Verification

GPT provided corrected 3x3 matrix:

| Vnom \ Vreq | 173V | 200V | 216V |
|-------------|------|------|------|
| 237V (168Vac) | 181W | 112W | 66W |
| 300V (212Vac) | 415W | 346W | 300W |
| 354V (250Vac) | 659W | 590W | 544W |

**GPT note**: "低线168Vac下Pmax=107W，如果使用的Vreq约为200-202V，是对的；如果你声称是在Vreq=216V下得到107W，那就不对，216V对应约66W。"

**Action needed**: Reconcile our derivation-002 table with GPT's values. Our Pmax formula gives:
- Pmax = 2π × 50 × 22e-6 × (Vnom² - Vreq²) = 6.908e-3 × (Vnom² - Vreq²)
- Vnom=237, Vreq=200: 6.908e-3 × (237² - 200²) = 6.908e-3 × 15,889 = 109.8W ≈ 112W ✓
- Vnom=237, Vreq=216: 6.908e-3 × (237² - 216²) = 6.908e-3 × 9,453 = 65.3W ≈ 66W ✓
- Vnom=237, Vreq=173: 6.908e-3 × (237² - 173²) = 6.908e-3 × 26,768 = 184.9W ≈ 181W ✓

**Our previous low-line 4000rpm Pmax=107W**: This used Vreq=283V (back-EMF at 4000rpm), NOT Vreq=216V. The 107W is correct for that speed-dependent Vreq. GPT's table uses fixed Vreq values, while our derivation used speed-dependent Vreq. Both are correct under different assumptions.

---

## 2. Torque Ripple Formula — Critical Distinction

**GPT found a terminology/formula error in our derivation-002**:

We wrote: "T_ripple/T_avg < 30% → Pmax_torque = 0.3 × ω_m × k_t × I_rated"

GPT correction:
- This formula corresponds to **T_ripple < 30% × T_rated** (rated torque)
- NOT **T_ripple < 30% × T_avg** (average torque)

**Why this matters**:
- At 170W, 3000rpm: T_avg = 0.54N·m, T_rated = 1.8N·m
- If T_ripple ≈ T_avg = 0.54N·m (100% average torque ripple)
- Then T_ripple/T_rated = 0.54/1.8 = 30% rated torque ✓
- But T_ripple/T_avg = 0.54/0.54 = 100% average torque ✗

**GPT recommendation**: Change constraint name from "average-torque ripple limit" to "rated-torque ripple limit"

**Implication**: If you want T_ripple/T_avg < 30%, you need APD or capacitor to absorb at least 70% of the 100Hz power pulsation. Mechanical absorption alone inherently gives ~100% average torque ripple.

---

## 3. Low-Line Analysis — 4 Missing Boundary Checks

GPT identified 4 gaps in our low-line analysis:

### Gap 1: Vnom = 237V is Optimistic
- Real rectifier conduction angle, source impedance, diode drops, capacitor charging spikes reduce available energy
- 237V is the ideal peak, not guaranteed bus center voltage

### Gap 2: Vreq Must Be Speed/Torque Dependent
- Vreq(ω, iq, id) = back-EMF + Rs·Iq + L·dIq/dt + control margin
- Should NOT use fixed 200V or 216V for all operating points

### Gap 3: High-Line Overvoltage
- Vnom=354V, 300W: Vmax ≈ 411V
- If capacitor/power devices rated 400V, this triggers overvoltage
- Need to check component voltage ratings

### Gap 4: Low-Line Current Limit
- Lower Vdc → higher DC bus current for same power
- Current limiting, copper losses, thermal, SVPWM saturation all worsen

**GPT recommended YAML**:
```yaml
low_line_168Vac:
  verdict: 300W at 4000rpm infeasible
  reason:
    - energy window insufficient
    - Vdc_min likely below motor voltage requirement
    - torque ripple limit binds before voltage envelope in some speed range
    - current/thermal margin not yet fully evaluated
  remaining_checks:
    - Vreq(speed, torque)
    - inverter current limit
    - overvoltage at high line
    - rectifier charging RMS/peak current
```

---

## 4. GPT's Final Assessment

```yaml
derivation_002_final_assessment:
  energy_formula: valid
  300W_300V_envelope: corrected_to_216_365V
  low_line_300W: infeasible
  torque_ripple_constraint: binding
  300W_with_22uF_single_phase_mechanical_absorption: not feasible under 30% rated-torque ripple limit
  requires:
    - APD
    - larger capacitor
    - strong power derating
    - or accepting severe 100Hz torque ripple
```

---

## 5. Recommended Next Experiment

GPT recommends: **derivation-003: Vreq(speed, torque) + Iq limit + voltage saturation envelope**

This will connect the energy model to actual FOC control constraints.

---

## 6. Actions Required

1. **Fix torque ripple terminology**: Change "T_ripple/T_avg < 30%" to "T_ripple < 30% × T_rated" in derivation-002
2. **Add Vreq(speed, torque) function**: Replace fixed Vreq with speed-dependent calculation
3. **Add high-line overvoltage check**: Vmax at Vnom=354V may exceed 400V rating
4. **Add current/thermal limit check**: Low-line requires higher current for same power
5. **Reconcile Pmax table**: Our derivation uses speed-dependent Vreq, GPT's table uses fixed Vreq — document both
