# Phase A-002: FOC Interface Design (TMS320F28035) — v3

GPT review: v1=74/100, v2=86/100 PASS_WITH_NOTES. v3 addresses final notes.

## 1. Fixed-Point Type Definitions

```c
/* foc_types.h — Fixed-point types for FOC on TMS320F28035 */

#ifndef FOC_TYPES_H
#define FOC_TYPES_H

#include <stdint.h>

/*
 * Q15: normalized signals [-1.0, +0.999969]
 * Physical meaning depends on base unit context:
 *   current: value = raw * I_base   (I_base = 5.0A)
 *   voltage: value = raw * V_base   (V_base = 400.0V)
 *   speed:   value = raw * omega_base (omega_base = 500.0 rad/s)
 */
typedef int16_t  q15_t;

/* Q12: limited physical intermediate values [-8.0, +7.9997] */
typedef int16_t  q12_t;

/* Q12 accumulator: 32-bit for PI integrators and products */
typedef int32_t  q12_acc_t;

/* Gain type: PI gains stored as int32 with declared Q format.
 * Kp_q16 = Kp_physical * 65536 (Q16 format)
 * KiTs_q16 = Ki * Ts * 65536   (discrete, includes sample time)
 */
typedef int32_t  gain_t;

/* Electrical angle: 0-65535 maps to [0, 2π) */
typedef uint16_t angle_t;

/* PWM duty cycle: 0-65535 maps to [0, 100%] */
typedef uint16_t duty_t;

/* ADC sample: 12-bit unsigned */
typedef uint16_t adc_raw_t;

/* Boolean flag for module status */
typedef uint8_t  foc_flag_t;

#endif /* FOC_TYPES_H */
```

### Base Units

All q15_t signals are normalized to [-1, +1) by dividing by the corresponding base:

| Base | Value | Use |
|------|-------|-----|
| I_base | 5.0 A | Phase current normalization (q15_t) |
| V_base | 400.0 V | Phase voltage normalization (q15_t) |
| omega_m_base | 500.0 rad/s | Mechanical speed normalization (q15_t) |
| omega_e_base | 2000.0 rad/s | Electrical speed normalization (q12_t) |
| Vdc_mon_base | 500.0 V | Vdc monitoring/protection (q12_t, covers overvoltage) |

Conversion: `q15_val = (int16_t)(physical_val / base * 32768)`

### Gain Type (Critical — GPT feedback)

PI gains from A2 are continuous-time values (Kp=120.54, Ki=70440). These cannot be stored directly in q12_t. The interface stores **discrete-time gains** pre-scaled:

```c
/* PI gain storage (discrete form) */
typedef struct {
    gain_t  kp;       /* Kp_q16 = Kp * 65536 */
    gain_t  ki_ts;    /* KiTs_q16 = Ki * Ts * 65536 */
} pi_gains_t;

/* Discrete PI equation (velocity form):
 * u[k] = u[k-1] + Kp_q16*(e[k]-e[k-1]) + KiTs_q16*e[k]
 */
```

For current loop at 10kHz (Ts=100µs):
- Kp_q16 = 120.54 * 65536 = 7,898,112
- KiTs_q16 = 70440 * 100e-6 * 65536 = 461,568

---

## 2. Module Taxonomy

```
FOC Core (7 modules):
  Clarke, Park, Current PI, Inverse Park, SVPWM, SMO, Speed PI

Peripheral (3 modules):
  ADC, Speed Ref, Theta Source Mux

Utility (1 module):
  IqLimiter (from derivation-003)
```

---

## 3. Module Interface Definitions

### 3.1 ADC Sampling (Peripheral)

