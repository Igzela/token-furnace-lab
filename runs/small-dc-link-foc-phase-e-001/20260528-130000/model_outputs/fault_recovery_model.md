# Phase E-001: Runtime Fault Recovery Model (v2 — GPT-corrected)

## State Definitions

| State | Description | Motor | PWM | Controller |
|-------|-------------|-------|-----|------------|
| FOC_NORMAL | Full closed-loop FOC | Running | Active | Speed PI + Current PI + SMO |
| FOC_DERATED | Reduced performance | Running | Active | Reduced Iq, speed PI limited |
| OBSERVER_DEGRADED | Observer unreliable | Running | Active | Extrapolated θ, derated Iq, no speed PI |
| FLYING_RESTART | Motor spinning, re-syncing | Running | Active | I-f re-acquire, speed PI frozen |
| OPEN_LOOP_RECOVERY | Known-state recovery | Coasting | Active | I-f ramp or hold |
| PASSIVE_COAST | Safe freewheel | Coasting | Disabled | All outputs zero |
| CONTROLLED_DECEL | Active deceleration | Running | Active | Zero torque, controlled ramp down |
| APD_DEGRADED | APD not functioning | Running | Active | FOC without APD, topology-aware derate |
| FAULT_LATCHED | Hard fault, requires reset | Stopped | Disabled | All outputs zero |
| RESTART_PENDING | Attempting restart | Stopped | Disabled | Cooldown timer running |
| PRECHARGE | DC-link voltage ramp-up | Stopped | Disabled | Precharge relay control, Vdc monitoring |
| ALIGN | Rotor alignment pulse | Stopped | Active | Fixed current vector, fixed angle |

## Fault-State Transition Matrix

### UNIVERSAL (all active and degraded states)

```
UNIVERSAL:
  oc_trip              → FAULT_LATCHED + PWM disable (immediate, hardware trip-zone)
  gate_driver_fault    → FAULT_LATCHED + PWM disable
  pwm_tripzone         → FAULT_LATCHED + PWM disable
  emergency_stop       → FAULT_LATCHED + PWM disable
  watchdog_reset       → FAULT_LATCHED
  adc_invalid          → FAULT_LATCHED + PWM disable
  over_temperature     → FAULT_LATCHED + PWM disable
```

These transitions apply from every state where PWM is active. They are not repeated per-state below.

### Active States (PWM enabled)

```
FOC_NORMAL:
  obs_lock_lost        → OBSERVER_DEGRADED (extrapolated θ, 10-20ms bridge)
  vdc_low              → FOC_DERATED (Iq_limit = min(I_rated, Iq_voltage_max(Vdc, ω)))
  vdc_uvlo             → PASSIVE_COAST
  vdc_ov               → FAULT_LATCHED + PWM disable
  svpwm_sat_short      → FOC_DERATED (reduce Iq/speed, >50ms threshold)
  svpwm_sat_long       → CONTROLLED_DECEL (reduce speed ref, >500ms threshold)
  iq_clamp_long        → FOC_DERATED (reduce speed ref, 2s threshold)
  apd_fault            → APD_DEGRADED (topology-aware derate)
  oc_trip              → FAULT_LATCHED + PWM disable
  stall_detected       → OPEN_LOOP_RECOVERY
  gate_driver_fault    → FAULT_LATCHED + PWM disable
  pwm_tripzone         → FAULT_LATCHED + PWM disable
  watchdog_reset       → FAULT_LATCHED
  adc_invalid          → FAULT_LATCHED + PWM disable
  current_sensor_fault → FAULT_LATCHED + PWM disable
  over_temperature     → FAULT_LATCHED + PWM disable
  emergency_stop       → FAULT_LATCHED + PWM disable

FOC_DERATED:
  obs_lock_lost        → OBSERVER_DEGRADED (extrapolated θ)
  vdc_uvlo             → PASSIVE_COAST
  vdc_ov               → FAULT_LATCHED + PWM disable
  recovery_ok          → FOC_NORMAL (auto-recovery)
  timeout_5s           → CONTROLLED_DECEL
  oc_trip              → FAULT_LATCHED + PWM disable

OBSERVER_DEGRADED:
  obs_recovered        → FOC_NORMAL (if speed stable)
  obs_extrapolate_max  → PASSIVE_COAST (>10-20ms no recovery)
  vdc_uvlo             → PASSIVE_COAST
  timeout_500ms_2s     → OPEN_LOOP_RECOVERY

FLYING_RESTART:
  sync_ok              → FOC_NORMAL (observer locked)
  sync_fail            → RESTART_PENDING
  timeout_3s           → RESTART_PENDING
  vdc_uvlo             → PASSIVE_COAST
```

