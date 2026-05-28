# Fixed-Point Range Audit — Phase A-004

## Overview

TMS320F28035 uses C28x fixed-point (16-bit integer, IQmath library). All signals must be represented without overflow across the full operating range.

**Operating range**: 0-4000rpm, 0-300V Vdc, ±10A phase current, ±20A peak

## Signal Table

| Signal | Q Format | Range | LSB | Max Value | Overflow Risk | Notes |
|--------|----------|-------|-----|-----------|---------------|-------|
| **Phase Currents (Ia, Ib)** | Q15 | ±16.0A | 0.49mA | ±15.999 | LOW | 10A nominal, 20A peak. Q15 gives 0.5mA resolution. |
| **Iα, Iβ** | Q15 | ±16.0A | 0.49mA | ±15.999 | LOW | Clarke output. Same range as phase currents. |
| **Id, Iq** | Q15 | ±16.0A | 0.49mA | ±15.999 | LOW | Park output. Id ≈ 0 for FOC. Iq = torque current. |
| **theta (electrical angle)** | Q20 | 0-2π | 6µrad | 6.283 | NONE | Angle always 0-2π. Q20 gives ~1µrad resolution. |
| **omega_e (electrical speed)** | Q15 | 0-500 rad/s | 0.015 rad/s | 32767 rad/s | NONE | 4000rpm = 419 rad/s. Q15 max 32767. Huge margin. |
| **omega_m (mechanical speed)** | Q15 | 0-500 rad/s | 0.015 rad/s | 32767 rad/s | NONE | Same as omega_e (1 pole pair assumed). |
| **Vdc (DC-link voltage)** | Q12 | 0-400V | 98mV | 4095V | NONE | 300V nominal, 400V max. Q12 max 4095. |
| **Vd, Vq** | Q15 | ±310V | 9.5mV | ±32767 (scaled) | LOW | Modulation-limited to Vdc/√3 ≈ 173V. Q15 at Vdc_base=311V. |
| **Vα, Vβ** | Q15 | ±310V | 9.5mV | ±32767 (scaled) | LOW | Inverse Park output. Same range as Vd/Vq. |
| **Duty cycles (Ta, Tb, Tc)** | Q15 | 0-1.0 | 30.5µ | 0.99997 | NONE | Always 0-1. Q15 gives 30ppm resolution. |
| **PI integral (current)** | Q15 | ±4.0A | 122µA | ±3.999 | MEDIUM | Anti-windup clamp needed. Integral can accumulate. |
| **PI integral (speed)** | Q15 | ±10.0A | 305µA | ±9.999 | MEDIUM | Speed PI output = Iq_ref. Clamp to motor rating. |
| **sin(theta), cos(theta)** | Q15 | ±1.0 | 30.5µ | ±0.99997 | NONE | LUT output. Always ±1. |
| **IqLimiter limit** | Q12 | 0-10A | 2.4mA | 4095 (scaled) | LOW | Vdc-dependent. Max = rated current. |
| **SMO zα, zβ** | Q15 | ±16.0A | 0.49mA | ±15.999 | LOW | Observer correction term. Bounded by current range. |
| **SMO omega_hat** | Q15 | 0-500 rad/s | 0.015 rad/s | 32767 | NONE | Estimated speed. Same range as omega_e. |
| **APD energy** | Q15 | 0-5.0 J | 153µJ | 32767 (scaled) | LOW | E = 0.5*C*Vdc^2. Max at 300V: 0.5*16µF*300^2 = 0.72J. |
| **APD current** | Q15 | ±5.0A | 153µA | ±4.999 | LOW | APD inductor current. Max ±3A typical. |
| **Temperature** | Q8 | 0-200°C | 0.78°C | 255°C | NONE | 8-bit unsigned. Sufficient for NTC range. |
| **Fault flags** | bitmap | 0-65535 | 1 flag | 65535 flags | NONE | 16-bit bitmap for fault codes. |

## Overflow Risk Analysis

### HIGH Risk: None identified
All signals have adequate Q-format range for the operating conditions.

### MEDIUM Risk: PI Integrators
- **Current PI integral**: Can accumulate to large values if output is clamped but input persists.
  - **Mitigation**: Anti-windup clamp on integral term. Clamp to ±4.0A (Q15 range).
  - **Verification**: Check that clamp value × Ki doesn't exceed Q15 range.

- **Speed PI integral**: Similar issue. Output = Iq_ref, must be clamped to motor rating.
  - **Mitigation**: Anti-windup clamp. Clamp to ±rated current.

### Multiplication Overflow Risk

| Operation | Input Q | Input Q | Result Q | Max Product | Risk |
|-----------|---------|---------|----------|-------------|------|
| Ia × sin(θ) | Q15 | Q15 | Q30 → Q15 | 1.0 × 1.0 = 1.0 | LOW (shift right 15) |
| Vdc × Kp | Q12 | Q15 | Q27 → Q15 | 400 × 32767 | LOW (Kp typically < 1.0) |
| omega × Ki | Q15 | Q15 | Q30 → Q15 | 500 × 0.1 = 50 | LOW |
| E = 0.5×C×V² | Q15 | Q12 | Q27 → Q15 | 0.5 × 16µ × 90000 | LOW (small constants) |

**Key**: C28x `MPY` instruction produces 32-bit result from 16×16. IQmath `_mpy()` handles Q format automatically. Overflow only occurs if the 32-bit result is shifted back to 16-bit and exceeds ±32768.

### Division Risk

| Operation | Dividend | Divisor | Risk |
|-----------|----------|---------|------|
| atan2(y, x) | Q15 | Q15 | NONE (IQmath `atan2DP`) |
| Vdc / Vdc_rated | Q12 | Q12 | NONE (normalized) |
| Speed / Speed_rated | Q15 | Q15 | NONE (normalized) |

Division is rare in FOC. Most operations use multiply-accumulate. IQmath provides `_divq15()` which is safe for normalized inputs.

## Recommended Q Formats

| Signal | Recommended Q | Rationale |
|--------|---------------|-----------|
| Phase currents | Q15 | 0.5mA resolution, ±16A range covers 20A peak |
| Voltage (Vdc, Vd, Vq) | Q12 | 98mV resolution, 4095V max covers 300V nominal |
| Angle | Q20 | 6µrad resolution, covers 0-2π exactly |
| Speed | Q15 | 0.015 rad/s resolution, 32767 rad/s max |
| Duty cycle | Q15 | 30ppm resolution, 0-1 range |
| PI gains | Q12 | Kp typically 0.01-1.0, Ki typically 0.001-0.1 |
| PI integral | Q15 | Anti-windup clamped |
| sin/cos LUT | Q15 | ±1.0 range, 256 entries |

## Conclusion

**No Q-format overflow risk identified** for the target operating range (0-4000rpm, 0-300V, ±10A). PI integrators require anti-windup clamping but are not an overflow risk. All multiplications produce results within C28x 32-bit intermediate range before shifting back to 16-bit.

The primary risk is **precision loss** in PI integral terms when gains are very small (Ki < 0.001). This is a control performance issue, not an overflow issue. Mitigate by using Q12 for gains and Q15 for integrals.
