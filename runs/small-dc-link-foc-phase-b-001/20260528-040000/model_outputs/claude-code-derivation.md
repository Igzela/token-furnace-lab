# Phase B-001: I-f Startup + Smooth FOC Transition

## 1. Alignment Phase

### Procedure

Before I-f ramp begins, rotor must be aligned to a known position.

| Parameter | Value | Notes |
|-----------|-------|-------|
| I_align | 1.5A (0.5 × I_rated) | Sufficient torque, below thermal limit |
| T_align | 200ms | >5τ_e = 5×(Ls/Rs) = 12.5ms, generous margin |
| θ_align | 0° (electrical) | d-axis aligned to rotor flux |
| Id_ref during alignment | I_align × cos(0°) = 1.5A | |
| Iq_ref during alignment | 0A | No torque, pure alignment |

### Fixed-Point

```
I_align_q15 = round(1.5 / 5.0 × 32768) = 9830  (q15_t)
T_align_counts = 0.2 × 10000 = 2000              (at 10kHz ISR)
```

### Alignment Verification

During alignment, monitor:
- `Vq ≈ Rs × I_align + ωe × Ls × Id ≈ 2 × 1.5 = 3.0V` (at standstill, ωe=0)
- If Vq > Vdc × 0.9, alignment current too high for available voltage

---

## 2. I-f Ramp Generator

### Ramp Profile

Constant acceleration ramp:

```
ω_e(k) = ω_e(k-1) + Δω_e
θ(k) = θ(k-1) + ω_e(k) × Ts
```

Where:
- ω_e: electrical angular velocity (rad/s)
- Δω_e: electrical acceleration increment per sample
- θ: electrical angle (angle_t, 0-65535 → [0, 2π))
- Ts: sample period

### Acceleration Limits

**Voltage limit** (at standstill, Ls×dI/dt dominates):

```
V_max ≈ ω_e × Ls × I_start
ω_e_max = Vdc_nom / (Ls × I_start)
```

For I_start = 1.5A:
```
ω_e_max = 300 / (5e-3 × 1.5) = 40,000 rad/s → absurdly high
```

Practical limit is from **current ripple and inductance**:

```
ΔI_pp = Vdc / (Ls × f_sw) × D × (1-D)
```

At 50% duty, f_sw=40kHz:
```
ΔI_pp = 300 / (5e-3 × 40000) × 0.25 = 0.375A  (25% of 1.5A, acceptable)
```

**Acceleration limit from thermal** (I²R during ramp):

```
P_heat = I_start² × Rs = 1.5² × 2 = 4.5W per phase
Total: 3 × 4.5 = 13.5W (acceptable for 200ms burst)
```

**Practical Δω_e**: Based on reaching transition speed in reasonable time.

### Ramp Parameter Sweep

| Δω_e (elec rad/s per sample) | f_ISR=10kHz | Ramp time to 200 rad/s elec | Notes |
|-------------------------------|-------------|------------------------------|-------|
| 0.1 | 2000ms | Too slow, current heats motor |
| 0.5 | 400ms | Conservative, safe |
| 1.0 | 200ms | Moderate, good balance |
| 2.0 | 100ms | Fast, may cause current overshoot |
| 5.0 | 40ms | Aggressive, voltage margin tight |

### Recommended

```
Δω_e = 1.0 rad/sample (at 10kHz ISR)
→ Ramp rate: 10,000 rad/s² (electrical)
→ Time to ω_e = 200 rad/s: 200ms
→ Corresponds to: ω_m = 200/2 = 100 rad/s mechanical = 955 rpm
```

### Angle Conversion to angle_t

```
θ_electrical (rad) → angle_t: θ_t = θ_electrical / (2π) × 65536
```

Per sample:
```
Δθ_t = Δω_e × Ts / (2π) × 65536
     = 1.0 × 100e-6 / 6.2832 × 65536
     = 100e-6 × 10430
     = 1.043 → round to 1 (at 10kHz)
```

At 10kHz ISR: `Δθ_t = 1` per sample → ω_e = 1 × 10000 / 65536 × 2π ≈ 0.958 rad/s

For faster ramp, use 20kHz ISR or accumulate in q12_t then convert.

### Fixed-Point Ramp Implementation