### Degraded States (reduced operation)

```
CONTROLLED_DECEL:
  speed_zero           → RESTART_PENDING
  vdc_uvlo             → PASSIVE_COAST
  timeout_5s           → PASSIVE_COAST

APD_DEGRADED:
  apd_recovered        → FOC_NORMAL
  vdc_uvlo             → PASSIVE_COAST
  timeout_10s (3ph)    → CONTROLLED_DECEL
  ripple_exceeds_limit (1ph) → PASSIVE_COAST (immediate)
```

### Recovery States

```
OPEN_LOOP_RECOVERY:
  speed_low            → RESTART_PENDING
  vdc_uvlo             → PASSIVE_COAST
  timeout_3s           → FAULT_LATCHED

PASSIVE_COAST:
  speed_zero           → RESTART_PENDING
  timeout_5s           → FAULT_LATCHED (motor should stop)

RESTART_PENDING:
  cooldown_done + speed_zero → PRECHARGE → ALIGN (cold start)
  cooldown_done + speed_est > 0 → FLYING_RESTART
  retry_3_failed       → FAULT_LATCHED

PRECHARGE:
  vdc_ready            → ALIGN (Vdc > target, e.g., 270V)
  timeout_500ms        → FAULT_LATCHED (precharge failed)
  oc_trip              → FAULT_LATCHED + PWM disable

ALIGN:
  align_done           → IF_RAMP (flux established, 200ms elapsed)
  timeout_200ms        → RESTART_PENDING (retry alignment)
  oc_trip              → FAULT_LATCHED + PWM disable
  retry_3_failed       → FAULT_LATCHED
```

## Recovery Strategies by Fault Type

### 1. Observer Lock Loss (FOC_NORMAL → OBSERVER_DEGRADED)

**Trigger**: θ_err > 45° for > 50 samples (5ms at 10kHz)

**Strategy**:
```
Phase 1 (0-10ms): Extrapolated-theta bridge
  θ_est = θ_last + ω_last × dt
  Freeze speed PI
  Derate Iq to 20-50%

Phase 2 (10-100ms): Recovery check
  If observer relocks (θ_err < 30° for 100 samples):
    → FOC_DERATED → FOC_NORMAL (auto-recovery)
  If no recovery:
    → PASSIVE_COAST

Phase 3 (>100ms): SAFETY — do not keep active FOC on frozen theta
  → PASSIVE_COAST
```

**Why extrapolated-theta bridge, not freeze**: At 4000rpm, frozen angle is only valid for ~1 control cycle. Extrapolation is accurate for 10-20ms at moderate speed. Long freeze (2s) is unsafe.

**Extrapolation failure detection**:
```
- Extrapolation update rate = PWM frequency (10kHz)
- If |θ_extrapolated - θ_measured| > 60° when observer partially relocks:
  → reject extrapolation → PASSIVE_COAST immediately
- If ω_last < 100 rpm (extrapolation unreliable at low speed):
  → reduce to 5ms max bridge → PASSIVE_COAST
```

### 2. Vdc Low (FOC_NORMAL → FOC_DERATED)

**Trigger**: 200V < Vdc < 250V

**Strategy**:
```
1. Physics-based current limit:
   Iq_allowed = min(I_rated, Iq_voltage_max(Vdc, ω))
2. Ramp speed reference down if voltage-limited
3. If Vdc drops to 200V: → PASSIVE_COAST
4. Auto-recovery: Vdc > 270V for 1s AND no SVPWM saturation
```

