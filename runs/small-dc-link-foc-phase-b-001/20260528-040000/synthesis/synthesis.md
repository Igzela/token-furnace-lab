# Phase B-001: I-f Startup + Smooth FOC Transition — Synthesis

## Score: 76/100 (PASS_WITH_NOTES) — GPT Final

**Rationale**: I-f startup structurally sound. GPT identified critical gaps: observer model too simplistic, ke/ψf convention unresolved, blend must be observer-gated, APD precharge needed. 168/216 configs pass simulation, but model optimism acknowledged.

## Key Findings

### 1. Startup Sequence (Revised per GPT)

| Phase | Duration | Notes |
|-------|----------|-------|
| PRECHARGE_APD | ~100ms | Ensure Vapd near energy center, Vdc ready |
| ALIGN | 200ms | DC current 1.5A, rotor to known position |
| I-f RAMP | ~6-200ms | S-curve, Δω_e = 0.5-2.0 rad/sample |
| OBSERVER_CHECK | — | Require θ_err bounded for N samples |
| BLEND | 100ms | Observer-gated α, angle + current handoff |
| FOC | — | Full sensorless FOC |
| **Total** | **~300-500ms** | **Standstill → FOC** |

### 2. Sweep Results

- 216 configs swept, 168 passed (77.8%)
- Best: Δω_e=2.0, I_start=1.0A, ω_start=30 rad/s, θ_err=16°, T=303ms
- Failures: 48 configs with θ_err > 45° (high Δω_e + high ω_start)

### 3. GPT Corrections (Critical)

1. **Observer model**: Must include LPF delay, deadtime error, param error — not just noise
2. **ke/ψf convention**: Unresolved — ke=0.15 vs ψf=0.08 from earlier derivations. Must define explicitly
3. **30 rad/s**: Marginal for observer lock — use as check speed, not guaranteed transition
4. **Blend**: Must be observer-gated (θ_err < 45° start, < 30° continue, < 15-20° complete)
5. **APD precharge**: Add PRECHARGE_APD state before ALIGN
6. **S-curve ramp**: Linear too aggressive (6ms to 30 rad/s). Use jerk-limited
7. **Safety checks**: IqLimiter, SVPWM saturation, fault exits (UVLO, OV, OC)

### 4. Revised State Machine (GPT Recommended)

```
PRECHARGE_APD → CHECK_VDC_READY → ALIGN → I_F_RAMP → OBSERVER_CHECK → BLEND → FOC
                                                                         ↓
                                                                    FAULT
```

### 5. Angle Error Budget (Revised)

| Source | Error | Model |
|--------|-------|-------|
| Observer noise | ~5° | V_noise/(ke×ω_m) |
| LPF phase delay | ~5-10° | Not modeled (GPT correction) |
| Deadtime voltage | ~2-3° | Not modeled (GPT correction) |
| Param error | ~2-5° | Not modeled (GPT correction) |
| **Total** | **~14-23°** | **Optimistic without LPF/deadtime** |

## Decision Record

**I-f startup is feasible** but needs corrections before implementation:
- Observer model must be expanded (LPF, deadtime, param error)
- ke/ψf/Kt convention must be resolved (critical for accuracy)
- Blend must be observer-gated, not time-based
- APD precharge state required
- S-curve ramp recommended over linear
- Score: 76/100 PASS_WITH_NOTES
