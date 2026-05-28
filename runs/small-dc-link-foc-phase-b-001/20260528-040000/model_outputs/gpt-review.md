# GPT Review: Phase B-001 I-f Startup

## Score: 76/100 — PASS_WITH_NOTES

## Verdict

| Area | Verdict |
|------|---------|
| startup_structure | PASS |
| theta_source_mux_usage | PASS |
| observer_convergence_model | WEAK |
| ramp_profile | PASS_WITH_NOTES |
| transition_speed_30rad_s | MARGINAL |
| blend_duration_100ms | PLAUSIBLE |
| dc_link_startup_assessment | PASS_WITH_NOTES |

## Key Corrections

### 1. Observer Model Too Simplistic
- Current: θ_err = V_noise/(ke × ω_m) — only noise term
- Needed: θ_total = θ_noise + θ_lpf_delay + θ_deadtime + θ_param_error
- Biggest omission: LPF phase delay in SMO at low speed

### 2. ke/ψf/Kt Convention Unresolved
- ke=0.15 V/(rad/s) vs ψf=0.08 Wb from earlier derivations — not interchangeable
- Must define: ke_phase_peak, ke_line_rms, ψf, Kt explicitly
- Without this, observer lock speed can be off 2-4×

### 3. 30 rad/s Transition Speed Marginal
- At 30 rad/s mech: E_bemf ≈ 4.5V (if ke=0.15 V/(rad/s mech))
- If ψf=0.15 Wb: E_bemf ≈ 18V (much better)
- Recommendation: 30 rad/s = observer-check speed, 50-80 rad/s = safe transition

### 4. Blend Must Be Observer-Gated
- Current: time-based alpha = t/T_blend
- Needed: gated blend requiring observer_valid, speed_valid, θ_err < threshold, Vdc > Vdc_min
- Suggested: start blend θ_err < 45°, continue < 30°, complete FOC < 15-20° for N samples

### 5. Add APD Precharge State
- Startup sequence should be: PRECHARGE_APD → CHECK_VDC_READY → ALIGN → I_F_RAMP → OBSERVER_CHECK → BLEND → FOC
- APD must be active before ALIGN to maintain Vdc

### 6. S-Curve Ramp Instead of Linear
- Linear Δω_e=2.0 rad/sample → α_m=5000 rad/s² → reaches 30 rad/s in 6ms (very aggressive)
- Use S-curve or jerk-limited ramp
- Include J/load torque in sweep

### 7. Add Safety Checks
- IqLimiter active during ramp
- SVPWM saturation check in state transitions
- Fault exits: Vdc_UVLO, Vapd_OV/UV, overcurrent, observer_invalid_timeout

## Recommended Revised State Machine

```
PRECHARGE_APD → CHECK_VDC_READY → ALIGN → I_F_RAMP → OBSERVER_CHECK → BLEND → FOC
                                                                         ↓
                                                                    FAULT (any check fail)
```