**Why derivation-003 model**: Linear Vdc scaling is crude. The voltage envelope model accounts for back-EMF and speed, giving physically correct derating.

### 3. APD Fault (FOC_NORMAL → APD_DEGRADED)

**Trigger**: Vapd out of range or APD current fault

**Strategy** (topology-dependent):
```
Three-phase input:
  - APD may not be required
  - Continue without APD if Vdc ripple/saturation OK
  - Monitor Vdc 100Hz ripple
  - Timeout 10s → CONTROLLED_DECEL

Single-phase input:
  - APD required for DC-link stability
  - P_limit = safe_no_apd_power(Cdc=22µF, Vdc, ripple_limit)
  - If P_limit < 30% rated: immediate PASSIVE_COAST
  - If P_limit >= 30% rated: derate to P_limit, timeout based on ripple
```

**Why topology-dependent**: Three-phase 22µF works without APD (derivation-002, derivation-003). Single-phase needs APD for DC-link stability. Fixed 60% derate is wrong.

**Water-hammer risk note**: If pump installation has water-hammer risk (vertical riser, no check valve), consider CONTROLLED_DECEL before PASSIVE_COAST for single-phase APD fault. Add system-level config flag: `apd_1ph_coast_mode = {IMMEDIATE, CONTROLLED}` with default IMMEDIATE.

### 4. SVPWM Saturation (FOC_NORMAL → FOC_DERATED)

**Trigger**: SVPWM saturated

**Strategy** (severity-split):
```
Short saturation (20-50ms):
  → FOC_DERATED: reduce Iq/speed reference by 20%

Long saturation (>500ms):
  → CONTROLLED_DECEL: ramp speed to zero

If saturation clears at any point:
  → gradually restore speed ref over 500ms
```

### 5. IqLimiter Clamp (FOC_NORMAL → FOC_DERATED)

**Trigger**: IqLimiter active > 2s

**Strategy**:
```
1. Reduce speed reference to match available torque
2. If clamp clears: restore speed ref over 500ms
3. If clamp persists > 5s: → CONTROLLED_DECEL
```

### 6. Overcurrent Trip

**Trigger**: |I_phase| > OC_threshold

**Strategy**:
```
1. IMMEDIATE: Disable PWM (hardware trip-zone)
2. → FAULT_LATCHED (requires manual reset)
3. No auto-retry (safety critical)
```

### 7. Pump Stall

**Trigger**: Speed < 10% of ref for 3s despite Iq > 80% of max

**Strategy**:
```
1. Reduce Iq to 50% (prevent overheating)
2. → OPEN_LOOP_RECOVERY
3. Attempt restart with I-f ramp
4. If 3 restarts fail: → FAULT_LATCHED
5. Add faster protection if current or temperature rises
```

### 8. Sensor Offset Drift

**Trigger**: ADC offset > 50 LSB from calibration value

**Strategy**:
```
1. Log warning (do not fault immediately)
2. If offset > 100 LSB: → FOC_DERATED
3. Attempt auto-recalibration during zero-current window
4. If recalibration fails: → FAULT_LATCHED
```

### 9. Watchdog Reset / Gate Driver Fault / PWM Tripzone

**Trigger**: Hardware-level fault

**Strategy**:
```
1. IMMEDIATE: PWM disabled
2. → FAULT_LATCHED (no auto-retry)
3. Manual reset required
```

### 10. Emergency Stop / User Disable

**Trigger**: User command or safety interlock

**Strategy**:
```
1. IMMEDIATE: PWM disabled
2. → FAULT_LATCHED
3. Manual reset required
```

## Restart/Retry Logic

### Fault Classes

```yaml
hard_fault_no_retry:
  events: [oc_trip, vdc_ov, gate_driver_fault, pwm_tripzone, emergency_stop, watchdog_reset]
  action: FAULT_LATCHED + PWM disable
  reset: manual only

recoverable_fault_retry_3:
  events: [vdc_uvlo, stall, startup_tmo, observer_lost]
  action: 3 retries with escalation
  profiles: [fallback_0.8A, nominal_1.0A, strong_1.2A]
  cooldown: 2s between retries

degraded_operation:
  events: [vdc_low, apd_fault, svpwm_sat, iq_clamp, sensor_drift]
  action: derate, no retry needed (auto-recovery)
  timeout: varies by fault

manual_intervention:
  events: [user_fault, precharge_fail]
  action: FAULT_LATCHED
  reset: requires human decision
```