```c
/* I-f ramp generator */
static q12_t  omega_e_q12 = 0;     /* electrical angular velocity */
static angle_t theta_e = 0;         /* electrical angle */

#define OMEGA_E_INC_Q12  4          /* Δω_e = 4 × 2^-12 = 0.977 rad/s per sample */
#define OMEGA_E_MAX_Q12  8192       /* 8192 × 2^-12 = 2.0 rad/s max */

void if_ramp_isr(void) {
    /* Ramp omega_e */
    if (omega_e_q12 < OMEGA_E_MAX_Q12) {
        omega_e_q12 += OMEGA_E_INC_Q12;
    }

    /* Integrate angle: θ += ω × Ts */
    /* θ_t increment = omega_e_q12 × Ts × 65536 / (2π × 4096) */
    /* At 10kHz: θ increment ≈ omega_e_q12 >> 4 */
    theta_e += (angle_t)(omega_e_q12 >> 4);
}
```

---

## 3. Current Reference in I-f Mode

### Strategy: Constant Amplitude, Torque Angle Ramp

The motor produces torque via Iq component. During I-f:

```
Id_ref = 0                        (no flux building after alignment)
Iq_ref = I_start × ramp_factor   (ramp from 0 to I_start)
```

Where `ramp_factor` ramps from 0 to 1 over T_current_ramp (e.g., 50ms).

### Alternative: Fixed Current Magnitude, Rotating Vector

```
I_alpha_ref = I_start × cos(θ_ramp)
I_beta_ref  = I_start × sin(θ_ramp)
```

This creates a rotating current vector at the I-f frequency. The motor follows if the electrical frequency is below pull-out speed.

### Pull-Out Speed

Maximum speed before losing synchronism:

```
ω_pullout = Vdc / (√3 × Ls × I_start)     (for IPM, approximate)
         = 300 / (1.732 × 5e-3 × 1.5)
         = 23,100 rad/s elec → way above operating range
```

Practical pull-out limited by back-EMF:

```
ω_backemf_max = Vdc / (√3 × ke × p/2)    (for surface PM)
             = 300 / (1.732 × 0.15 × 2)
             = 577 rad/s elec → 2885 rpm mechanical
```

Wait — this is too low. For 4000rpm (419 rad/s mechanical), ω_e = 838 rad/s elec.

Let me recalculate: ke = 0.15 V/(rad/s) mechanical.

```
V_bemf = ke × ω_m = 0.15 × 419 = 62.9V per phase
V_required = √(Vd² + Vq²) where Vd = -ω_e×Ls×Iq, Vq = Rs×Iq + ω_e×Ls×Id
```

At Id=0, Iq=1.5A, ω_m=419 rad/s (4000rpm):
```
ω_e = p/2 × ω_m = 2 × 419 = 838 rad/s
Vd = -ω_e × Ls × Iq = -838 × 5e-3 × 1.5 = -6.29V
Vq = Rs × Iq + ke × ω_m = 2 × 1.5 + 0.15 × 419 = 3.0 + 62.9 = 65.9V
V_required = √(6.29² + 65.9²) = 66.2V
```

This is well within 300V DC-link. Motor can run up to 4000rpm in I-f mode with margin.

---

## 4. Transition: I-f → Sensorless FOC

### Strategy: Speed-Triggered Angle Blend

**Phase 1: Pre-transition (ω_m < ω_start)**
- Use θ_ramp for angle (I-f mode)
- Observer runs in background, estimating θ_obs
- Current reference: Iq_ref from I-f (constant or ramped)

**Phase 2: Blending (ω_start ≤ ω_m < ω_end)**
- Blend angle: `θ = α × θ_obs + (1-α) × θ_ramp`
- α ramps from 0 to 1
- Current reference transitions from I-f to speed PI output

**Phase 3: FOC (ω_m ≥ ω_end)**
- Use θ_obs exclusively (THETA_SENSORLESS)
- Speed PI controls Iq_ref
- I-f ramp frozen

### Transition Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| ω_start | 50 rad/s mech (480 rpm) | Observer can lock above this |
| ω_end | 100 rad/s mech (955 rpm) | Full confidence in observer |
| T_blend | 200ms | Gradual transition |
| I_transition | 1.5A (I_rated) | Maintain torque during transition |

### Angle Blending Formula

```
α = (ω_m - ω_start) / (ω_end - ω_start)     clamped to [0, 1]

θ_blend = α × θ_obs + (1-α) × θ_ramp
```

