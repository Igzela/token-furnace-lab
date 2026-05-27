# GPT Verification — derivation-004 (APD Sizing)

## Metadata

- Experiment: small-dc-link-foc-derivation-004
- Model: GPT (ChatGPT)
- Role: Verification of APD sizing
- Date: 2026-05-28

## Verdict: PASS_WITH_TWO_CORRECTIONS

Direction correct. Two critical errors caught:
1. APD capacitor formula missing factor of 2
2. Torque ripple conclusion wrong — APD DOES reduce motor-side torque ripple

---

## 1. Corrections Applied

### Correction 1: APD Capacitor Formula

**Error**: Used C = ΔE/(½·ΔV²) without factor of 2
**Correct**: C_apd = 2 × ΔE_pp / (Vmax² - Vmin²)
**Impact**: All capacitor values doubled. 12µF → 19.6µF (full), 17.6µF (90%)

### Correction 2: Torque Ripple with APD

**Error**: "APD solves voltage constraint but not torque constraint"
**Correct**: APD absorbs 100Hz power from motor side. At 90% decoupling, motor-side torque ripple = 5% rated (from 50% without APD).
**Impact**: 300W is achievable at 4000rpm with APD. Torque ripple is no longer binding.

### Correction 3: Residual DC-Link Ripple

**Error**: 19.6V / 6.5%pp
**Correct**: 14.5V / 4.8%pp (using energy-based formula)
**Impact**: Better than expected — well within SMO tolerance.

## 2. Verified Formulas

| Formula | Status | Notes |
|---------|--------|-------|
| ΔE_peak = P/(4πf) | PASS | 0.477J at 300W/50Hz |
| ΔE_pp = 2 × ΔE_peak | PASS | 0.955J |
| C_apd = 2·ΔE_pp/(Vmax²-Vmin²) | PASS (corrected) | Factor of 2 was missing |
| Residual Vpp from energy formula | PASS (corrected) | 14.5V at 90% |
| Motor torque ripple = (1-D)·P_avg/ω_m | PASS | 5% at 90% decoupling |

## 3. GPT's Key Insight

"APD 不能解决的是：平均转矩能力、热限制、电压饱和限制、低线母线最低电压限制、高线过压限制。但它可以显著解决由单相二倍频功率引起的 100Hz 转矩纹波。"

Translation: APD cannot solve average torque capability, thermal limits, voltage saturation, low-line minimum voltage, or high-line overvoltage. But it CAN significantly reduce 100Hz torque ripple caused by single-phase power pulsation.

## 4. Engineering Conclusion

With 90% APD decoupling:
- DC-link residual ripple: 4.8%pp ✓
- Motor torque ripple: 5% rated ✓
- 300W achievable at 3000-4000rpm ✓
- Remaining constraints: high-line overvoltage (240W), low-line speed limit (3670rpm)