### Cold Start Sequence (from RESTART_PENDING)

```
RESTART_PENDING:
  cooldown_timer = 2s
  retry_count++

  if retry_count >= 3:
    → FAULT_LATCHED

  if speed_est > 0 or BEMF detected:
    → FLYING_RESTART
  else:
    → PRECHARGE → ALIGN → IF_RAMP → OBSERVER_CHECK → BLEND → FOC
```

## Fault Code Table

| Code | Name | Severity | Fault Class | Auto-Recover |
|------|------|----------|-------------|--------------|
| 0 | OK | - | - | - |
| 1 | UVLO | Critical | Recoverable | 3 retries |
| 2 | OV | Critical | Hard fault | No |
| 3 | OC | Critical | Hard fault | No |
| 4 | PRECHARGE_TMO | Critical | Manual | No |
| 5 | OBSERVER_LOST | High | Recoverable | 3 retries |
| 6 | SVPWM_SAT | Medium | Degraded | Auto (reduce speed) |
| 7 | IQ_CLAMP | Medium | Degraded | Auto (reduce speed) |
| 8 | APD_FAULT | High | Topology-dependent | 3ph: auto, 1ph: coast |
| 9 | STALL | High | Recoverable | 3 retries |
| 10 | SENSOR_DRIFT | Medium | Degraded | Auto (auto-recal) |
| 11 | STARTUP_TMO | High | Recoverable | 3 retries |
| 12 | USER_FAULT | Critical | Manual | No |
| 13 | LATCHED | Critical | Hard fault | Manual reset only |
| 14 | GATE_DRIVER | Critical | Hard fault | No |
| 15 | PWM_TRIPZONE | Critical | Hard fault | No |
| 16 | WATCHDOG | Critical | Hard fault | No |
| 17 | ADC_FAULT | Critical | Hard fault | No |
| 18 | OVER_TEMP | Critical | Hard fault | No |
| 19 | EMERGENCY_STOP | Critical | Hard fault | Manual reset only |
| 20 | PRECHARGE_FAIL | Critical | Manual | No (precharge timeout) |
| 21 | ALIGN_FAIL | High | Recoverable | 3 retries (alignment timeout) |

## Timing Constants

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| observer_detect | 5ms (50 samples @ 10kHz) | Fast detection, safe margin |
| observer_extrapolate_max | 10-20ms | Extrapolated θ drift too fast at high speed |
| observer_recovery_phase2 | 10-100ms | Recovery check window after extrapolation bridge |
| observer_total_timeout | 100ms | Max time in OBSERVER_DEGRADED before PASSIVE_COAST |
| svpwm_sat_short | 50ms → derate | Early intervention |
| svpwm_sat_long | 500ms → coast | Saturation not clearing = problem |
| iq_clamp_derate | 2s | Reasonable for pump load |
| iq_clamp_coast | 5s | Persistent clamp = unrecoverable |
| stall_detect | 3s | Water pump inertia allows 3s |
| stall_faster_protect | If current/temp rising | Additional protection |
| vdc_recovery | Vdc > 270V for 1s | Hysteresis prevents chatter |
| apd_timeout_3ph | 10s | Three-phase stable without APD |
| apd_timeout_1ph | Immediate | Single-phase needs APD for DC-link |
| restart_cooldown | 2s | Thermal protection |
| passive_coast_timeout | 5s | Motor should stop in 5s |
| flying_restart_timeout | 3s | Re-sync attempt limit |
| precharge_timeout | 500ms | 22µF charges in <100ms through限流 resistor; 5x margin |
| align_duration | 200ms | 1-2 electrical periods at standstill, sufficient for flux buildup |
| if_ramp_duration | 300ms | Matches phase-b-001/002 I-f ramp specification |
| observer_check_window | 100ms | Verify observer lock before blend, matches phase-b-003 |
