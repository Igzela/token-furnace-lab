# Scheduler Plan — Phase A-004 (v2 — corrected)

## Overview

TMS320F28035 timer-based ISR architecture. PWM module triggers ADC + ISR at 10kHz. Two-layer observer design per GPT review: fast prediction in 10kHz ISR, full SMO correction at 5kHz.

**v1 error**: Used 15000 cycles budget (150MHz). Correct budget is 6000 cycles (60MHz / 10kHz).

## Timer Configuration

| Timer | Source | Frequency | Period (cycles) |
|-------|--------|-----------|-----------------|
| PWM1/2/3 | ePWM module | 10kHz | 6000 (60MHz/10kHz) |
| ADC SOC | PWM1 SOCA | 10kHz | Synchronized to PWM |
| CPU Timer 0 | ISR | 10kHz | 6000 (ISR budget) |
| CPU Timer 1 | 5kHz SMO | 5kHz | 12000 |
| CPU Timer 2 | 1kHz tasks | 1kHz | 60000 |
| Software | Background | 100Hz | ISR counter modulo |

## Task Layering

### Layer 0: Fast ISR (10kHz, current loop only)

Priority: HIGHEST. Non-preemptable. Must complete within 6000 cycles.
Target: ≤ 4200 cycles (70% of budget) for safety margin.

```
ISR_entry (context save)
  ├── ADC_read_calibrate      [300 cycles]
  ├── Clarke_transform        [150 cycles]
  ├── theta_predict           [50 cycles]   ← prediction only, no full observer
  ├── Park_transform          [200 cycles]
  ├── IqLimiter               [120 cycles]
  ├── Current_PI_Id           [250 cycles]
  ├── Current_PI_Iq           [250 cycles]
  ├── Inverse_Park            [200 cycles]
  ├── SVPWM                   [600 cycles]
  ├── Fast_fault_checks       [400 cycles]
  ├── Trace_logging           [80 cycles]
ISR_exit (context restore + overhead [250 cycles])
  ────────────────────────────────
  Total: 2650 cycles (44% utilization, 56% headroom)
```

### Layer 1: SMO Observer (5kHz, separate task)

Runs every other ISR tick. Provides corrected θ_hat and ω_hat to fast ISR via shared memory.

```
SMO_current_model            [800 cycles]
SMO_sign_function            [100 cycles]
SMO_low_pass_filter          [400 cycles]
SMO_angle_extraction         [800 cycles]
SMO_speed_estimation         [300 cycles]
SMO_overhead                 [200 cycles]
───────────────────────────────
Total: 3500 cycles (29% of 5kHz budget = 12000 cycles)
```

### Layer 2: Speed + APD (1kHz, alternating)

Speed loop on even ticks, APD on odd ticks. Each gets 500Hz effective rate.

```
Even ticks (speed loop):
  Speed_PI                    [300 cycles]
  Speed_ramp                  [100 cycles]
  Startup_SM                  [400 cycles]
  Observer_dwell              [200 cycles]
  Derating_policy             [300 cycles]
  Misc_1kHz                   [200 cycles]
  Total: 1500 cycles

Odd ticks (APD control):
  Power_feedforward           [400 cycles]
  APD_energy_loop             [800 cycles]
  APD_current_ref             [600 cycles]
  APD_fault_check             [200 cycles]
  Misc_APD                    [200 cycles]
  Total: 2200 cycles
```

### Layer 3: Background (100Hz, main loop)

Can be preempted by any higher layer.

```
Diagnostics                  [200 cycles]
Synthesis_logs               [200 cycles]
Noncritical_counters         [100 cycles]
Total: 500 cycles
```

## ISR Timing Diagram

```
10kHz tick (100µs period):
  ┌─────────────────────────────────────────────────────────────┐
  │ Fast ISR: ADC → Clarke → Park → PI → SVPWM → fault        │ 2650 cyc (44µs)
  │ [every tick]                                                │
  ├─────────────────────────────────────────────────────────────┤
  │ SMO task: full observer update (every 2nd tick)             │ 3500 cyc (58µs)
  │ [even ticks only]                                           │
  ├─────────────────────────────────────────────────────────────┤
  │ 1kHz tasks: speed loop or APD (every 6th tick, alternating)│ 1500-2200 cyc
  │ [tick % 6 == 0: speed, tick % 6 == 3: APD]                 │
  └─────────────────────────────────────────────────────────────┘

  Fast ISR worst-case: 2650 cycles (44%) — WELL UNDER 70% TARGET
  SMO task: 3500 cycles at 5kHz (29%) — comfortable
  1kHz tasks: 1500-2200 cycles — negligible at 1kHz rate
```

## Two-Layer Observer Design

The key architectural change from v1:

**Fast path (10kHz, in ISR):**
- Angle prediction: θ_pred = θ_hat + ω_hat × Ts
- No SMO computation
- Cost: ~50 cycles
- Accuracy: depends on ω_hat quality from last SMO update

**Slow path (5kHz, separate task):**
- Full SMO: current model + sign function + LPF + angle extraction
- Updates θ_hat and ω_hat
- Cost: ~3500 cycles
- Provides corrected state to fast ISR

**Prediction error analysis:**
- At 4000rpm (419 rad/s), prediction error over 1 SMO period (200µs): 419 × 200e-6 = 0.084 rad = 4.8°
- This is acceptable for FOC (typical tolerance: ±5-10° electrical)
- At 1000rpm: 0.021 rad = 1.2° — negligible

## Scheduling Conflicts

| Conflict | Resolution |
|----------|------------|
| Fast ISR + SMO both use shared θ/ω | SMO writes to shadow buffer, fast ISR reads from active buffer. Swap at SMO completion boundary (no atomic read needed). |
| Flash wait states | Copy fast ISR code to RAM at boot (`.ramfunc` section). SMO can stay in Flash (lower priority). |
| 1kHz speed + APD both at 1kHz | Alternate at 500Hz each. Both loops are slow enough for this. |

## Critical Path

The critical path is the **fast ISR at 10kHz**. Current estimate: 2650 cycles (44% utilization). The 70% target (4200 cycles) provides 1550 cycles of safety margin for:

- Compiler variance (+10-20%)
- Flash wait states (+5-10%)
- Worst-case branch paths (+5%)
- Interrupt nesting if needed

If fast ISR exceeds 4200 cycles after profiling:
1. Move SVPWM to lookup table (saves ~200 cycles)
2. Merge Id/Iq PI into single function (saves ~100 cycles)
3. Last resort: drop to 5kHz current loop (doubles budget to 12000 cycles)

## Boot Sequence

1. System init (clock, GPIO, ADC calibration)
2. Copy fast ISR code from Flash to RAM (`.ramfunc`)
3. Initialize sin/cos LUT in RAM (quarter-wave, 256 entries)
4. Initialize SMO state to safe defaults (θ=0, ω=0)
5. Initialize control state (zero current, speed = 0)
6. Start PWM outputs (duty = 50% for precharge)
7. Enable ADC + ISR + SMO timer
8. Enter background loop (diagnostics, communication)
