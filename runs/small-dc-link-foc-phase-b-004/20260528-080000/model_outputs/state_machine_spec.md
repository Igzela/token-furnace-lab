# Phase B-004: Startup State Machine Spec

## State Diagram

```
IDLE → PRECHARGE → ALIGN → IF_RAMP → OBSERVER_CHECK → BLEND → FOC
  ↓        ↓                              ↓               ↓
  └── FAULT ←─────────────────────────────┘───────────────┘
```

## States

| State | ID | Description |
|-------|-----|-------------|
| IDLE | 0 | Power-on, waiting for enable |
| PRECHARGE | 1 | APD precharge, verify Vdc and Vapd |
| ALIGN | 2 | Rotor alignment pulse |
| IF_RAMP | 3 | I-f open-loop ramp with S-curve |
| OBSERVER_CHECK | 4 | Verify observer convergence at threshold |
| BLEND | 5 | Angle blend with anti-chatter |
| FOC | 6 | Closed-loop sensorless FOC |
| FAULT | 7 | Fault shutdown |

## State Transitions

```
IDLE:
  → PRECHARGE: when enable=1 AND no fault
  → FAULT: when fault detected

PRECHARGE:
  → ALIGN: when Vdc ∈ [250,450] AND Vapd ∈ [200,500] AND dwell ≥ 100ms
  → FAULT: when dwell ≥ 500ms AND Vdc/Vapd out of range

ALIGN:
  → IF_RAMP: when dwell ≥ T_align (200ms default)
  → FAULT: when fault detected

IF_RAMP:
  → OBSERVER_CHECK: when omega_m ≥ omega_start AND observer_detected=1
  → FAULT: when fault detected

OBSERVER_CHECK:
  → BLEND: when theta_err_deg < blend_threshold (30°) AND omega_m ≥ omega_end
  → FAULT: when fault detected

BLEND:
  → FOC: when handover_counter ≥ N_foc_samples (200 = 20ms)
  → OBSERVER_CHECK: when observer_invalid_counter ≥ N_invalid (50 samples)
  → FAULT: when fault detected

FOC:
  → FAULT: when fault detected
  → (steady state, no exit except fault)
```

## Dwell Counters

| Counter | Threshold | Purpose |
|---------|-----------|---------|
| precharge_dwell | 100ms (1000 samples) | Ensure APD stable before proceeding |
| align_dwell | 200ms (2000 samples) | Rotor alignment pulse duration |
| observer_detect_counter | 1 sample | Observer detected flag (sticky once set) |
| blend_valid_counter | 1 sample | Blend allowed flag (sticky once set) |
| handover_counter | 200 samples (20ms) | Consecutive samples with θ_err < 20° |
| observer_invalid_counter | 50 samples (5ms) | Consecutive samples with θ_err > 45° → rollback to OBSERVER_CHECK |

## Blend Logic (Deterministic)

```
α_step = Ts / T_blend   (e.g., 0.1s / 100ms = 0.001 per sample)
rollback_step = 0.01    (1% per sample when θ_err > 35°)

if θ_err < 30°:
    α = min(1.0, α + α_step)

if θ_err > 35°:
    α = max(0.0, α - rollback_step)

if θ_err > 45°:
    observer_invalid_counter++
    if observer_invalid_counter ≥ 50:
        state = OBSERVER_CHECK
        α = 0.0
else:
    observer_invalid_counter = 0

theta_blend = α * θ_obs + (1 - α) * θ_ramp
```

## Fallback Startup Profiles

```c
typedef struct {
    float I_start;        // q15_t normalized
    float omega_start;    // rad/s mech
    float omega_end;      // rad/s mech
    float T_blend_ms;     // ms
    const char *name;
} StartupProfile;

#define PROFILE_NOMINAL   { 0.5, 30.0, 60.0, 100.0, "nominal"   }
#define PROFILE_FALLBACK  { 0.8, 30.0, 60.0, 150.0, "fallback"  }
#define PROFILE_STRONG    { 1.0, 30.0, 60.0, 200.0, "strong"    }
```

## Trace Buffer Format

```c
#define TRACE_DEPTH 2048

typedef struct {
    uint32_t timestamp;     // 32-bit timer ticks
    uint16_t state;         // current state
    int16_t theta_ramp;     // q12 angle (radians × 4096)
    int16_t theta_obs;      // q12 angle
    int16_t theta_blend;    // q12 angle (after blend)
    int16_t theta_err_deg;  // millidegrees (×1000)
    uint16_t alpha_x1000;   // α × 1000 (0-1000)
    int16_t omega_ref;      // q12 rad/s
    int16_t omega_est;      // q12 rad/s
    int16_t iq_ref;         // q15 amps
    int16_t iq_meas;        // q15 amps
    uint16_t vdc_mv;        // millivolts
    uint16_t vapd_mv;       // millivolts
    uint8_t svpwm_saturated;// 0/1
    uint8_t observer_valid; // 0/1
    uint16_t fault_code;    // 0=OK, 1-8=fault codes
} TraceEntry;
```

**Size**: 28 bytes × 2048 = 56KB (fits in 64KB RAM page)

**DMA logging**: Write to circular buffer in ISR, dump via SCI on request.

## Fault Codes

| Code | Name | Condition |
|------|------|-----------|
| 0 | OK | No fault |
| 1 | UVLO | Vdc < 200V |
| 2 | OV | Vdc > 450V |
| 3 | OC | Iq or Id > 5A |
| 4 | PRECHARGE_TIMEOUT | Vdc/Vapd out of range after 500ms |
| 5 | BLEND_ABORT | θ_err > 45° for 50 samples during blend |
| 6 | OBSERVER_LOST | θ_err > 45° during FOC |
| 7 | APD_FAULT | Vapd out of range |
| 8 | USER_FAULT | External fault input |
