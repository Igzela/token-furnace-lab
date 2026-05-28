# Phase B-002: Corrected I-f Startup Model

## Goal

Apply GPT corrections from Phase B-001 (76/100 PASS_WITH_NOTES) to produce a corrected startup model.

## GPT Corrections to Apply

1. **Observer model**: Expand θ_err = V_noise/(ke×ω_m) to include LPF delay, deadtime error, param error
2. **ψ_f = 0.08 Wb**: Use corrected flux linkage from derivation-003 (not ke=0.15)
3. **Observer-gated blend**: Blend only when θ_err < threshold, not purely time-based
4. **APD precharge state**: Add PRECHARGE_APD before ALIGN
5. **S-curve ramp**: Replace linear Δω_e with jerk-limited ramp
6. **Safety checks**: IqLimiter, SVPWM saturation, fault exits (UVLO, OV, OC)
7. **State machine**: PRECHARGE → CHECK_VDC → ALIGN → I_F_RAMP → OBSERVER_CHECK → BLEND → FOC

## Corrected Motor Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| ψ_f | 0.08 Wb | derivation-003 (corrected from 0.15) |
| Kt | 0.48 Nm/A | 1.5 × p × ψ_f |
| ke (phase) | 0.08 V/(rad/s elec) | ψ_f |
| T_rated at 3A | 1.44 Nm | Kt × I_rated |
| 300W at 4000rpm | 0.72 Nm needed | P/ω = 300/419 |

## Required Outputs

1. Corrected simulation model with expanded observer
2. Sweep with corrected parameters
3. Comparison with Phase B-001 results
4. GPT re-review
