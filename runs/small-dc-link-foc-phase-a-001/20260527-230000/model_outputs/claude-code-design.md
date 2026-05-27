# Claude Code — Core FOC Baseline Design (Phase A)

## 1. System Definition

### Platform: TMS320F28035

| Resource | Available | Notes |
|----------|-----------|-------|
| Clock | 60 MHz | 33.3 ns per cycle |
| Flash | 64 KB | Program storage |
| RAM | 12 KB | Runtime data |
| PWM channels | 8 (4 pairs) | ePWM modules |
| ADC | 16 channels | 12-bit, 80 ns conversion |
| Math accelerator | None | Must use fixed-point library |

### Motor Parameters (Typical Small PMSM Pump)

| Parameter | Symbol | Typical Value | Units |
|-----------|--------|---------------|-------|
| Pole pairs | p | 4 | - |
| Phase resistance | R_s | 2.0 | Ω |
| Phase inductance | L_s | 5.0 | mH |
| Back-EMF constant | k_e | 0.15 | V/(rad/s) |
| Torque constant | k_t | 0.15 | N·m/A |
| Moment of inertia | J | 0.001 | kg·m² |
| Rated current | I_rated | 3.0 | A (rms) |
| Rated speed | n_rated | 4000 | rpm |

---

## 2. FOC Module Architecture

### 2.1 Module List

```
┌─────────────────────────────────────────────┐
│               FOC System                     │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐ │
│  │ Clarke   │→│   Park    │→│ Current    │ │
│  │ Transform│  │ Transform │  │ Controller │ │
│  └─────────┘  └──────────┘  │ (dq PI)    │ │
│                              └─────┬─────┘ │
│                                    │        │
│  ┌─────────┐  ┌──────────┐  ┌─────▼─────┐ │
│  │ Speed    │←│ Observer  │←│ Inverse    │ │
│  │ Controller│  │ (SMO)    │  │ Park       │ │
│  │ (PI)     │  │          │  │            │ │
│  └────┬────┘  └──────────┘  └───────────┘ │
│       │                                     │
│  ┌────▼────┐  ┌──────────┐  ┌───────────┐ │
│  │ Speed   │→│ Reference │→│   SVPWM    │ │
│  │ Ref Gen │  │ Generator │  │ + Vdc FF  │ │
│  └─────────┘  └──────────┘  └───────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

### 2.2 Signal Flow

1. **ADC**: Sample I_a, I_b (or I_a, I_c), V_dc
2. **Clarke**: I_a, I_b → I_α, I_β
3. **Park**: I_α, I_β, θ_est → I_d, I_q
4. **Current PI**: I_d, I_q vs I_d*, I_q* → V_d*, V_q*
5. **Inverse Park**: V_d*, V_q*, θ_est → V_α*, V_β*
6. **SVPWM**: V_α*, V_β*, V_dc → PWM duty cycles
7. **Observer**: I_a, I_b, V_dc, PWM → θ_est, ω_est
8. **Speed PI**: ω_est vs ω_ref → I_q*

---

## 3. Module Specifications

### 3.1 Clarke Transform

```
I_α = I_a
I_β = (I_a + 2·I_b) / √3
```

**Fixed-point**: Q15 format, use 1/√3 ≈ 0.5774 (Q15: 18917)

### 3.2 Park Transform

```
I_d = I_α·cos(θ) + I_β·sin(θ)
I_q = -I_α·sin(θ) + I_β·cos(θ)
```

**Fixed-point**: θ in Q15 (0-65535 maps to 0-2π), cos/sin from lookup table (256 entries, Q15)

### 3.3 Current PI Controller

**Structure**: Anti-windup with output clamping

**Parameters** (from A2, tuned for F28035):

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| Kp_d | 120.54 | - | Proportional gain (d-axis) |
| Ki_d | 70440 | 1/s | Integral gain (d-axis) |
| Kp_q | 120.54 | - | Same as d-axis (symmetric) |
| Ki_q | 70440 | 1/s | Same as d-axis |
| Output limit | ±Vdc/√3 | V | Voltage saturation |
| Anti-windup | Clamping | - | Clamp integrator when output saturated |
| Sample rate | 10 kHz | Hz | PWM switching frequency |

**Fixed-point**: Q15 for gains, Q12 for integrator state (wider to prevent overflow)

### 3.4 SVPWM with Vdc Feedforward

**Duty cycle calculation**:
```
V_α_ref = V_α* · (√3 / V_dc)
V_β_ref = V_β* · (√3 / V_dc)
```

**Vdc feedforward**: Use real-time Vdc measurement to normalize voltage commands. This is critical for 22µF operation where Vdc varies widely.

**Sector determination**: Standard 6-sector SVPWM algorithm
**Timing**: Compute in ISR, update PWM registers at next switching cycle

### 3.5 Current Limiting

```
I_q_max = min(I_rated, √(I_max² - I_d²))
```

With I_d* = 0 (FOC): I_q_max = I_rated = 3A

**Vdc-dependent limiting** (for Phase C integration):
```
I_q_max(vdc) = min(I_rated, (Vdc - V_margin) / (ω_e · L_s + R_s))
```

### 3.6 Sliding Mode Observer (SMO)

**Structure** (from A2, eq. 6-9):

```
dî_α/dt = (-R_s·î_α - e_α + v_α - k·sign(î_α - î_α)) / L_s
dî_β/dt = (-R_s·î_β - e_β + v_β - k·sign(î_β - î_β)) / L_s
```

Where:
- î_α, î_β = estimated currents
- e_α, e_β = estimated back-EMF
- k = sliding mode gain

**Parameters** (from A2):

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| k (SMO gain) | 145 | V | Tune for fixed-point |
| LPF cutoff | 30 kHz | Hz | Adjust for 10-20 kHz PWM |
| Observer bandwidth | ~500 Hz | Hz | Mid-high speed range |
| θ_est | atan2(-e_α, e_β) | rad | Position estimate |

**Fixed-point**: Q12 for current estimates, Q15 for angle, lookup table for atan2

### 3.7 Speed PI Controller

**Parameters** (from A2):

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| Kp_m | 0.004 | - | Proportional gain |
| Ki_m | 2 | 1/s | Integral gain |
| Output limit | ±I_q_max | A | Current reference limit |
| Sample rate | 1 kHz | Hz | 10x slower than current loop |

### 3.8 Speed Reference Generator

For Phase A: Simple ramp generator
```
ω_ref(t) = ω_target if t > ramp_time
ω_ref(t) = ω_target · t / ramp_time if t ≤ ramp_time
```

Ramp time: 2-5 seconds (configurable)

---

## 4. TMS320F28035 Fixed-Point Feasibility

### 4.1 Math Budget (per 100 µs ISR)

| Operation | Cycles | Count | Total |
|-----------|--------|-------|-------|
| Clarke | 10 | 1 | 10 |
| Park | 15 | 1 | 15 |
| Inverse Park | 15 | 1 | 15 |
| Current PI | 20 | 2 | 40 |
| SVPWM | 30 | 1 | 30 |
| SMO | 50 | 1 | 50 |
| sin/cos LUT | 5 | 4 | 20 |
| ADC sampling | 160 | 1 | 160 |
| **Total** | | | **340** |

**Available at 60 MHz, 10 kHz ISR**: 6000 cycles
**Utilization**: 340/6000 = 5.7% — **well within budget**

### 4.2 RAM Budget

| Variable | Size | Count | Total |
|----------|------|-------|-------|
| ADC buffers | 16 bits | 4 | 8 bytes |
| Clarke/Park state | 16 bits | 4 | 8 bytes |
| PI state (current) | 32 bits | 4 | 16 bytes |
| PI state (speed) | 32 bits | 2 | 8 bytes |
| SMO state | 16 bits | 8 | 16 bytes |
| SVPWM state | 16 bits | 6 | 12 bytes |
| Lookup tables | 16 bits | 512 | 1024 bytes |
| Stack | 8 bits | 512 | 512 bytes |
| **Total** | | | **~1.6 KB** |

**Available**: 12 KB
**Utilization**: 1.6/12 = 13.3% — **well within budget**

### 4.3 Flash Budget

| Module | Estimated Size |
|--------|---------------|
| Main control loop | ~2 KB |
| SMO observer | ~1.5 KB |
| SVPWM | ~1 KB |
| Math library (fixed-point) | ~3 KB |
| Startup + initialization | ~1 KB |
| **Total** | **~8.5 KB** |

**Available**: 64 KB
**Utilization**: 8.5/64 = 13.3% — **well within budget**

---

## 5. foc_constraints Interface

```yaml
foc_constraints:
  # Voltage requirements
  min_required_vdc_by_speed:
    1000rpm: 82V
    2000rpm: 149V
    3000rpm: 216V
    4000rpm: 283V
  voltage_saturation_margin: 15V

  # Current limits
  max_iq: 3.0A  # rated current
  max_id: 0A    # FOC with id*=0

  # Loop bandwidths
  current_loop_bandwidth: 1000Hz  # ~1/10 of PWM frequency
  speed_loop_bandwidth: 100Hz     # ~1/10 of current loop

  # Observer parameters
  observer_min_speed: 1500rpm  # minimum for reliable SMO
  observer_gain_k: 145
  observer_lpf_cutoff: 30000Hz

  # Efficiency
  estimated_efficiency: 0.90  # for Pavg_ref calculation

  # Timing
  pwm_frequency: 10000Hz
  current_loop_rate: 10000Hz
  speed_loop_rate: 1000Hz