```c
/* foc_adc.h */

typedef struct {
    adc_raw_t  ia_raw;
    adc_raw_t  ib_raw;
    adc_raw_t  vdc_raw;
} foc_adc_input_t;

typedef struct {
    q15_t      ia;          /* Phase A current, normalized to I_base */
    q15_t      ib;          /* Phase B current, normalized to I_base */
    q15_t      vdc;         /* DC-link voltage, normalized to V_base (control) */
    q12_t      vdc_mon;     /* DC-link voltage, Vdc_mon_base=500V (protection, covers >400V) */
    foc_flag_t fault_oc;    /* Overcurrent flag */
    foc_flag_t fault_uvlo;  /* Under-voltage lockout flag */
    foc_flag_t fault_ov;    /* Over-voltage flag */
} foc_adc_output_t;

typedef struct {
    q15_t  offset_ia;       /* ADC offset calibration */
    q15_t  offset_ib;
    q15_t  gain_ia;         /* ADC gain calibration (Q16) */
    q15_t  gain_ib;
    q15_t  gain_vdc;
    q15_t  vdc_oc阈;        /* Overcurrent threshold */
    q15_t  vdc_uvlo阈;      /* Under-voltage threshold */
    q15_t  vdc_ov阈;        /* Over-voltage threshold */
} foc_adc_params_t;

void foc_adc_init(const foc_adc_params_t *params);
void foc_adc_convert(const foc_adc_input_t *in, foc_adc_output_t *out);
```

### 3.2 Clarke Transform (Core)

```c
/* foc_clarke.h */

typedef struct {
    q15_t  ia;
    q15_t  ib;
} foc_clarke_input_t;

typedef struct {
    q15_t  i_alpha;         /* Normalized to I_base */
    q15_t  i_beta;          /* Normalized to I_base */
} foc_clarke_output_t;

void foc_clarke(const foc_clarke_input_t *in, foc_clarke_output_t *out);
```

Constant: 1/√3 = 0.5774 → Q15 = 18917

### 3.3 Theta Source Mux (Peripheral — GPT feedback)

```c
/* foc_theta_mux.h — Selects angle source for Park/Inverse Park */

typedef enum {
    THETA_OPEN_LOOP = 0,    /* I-f startup: open-loop angle */
    THETA_SENSORLESS = 1,   /* SMO estimated angle */
    THETA_BLEND = 2         /* Transition: blended angle */
} theta_source_t;

typedef struct {
    angle_t  theta_open_loop;   /* From I-f ramp generator */
    angle_t  theta_est;         /* From SMO */
    theta_source_t source;      /* Current angle source */
    q15_t    blend_ratio;       /* 0=full open_loop, 1=full sensorless */
} foc_theta_mux_input_t;

typedef struct {
    angle_t  theta_out;         /* Selected/blended angle → Park, InvPark */
} foc_theta_mux_output_t;

void foc_theta_mux(const foc_theta_mux_input_t *in, foc_theta_mux_output_t *out);
```

**Critical for Phase B**: Without this, I-f startup → FOC transition has no interface to connect.

### 3.4 Park Transform (Core)

```c
/* foc_park.h */

typedef struct {
    q15_t    i_alpha;
    q15_t    i_beta;
    angle_t  theta;             /* From theta_source_mux */
} foc_park_input_t;

typedef struct {
    q15_t  id;                  /* Normalized to I_base */
    q15_t  iq;                  /* Normalized to I_base */
} foc_park_output_t;

void foc_park(const foc_park_input_t *in, foc_park_output_t *out);
```

### 3.5 IqLimiter (Utility — from derivation-003)

```c
/* foc_iq_limiter.h — Vdc-dependent current limit */

typedef struct {
    q15_t    vdc;               /* Current DC-link voltage */
    q12_t    omega_est_e;       /* Electrical speed (q12, omega_e_base=2000) */
    q15_t    i_rated;           /* Rated current */
    q15_t    rs;                /* Phase resistance */
    q15_t    psi_f;             /* Flux linkage */
    uint8_t  pole_pairs;
} foc_iq_limiter_input_t;

typedef struct {
    q15_t  iq_max_voltage;     /* Max Iq from voltage limit */
    q15_t  iq_max_current;     /* Max Iq from current limit (= i_rated) */
    q15_t  iq_max;             /* min(voltage, current) limit */
    foc_flag_t voltage_limited;
} foc_iq_limiter_output_t;

void foc_iq_limiter(const foc_iq_limiter_input_t *in, foc_iq_limiter_output_t *out);
```