In angle_t (uint16, wraps at 65536):

```c
/* Angle blending — works with wrapping arithmetic */
angle_t theta_blend;
uint16_t alpha_q15 = /* computed α × 32768 */;
theta_blend = (angle_t)(
    (uint32_t)alpha_q15 * theta_obs / 32768 +
    (uint32_t)(32768 - alpha_q15) * theta_ramp / 32768
);
```

### Current Reference Handoff

During blending, transition Iq_ref from I-f constant to speed PI output:

```
Iq_ref_blend = α × Iq_ref_foc + (1-α) × I_start
```

Where `Iq_ref_foc` is the speed PI output (ramped from 0).

---

## 5. Observer Requirements During Startup

### Observer Activation

- **During alignment**: Observer OFF (no meaningful angle)
- **During I-f ramp**: Observer ON, running in background
- **At ω_start**: Observer angle θ_obs is used for blending

### Observer Convergence

The SMO observer needs sufficient back-EMF to estimate angle:

```
V_bemf_min ≈ ke × ω_m_min
```

For reliable estimation:
```
ω_m_min ≥ V_noise / ke = 0.5V / 0.15 = 3.3 rad/s mech (32 rpm)
```

This is very low — observer can converge early in the ramp.

### Observer Error During I-f

The observer uses actual measured currents but command voltages for the voltage model. During I-f, the voltage applied is:

```
Vd_applied = -ω_ramp × Ls × Iq_ref
Vq_applied = Rs × Iq_ref
```

The observer sees actual currents (which may lag due to inductance) and reconstructs voltage from PWM duty cycles. This mismatch causes observer angle error during I-f.

**Mitigation**: Use SMO with applied-voltage reconstruction (from PWM + Vdc measurement), as designed in phase-a-002.

---

## 6. DC-Link Voltage During Startup

### Current Draw During Alignment

```
I_phase = I_align = 1.5A (DC component, one phase)
I_dc = I_align × D (average, depends on modulation)
```

For 300V DC-link, 22µF:
```
ΔV = I_dc × T_align / Cdc = 1.5 × 0.2 / 22e-6 = 13,600V → impossible
```

Wait — this is wrong. The alignment current flows through the H-bridge, not directly from the capacitor. The DC-link sees the rectified current:

```
I_dc_avg ≈ 3/π × I_peak = 0.955 × 1.5 = 1.43A  (for 3-phase rectified)
```

Voltage sag:
```
ΔV = I_dc_avg × T_align / Cdc = 1.43 × 0.2 / 22e-6 = 13,000V → still wrong
```

**Correction**: The DC-link capacitor supplies the difference between input power and motor power. During alignment, motor power is just I²R losses:

```
P_loss = 3 × I_align² × Rs = 3 × 1.5² × 2 = 13.5W
```

From single-phase rectified input (with APD):
```
P_in ≈ P_loss = 13.5W (steady state)
```

The capacitor doesn't need to supply 13.5W continuously — the input rectifier does. The capacitor only handles ripple.

**Real concern**: At startup, before APD and input rectifier reach steady state, the DC-link capacitor must supply the transient current. With 22µF:

```
Energy stored: E = 0.5 × C × V² = 0.5 × 22e-6 × 300² = 0.99J
```

For alignment burst (200ms, 13.5W average):
```
Energy needed: 13.5 × 0.2 = 2.7J → exceeds stored energy
```

**This means**: The DC-link voltage will sag significantly during alignment if there's no input source. With APD and input rectifier active, the source maintains voltage. Without input, alignment must be shorter or current lower.

### Recommendation

- Use APD + input rectifier during startup
- If standalone (no input), reduce I_align to 0.5A and T_align to 50ms
- Monitor Vdc during alignment; abort if Vdc < 250V

---

## 7. Fixed-Point Implementation

### State Machine

```c
typedef enum {
    STARTUP_IDLE = 0,
    STARTUP_ALIGN,      /* DC alignment */
    STARTUP_IF_RAMP,    /* I-f acceleration */
    STARTUP_BLEND,      /* Angle blending */
    STARTUP_FOC         /* Full FOC */
} startup_state_t;
```

### Variables

