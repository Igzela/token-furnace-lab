# Phase E-001: GPT Review

## Score: 72/100 — PASS_WITH_NOTES

**Verdict**: PASS_WITH_NOTES
**Implementation ready**: No — needs corrections before implementation

## Summary

GPT identified 7 major corrections needed:

1. **Missing hard-fault paths** — vdc_ov, vapd_ov, pwm_tripzone, gate_driver_fault, watchdog, adc_fault, over_temperature, emergency_stop
2. **CONTROLLED_COAST unsafe** — Split into PASSIVE_COAST (PWM disabled) and CONTROLLED_DECEL (PWM active)
3. **Observer freeze too optimistic** — 2s frozen θ unsafe at 4000rpm; use extrapolated-theta bridge (10-20ms), then recovery or coast
4. **Vdc derating formula too crude** — Use derivation-003 voltage model, not linear scaling
5. **APD fault derating not topology-aware** — Three-phase may continue; single-phase must check ripple model
6. **Restart logic wrong** — Should go through PRECHARGE → ALIGN, not OPEN_LOOP_RECOVERY
7. **Retry policy needs fault classes** — Hard faults = no retry, recoverable = 3 retries, critical = manual only

## Detailed Corrections

### 1. Missing Hard-Fault Paths

Events that must route to FAULT_LATCHED from every active state:
- vdc_ov, vapd_ov, vapd_uv, pwm_tripzone, gate_driver_fault
- watchdog_reset, adc_invalid/saturation, current_sensor_fault
- apd_inductor_oc, over_temperature, dc_bus_precharge_fail
- emergency_stop/user_disable

Rule: OC, OV, gate_driver_fault, PWM_tripzone, watchdog, emergency_stop → FAULT_LATCHED + PWM disable immediately.

### 2. CONTROLLED_COAST Split

Replace single CONTROLLED_COAST with:
- **PASSIVE_COAST**: PWM disabled, motor freewheels. Safest for hard electrical faults.
- **CONTROLLED_DECEL**: PWM active, Id/Iq controlled. Only allowed if Vdc/Vapd/current sensing healthy.

UVLO → PASSIVE_COAST. OV/OC/gate fault → FAULT_LATCHED. Observer loss → controlled derate.

### 3. Observer Freeze Duration

Replace "freeze θ for 2s" with phased approach:
- 0-10ms: extrapolated theta = theta_last + omega_last × dt, freeze speed PI, derate Iq to 20-50%
- 10-100ms: if observer recovers → FOC_DERATED → FOC_NORMAL; else → PASSIVE_COAST
- >100ms: do not keep active FOC on frozen theta

### 4. Vdc Derating Formula

Use derivation-003 voltage model:
```
Iq_allowed = min(I_rated, Iq_voltage_max(Vdc, omega))
```
Not linear Vdc scaling. Auto-recovery: Vdc > 270V for 1s AND no SVPWM saturation.

### 5. APD Fault Topology Awareness

- Three-phase: may continue without APD if Vdc ripple/saturation OK
- Single-phase: P_limit = safe_no_apd_power(Cdc=22µF, Vdc, ripple_limit). If too low → controlled coast.

### 6. Restart Logic Fix

If speed_zero:
```
RESTART_PENDING → PRECHARGE → ALIGN → IF_RAMP → OBSERVER_CHECK → BLEND → FOC
```

If motor still spinning (speed_est > 0 or BEMF detected):
```
RESTART_PENDING → FLYING_RESTART or OPEN_LOOP_RECOVERY
```

### 7. Fault Classes for Retry

```yaml
hard_fault_no_retry:
  events: [oc_trip, vdc_ov, gate_driver_fault, pwm_tripzone, emergency_stop]
  action: FAULT_LATCHED, manual reset

recoverable_fault_retry_3:
  events: [vdc_uvlo, stall, startup_tmo, observer_lost]
  action: 3 retries with escalation

degraded_operation:
  events: [vdc_low, apd_fault, svpwm_sat, iq_clamp, sensor_drift]
  action: derate, no retry needed

manual_intervention:
  events: [user_fault, precharge_fail]
  action: FAULT_LATCHED, requires human
```

### 8. Timing Constant Refinements

- observer_extrapolate_max: 10-20ms (not 2s freeze)
- observer_recovery_window: 0.5-2s
- svpwm_sat_short: 50ms → derate
- svpwm_sat_long: 500ms → controlled coast
- apd_fault_single_phase: immediate derate/coast based on ripple
- apd_fault_three_phase: allow longer degraded operation
- APD timeout: topology-dependent (not fixed 10s)