**Derivation-003 result**: `Iq_max = min(I_rated, (Vdc - V_margin) / (ωe·Ls + Rs))`

### 3.6 Current PI Controller (Core)

```c
/* foc_pi_current.h */

typedef struct {
    q15_t  id_ref;             /* Typically 0 for FOC */
    q15_t  iq_ref;             /* From Speed PI or IqLimiter */
    q15_t  id_meas;
    q15_t  iq_meas;
    q15_t  vdc;                /* For output voltage limit */
} foc_pi_current_input_t;

typedef struct {
    q15_t  vd_ref;             /* Normalized to V_base */
    q15_t  vq_ref;             /* Normalized to V_base */
    foc_flag_t sat_d;          /* D-axis saturated */
    foc_flag_t sat_q;          /* Q-axis saturated */
} foc_pi_current_output_t;

typedef struct {
    q12_acc_t  integrator_d;
    q12_acc_t  integrator_q;
    q15_t      v_limit;        /* ±Vdc/√3, cached */
} foc_pi_current_state_t;

typedef struct {
    pi_gains_t  gains_d;       /* Discrete gains for d-axis */
    pi_gains_t  gains_q;       /* Discrete gains for q-axis */
} foc_pi_current_params_t;

void foc_pi_current_init(const foc_pi_current_params_t *params,
                         foc_pi_current_state_t *state);
void foc_pi_current(const foc_pi_current_input_t *in,
                    foc_pi_current_output_t *out,
                    foc_pi_current_state_t *state);
```

**Anti-windup**: Clamp integrator when output hits ±v_limit. sat_d/sat_q flags indicate saturation.

### 3.7 Inverse Park Transform (Core)

```c
/* foc_inv_park.h */

typedef struct {
    q15_t    vd;               /* From Current PI */
    q15_t    vq;               /* From Current PI */
    angle_t  theta;            /* From theta_source_mux */
} foc_inv_park_input_t;

typedef struct {
    q15_t  v_alpha;            /* Normalized to V_base */
    q15_t  v_beta;             /* Normalized to V_base */
} foc_inv_park_output_t;

void foc_inv_park(const foc_inv_park_input_t *in, foc_inv_park_output_t *out);
```

### 3.8 SVPWM with Vdc Feedforward (Core)

```c
/* foc_svpwm.h */

typedef struct {
    q15_t  v_alpha;            /* Normalized to V_base, from Inverse Park */
    q15_t  v_beta;             /* Normalized to V_base, from Inverse Park */
    q15_t  vdc;                /* Normalized to V_base, from ADC */
} foc_svpwm_input_t;

typedef struct {
    duty_t  duty_a;
    duty_t  duty_b;
    duty_t  duty_c;
    uint8_t sector;            /* SVPWM sector (1-6) */
    q15_t   modulation_index;  /* Output: |V| / (Vdc/√3) */
    foc_flag_t saturated;      /* Overmodulation detected */
} foc_svpwm_output_t;

void foc_svpwm(const foc_svpwm_input_t *in, foc_svpwm_output_t *out);
```

**Vdc feedforward**: `m_alpha = v_alpha * (√3 / vdc)`, where v_alpha is in V_base units.
**Critical for 22µF**: Vdc varies widely; feedforward normalizes in real-time.

### 3.9 Sliding Mode Observer (Core)