```

---

## 6. Acceptance Criteria

### Phase A-001 (Design) Acceptance

- [ ] All 7 modules defined with parameters
- [ ] Fixed-point feasibility verified (cycle, RAM, Flash budgets)
- [ ] foc_constraints YAML complete and compatible with derivation-002
- [ ] PI gains physically reasonable (from A2, validated)
- [ ] SMO parameters suitable for mid-high speed range

### Phase A-002 (Implementation) Acceptance

- [ ] FOC runs on TMS320F28035 simulator (Code Composer Studio)
- [ ] Current loop tracks reference within 5% at 2000 rpm
- [ ] Speed loop tracks reference within 2% at 2000 rpm
- [ ] SMO estimates angle within 5° electrical at 2000+ rpm
- [ ] All modules fit within fixed-point budget (no overflow)

### Phase A-003 (Hardware Validation) Acceptance

- [ ] FOC runs on 1360µF baseline hardware
- [ ] Motor spins up from standstill to 4000 rpm
- [ ] Speed ripple < 1% at steady state
- [ ] Current THD < 5% at rated load
- [ ] No observable instability during transients

---

## 7. Explicitly Excluded from Phase A

1. **Active Power Decoupling (APD)** — Phase C scope
2. **Pavg_ref power limiting** — Phase C scope
3. **Large-ripple closed-loop control** — Phase C scope
4. **22µF stability claims** — Requires derivation-002 results
5. **I-f startup** — Phase B scope (from A1)
6. **Smooth FOC transition** — Phase B scope

Phase A validates the FOC foundation on a stable supply. The 22µF integration happens in Phase C after derivation-002 defines the operating envelope.
