# Phase C-001: DC-Link Voltage Ripple Management Model

## 1. DC-Link Voltage Ripple Equation

For single-phase input with 22µF DC-link:

```
ΔVpp = P / (2·ω_line·Cdc·Vdc_avg)
```

Where:
- P = output power (W)
- ω_line = 2π×50 = 314 rad/s (single-phase rectified)
- Cdc = 22µF
- Vdc_avg = 300V

**Example**: P=300W → ΔVpp = 300/(2×314×22e-6×300) = 72V (24%pp)

## 2. APD Decoupling Model

With APD active power decoupling:

```
Vdc_ripple_eff = Vdc_ripple × (1 - K_apd)
```

Where K_apd = APD decoupling factor (0 to 1):
- K_apd = 0: no decoupling
- K_apd = 0.9: 90% decoupling (from derivation-004/005)

**With 90% APD**: ΔVpp_eff = 72V × 0.1 = 7.2V (2.4%pp)

## 3. Pavg_ref Calculation

From derivation-001 (GPT corrected):

```
P_avg_ref = P₀ + k·ω³
```

Where:
- P₀ = no-load loss (friction + windage) ≈ 5-10W
- k = load coefficient (from pump curve)
- ω = mechanical speed (rad/s)

For water pump: k ≈ P_rated / ω_rated³ = 300 / 418.9³ ≈ 4.07e-6

## 4. Vdc Feedforward for SMO

The SMO observer uses Vdc to reconstruct voltage vectors. Under ripple:

```
Vdc_measured = Vdc_avg + ΔVpp/2 × sin(2·ω_line·t)
```

**Feedforward strategy**:
- Use filtered Vdc (LPF, fc=100Hz) for observer
- Feedforward actual Vdc to SVPWM modulation index
- Limits: Vdc_min = Vdc_avg - ΔVpp/2, Vdc_max = Vdc_avg + ΔVpp/2

## 5. IqLimiter Design

Vdc-aware Iq limiting:

```
Vdc_min = Vdc_avg - ΔVpp_eff/2
Vreq_max = √(Vdc_min²/3 - (ω_e·Ls·Id)²) / (ω_e·Ls)
Iq_max = min(I_rated, Vreq_max)
```

When Vdc dips:
- Iq_max decreases proportionally
- Speed PI output limited by Iq_max
- Prevents voltage saturation of inverter

## 6. SVPWM Saturation Strategy

When Vdc drops below minimum for commanded voltage:

1. **Overmodulation**: Allow 5th harmonic injection (up to 15% voltage boost)
2. **Field weakening**: Reduce Id to negative for high-speed operation
3. **Iq reduction**: Limit Iq to maintain voltage margin
4. **Anti-windup**: Freeze integrator when saturated

**Priority**: Vdc stability > torque accuracy > speed accuracy

## 7. Integration with Startup (B-004)

Startup state machine additions for DC-link management:

```
SM_PRECHARGE:
  - APD precharge to Vapd_target
  - Monitor Vdc ripple during precharge
  - Verify APD decoupling active before ALIGN

SM_IF_RAMP:
  - Vdc feedforward active
  - IqLimiter monitoring Vdc_min
  - If Vdc < Vdc_min_for_speed → fault

SM_FOC:
  - Full DC-link management active
  - APD tracking Pavg_ref
  - Vdc feedforward to SMO
  - IqLimiter dynamic limiting
```