```c
/* foc_smo.h */

typedef struct {
    q15_t  ia;
    q15_t  ib;
    q15_t  v_alpha_applied;   /* Reconstructed from PWM duty + measured Vdc */
    q15_t  v_beta_applied;    /* NOT command voltage — must account for saturation */
    q15_t  vdc_inst;          /* Instantaneous DC-link voltage */
    q12_t  ts;                /* Sample time (Q12, seconds) */
} foc_smo_input_t;

typedef struct {
    angle_t  theta_est;
    q12_t    omega_est_e;      /* Electrical speed, omega_e_base=2000 rad/s */
    q15_t    e_alpha;          /* Estimated back-EMF */
    q15_t    e_beta;
    foc_flag_t valid;          /* Observer lock status */
    foc_flag_t speed_valid;    /* Speed estimate reliable */
} foc_smo_output_t;

typedef struct {
    q12_t  i_hat_alpha;
    q12_t  i_hat_beta;
    q12_t  e_hat_alpha;
    q12_t  e_hat_beta;
    q12_t  z_alpha;
    q12_t  z_beta;
} foc_smo_state_t;

typedef struct {
    gain_t  k;                 /* SMO gain (Q16) */
    gain_t  lpf_alpha;         /* LPF coefficient (Q16) */
} foc_smo_params_t;

void foc_smo_init(const foc_smo_params_t *params, foc_smo_state_t *state);
void foc_smo(const foc_smo_input_t *in, foc_smo_output_t *out,
             foc_smo_state_t *state);
```

**Applied voltage reconstruction** (critical for accuracy under saturation):
```c
/* Reconstruct from SVPWM duty + measured Vdc — NOT command voltage */
v_alpha_applied = (2*duty_a - duty_b - duty_c) / 3 * vdc_inst;
v_beta_applied = (duty_b - duty_c) / sqrt(3) * vdc_inst;
/* If SVPWM saturated: observer_valid may degrade */
```
**Parameters**: k=145, LPF cutoff=30kHz
**Angle extraction**: `theta_est = atan2(-e_alpha, e_beta)` via LUT

### 3.10 Speed PI Controller (Core)

```c
/* foc_pi_speed.h */

typedef struct {
    q15_t  omega_ref;          /* From Speed Ref (mechanical, omega_m_base=500) */
    q15_t  omega_m_est;        /* Mechanical speed = omega_est_e / pole_pairs */
    q15_t  iq_max;             /* From IqLimiter */
} foc_pi_speed_input_t;

typedef struct {
    q15_t  iq_ref;             /* Current reference → Current PI */
} foc_pi_speed_output_t;

typedef struct {
    q12_acc_t  integrator;
} foc_pi_speed_state_t;

typedef struct {
    pi_gains_t  gains;         /* Discrete gains */
} foc_pi_speed_params_t;

void foc_pi_speed_init(const foc_pi_speed_params_t *params,
                       foc_pi_speed_state_t *state);
void foc_pi_speed(const foc_pi_speed_input_t *in,
                  foc_pi_speed_output_t *out,
                  foc_pi_speed_state_t *state);
```

Sample rate: 1kHz (every 10th call of 10kHz ISR)

### 3.11 Speed Reference Generator (Peripheral)

```c
/* foc_speed_ref.h */

typedef struct {
    q15_t    omega_target;     /* Target speed */
    uint32_t ramp_time_ms;
    uint32_t elapsed_ms;
    foc_flag_t enable;
    foc_flag_t direction;      /* 0=CW, 1=CCW */
    q15_t    accel_limit;      /* Max acceleration (rad/s per step) */
} foc_speed_ref_input_t;

typedef struct {
    q15_t    omega_ref;
    foc_flag_t ramp_active;    /* True during ramp-up */
} foc_speed_ref_output_t;

void foc_speed_ref(const foc_speed_ref_input_t *in, foc_speed_ref_output_t *out);
```

---

## 4. ISR Entry Points

```c
/* foc_isr.h */

/* 10kHz current loop — called by ePWM timer ISR */
void foc_current_loop_isr(void);

/* Internal sub-tasks (called within foc_current_loop_isr) */
void foc_speed_loop_task(void);   /* Every 10th call → 1kHz */
```

### 10kHz ISR Internal Flow