```c
static startup_state_t state = STARTUP_IDLE;
static uint16_t align_timer = 0;
static q12_t omega_e_q12 = 0;
static angle_t theta_ramp = 0;
static q15_t alpha_q15 = 0;       /* blend factor */
static q15_t iq_ref_blend = 0;
```

### ISR Flow

```c
void foc_startup_isr(void) {
    switch (state) {
    case STARTUP_ALIGN:
        Id_ref = I_ALIGN_Q15;
        Iq_ref = 0;
        theta_e = THETA_ALIGN;
        if (++align_timer >= ALIGN_TIME) {
            state = STARTUP_IF_RAMP;
            omega_e_q12 = 0;
        }
        break;

    case STARTUP_IF_RAMP:
        /* Ramp omega_e */
        if (omega_e_q12 < OMEGA_E_MAX_Q12) {
            omega_e_q12 += OMEGA_E_INC_Q12;
        }
        /* Integrate angle */
        theta_ramp += (angle_t)(omega_e_q12 >> 4);
        theta_e = theta_ramp;

        /* Current: ramp up */
        Id_ref = 0;
        Iq_ref = ramp_iq(I_START_Q15, 50);  /* 50ms ramp */

        /* Check transition speed */
        if (omega_e_q12 >= OMEGA_START_Q12) {
            state = STARTUP_BLEND;
            alpha_q15 = 0;
        }
        break;

    case STARTUP_BLEND:
        /* Blend angle */
        theta_e = blend_angle(theta_obs, theta_ramp, alpha_q15);

        /* Blend current reference */
        Iq_ref = blend_current(iq_ref_foc, I_START_Q15, alpha_q15);

        /* Advance blend */
        if (alpha_q15 < 32768) {
            alpha_q15 += BLEND_INC;
        }
        if (alpha_q15 >= 32768) {
            state = STARTUP_FOC;
        }
        break;

    case STARTUP_FOC:
        theta_e = theta_obs;
        Iq_ref = iq_ref_foc;  /* from speed PI */
        break;
    }
}
```

---

## 8. Stability Analysis

### Failure Modes During Transition

| Failure | Cause | Mitigation |
|---------|-------|------------|
| Current oscillation | Angle error > 30° at blend | Ensure observer converged before blend |
| Torque transient | Sudden Iq_ref change | Ramp Iq_ref over 50ms |
| Angle jump | Wrapping arithmetic error | Use unsigned wrapping arithmetic |
| Speed PI windup | Iq_ref saturated at transition | Clamp PI integrator at handoff |
| DC-link sag | Large current step | APD maintains voltage, monitor Vdc |

### Angle Error Tolerance

For stable FOC, angle error must be < 30° (π/6 rad):

```
θ_error_max = 30° → torque loss = cos(30°) = 87% (acceptable)
θ_error_max = 45° → torque loss = cos(45°) = 71% (marginal)
θ_error_max = 60° → torque loss = cos(60°) = 50% (unstable)
```

At transition, if observer angle error > 30°, delay blend and let observer converge.

### Observer Convergence Check

```c
/* Check observer convergence before allowing blend */
q15_t theta_error = abs(theta_obs - theta_ramp);  /* wrapping-safe */
if (theta_error > THETA_ERROR_MAX) {
    /* Observer not converged, stay in I-f */
    state = STARTUP_IF_RAMP;
}
```

---

## 9. Summary: Phase B Design

| Component | Value | Notes |
|-----------|-------|-------|
| I_align | 1.5A | 0.5 × I_rated |
| T_align | 200ms | >5τ_e |
| Δω_e | 1.0 rad/sample | At 10kHz ISR |
| Ramp time to transition | 200ms | To ω_m = 955 rpm |
| ω_start (blend begin) | 50 rad/s mech | 480 rpm |
| ω_end (blend complete) | 100 rad/s mech | 955 rpm |
| T_blend | 200ms | Gradual transition |
| I_start | 1.5A | Maintains torque |
| DC-link: APD required | Yes | Maintains Vdc during startup |

### Deliverables

1. Startup state machine: IDLE → ALIGN → IF_RAMP → BLEND → FOC
2. I-f ramp: constant acceleration, Δω = 1.0 rad/sample
3. Angle blending: linear α interpolation, wrapping arithmetic
4. Current handoff: Iq_ref ramps from I-f to speed PI output
5. Stability: observer convergence check before blend, angle error < 30°