```
foc_current_loop_isr():
  1. ADC sample + convert → ia, ib, vdc, vdc_mon
  2. Clarke transform → i_alpha, i_beta
  3. Theta source select (theta_mux) → theta
  4. Park transform(i_alpha, i_beta, theta) → id, iq
  5. Current PI(id_ref=0, iq_ref, id, iq, vdc) → vd, vq
  6. Inverse Park(vd, vq, theta) → v_alpha, v_beta
  7. SVPWM(v_alpha, v_beta, vdc) → duty, modulation_index, saturated
  8. Reconstruct applied voltage from duty + vdc → v_alpha_applied, v_beta_applied
  9. SMO(ia, ib, v_alpha_applied, v_beta_applied, vdc) → theta_est, omega_est_e
  10. omega_m_est = omega_est_e / pole_pairs
  11. Fault fast-check (OC, UVLO, OV using vdc_mon)
  12. if (counter % 10 == 0) → foc_speed_loop_task()

foc_speed_loop_task():
  1. Speed reference ramp → omega_ref
  2. IqLimiter(vdc, omega_est_e) → iq_max
  3. Speed PI(omega_ref, omega_m_est, iq_max) → iq_ref_cmd
  4. iq_ref_active = iq_ref_cmd  /* double-buffer: cmd → active */
```

**iq_ref double-buffering**: Speed PI writes iq_ref_cmd at 1kHz. Current PI reads iq_ref_active at 10kHz. Atomic copy on 1kHz tick prevents tearing.

---

## 5. RAM Budget

```yaml
ram_budget:
  control_state: ~1.1KB    # All module state structs
  reserved_stack: >=1KB
  reserved_driver_buffers: >=1KB
  sin_cos_lut: 512B        # 256-entry Q15 LUT
  no_runtime_trace_buffers_in_release: true
  no_debug_logging_in_release: true
```

| Category | Size | Notes |
|----------|------|-------|
| Module state structs | ~69 bytes | All state_t types |
| sin/cos LUT | 512 bytes | 256 × int16 |
| Stack | 512 bytes minimum | ISR + main |
| Driver buffers | 256 bytes | ADC, PWM hardware buffers |
| **Total runtime** | **~1.1 KB** | Excludes debug/trace |
| **Available** | **12 KB** | F28035 RAM |
| **Utilization** | **9.2%** | Safe margin |

---

## 6. Acceptance Checklist

- [x] Module taxonomy: 7 core + 3 peripheral + 1 utility
- [x] All modules have Input/Output/State/Param structs where applicable
- [x] Fixed-point base units defined (I_base, V_base, omega_base)
- [x] Gain type (gain_t) for PI gains with discrete-form storage
- [x] Theta source mux for startup transition (OPEN_LOOP/SENSORLESS/BLEND)
- [x] IqLimiter interface from derivation-003
- [x] ADC calibration and fault flags
- [x] SVPWM saturation/modulation index output
- [x] SMO valid/speed_valid status flags
- [x] Speed Ref enable/direction/acceleration fields
- [x] Anti-windup state explicit in PI controllers
- [x] ISR: speed loop as sub-task of 10kHz ISR (no nested interrupt)
- [x] RAM budget clarified (excludes LUT, driver, debug)
- [x] Vdc feedforward unit clarified (normalized V_base)

## 7. GPT Review Notes (v1 → v2 changes)

1. **Added theta_source_mux** — critical for Phase B I-f startup transition
2. **Added IqLimiter** — derivation-003 result enters interface
3. **Defined base units** — q15_t now has physical meaning via I_base/V_base/omega_base
4. **Added gain_t** — PI gains stored as discrete Q16 values, not continuous-time floats
5. **Added ADC calibration/fault** — offset, gain, OC/UVLO/OV flags
6. **Added SMO valid/lock status** — observer reliability indication
7. **Clarified ISR structure** — speed loop as 10kHz sub-task, not separate interrupt
8. **Added SVPWM saturation output** — modulation_index and overmodulation flag
9. **Expanded Speed Ref** — enable, direction, acceleration limit
10. **RAM budget** — explicit exclusions (debug, trace, driver buffers)

## 8. Next Steps

1. **Phase A-003**: Hardware validation on 1360µF baseline
2. **Phase B**: I-f startup + smooth FOC transition (uses theta_source_mux)
3. **Phase C**: APD integration + 22µF ripple handling
