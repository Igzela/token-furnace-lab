# Scheduler Plan — Phase A-004

## Overview

TMS320F28035 timer-based ISR architecture. PWM module triggers ADC + ISR at 10kHz. Software timers derived from ISR counter for slower loops.

## Timer Configuration

| Timer | Source | Frequency | Period (cycles) |
|-------|--------|-----------|-----------------|
| PWM1/2/3 | ePWM module | 10kHz | 6000 (60MHz/10kHz) |
| ADC SOC | PWM1 SOCA | 10kHz | Synchronized to PWM |
| CPU Timer 0 | ISR | 10kHz | 15000 (ISR budget) |
| CPU Timer 1 | 1kHz task | 1kHz | 60000 |
| Software | Background | 100Hz | ISR counter modulo |

## Task Layering

### Layer 0: Hardware (10kHz, ISR context)

Priority: HIGHEST. Non-preemptable. Must complete within 15,000 cycles.

```
ISR_entry (context save)
  ├── ADC_read_calibrate     [300 cycles]
  ├── Clarke_transform       [150 cycles]
  ├── theta_source_mux       [80 cycles]
  ├── Park_transform         [200 cycles]
  ├── IqLimiter              [120 cycles]
  ├── Current_PI_Id          [250 cycles]
  ├── Current_PI_Iq          [250 cycles]
  ├── Inverse_Park           [200 cycles]
  ├── SVPWM                  [600 cycles]
  ├── SMO_observer           [3500 cycles]
  ├── Fast_fault_checks      [400 cycles]
  ├── Trace_logging          [200 cycles]
ISR_exit (context restore + overhead [800 cycles])
  ────────────────────────────────
  Total: 8850 cycles (41% headroom)
```

### Layer 1: Speed Loop (1kHz, ISR context but low priority)

Runs every 10th ISR tick. Still in ISR context but can be deferred 1 tick if needed.

```
Speed_PI              [300 cycles]
Speed_ramp            [100 cycles]
Startup_SM            [400 cycles]
Observer_dwell        [200 cycles]
Derating_policy       [300 cycles]
Misc_1kHz             [200 cycles]
───────────────────────────────
Total: 1500 cycles (within remaining ISR budget)
```

**Note**: Speed loop runs AFTER current loop in same ISR. Total ISR budget with speed loop: 8850 + 1500 = 10350 cycles (31% headroom).

### Layer 2: APD Control (1kHz, separate task or ISR)

Option A: Same ISR as speed loop (simplest, no context switch overhead)
Option B: Separate high-priority task (if ISR too long)

```
Power_feedforward     [400 cycles]
APD_energy_loop       [800 cycles]
APD_current_ref       [600 cycles]
APD_fault_check       [200 cycles]
Misc_APD              [200 cycles]
───────────────────────────────
Total: 2200 cycles
```

**Recommendation**: Run APD in Layer 1 (same ISR, alternating with speed loop). Even-numbered ticks: speed loop. Odd-numbered ticks: APD control. This keeps total ISR at 8850 + 1500 = 10350 cycles with 31% headroom.

### Layer 3: Background (100Hz, main loop or lowest-priority ISR)

Can be preempted by any higher layer. Runs when ISR is idle.

```
Diagnostics           [200 cycles]
Synthesis_logs        [200 cycles]
Noncritical_counters  [100 cycles]
───────────────────────────────
Total: 500 cycles
```

## ISR Timing Diagram

```
10kHz tick (100µs period):
  ┌─────────────────────────────────────────────────────────┐
  │ ISR: ADC + Clarke + Park + PI + SVPWM + SMO + fault   │ 8850 cyc (59µs)
  │ [even tick] Speed loop or APD loop                     │ 1500 cyc (10µs)
  │ [odd tick]  APD loop or Speed loop                     │ 2200 cyc (15µs)
  │ Trace write                                            │ 200 cyc (1.3µs)
  │ TOTAL: 10550-11250 cyc (70-75µs)                       │
  │ HEADROOM: 25-30%                                       │
  └─────────────────────────────────────────────────────────┘
  Background tasks fill remaining 25-30% of CPU time.
```

## Scheduling Conflicts

| Conflict | Resolution |
|----------|------------|
| Speed loop + APD loop both at 1kHz | Alternate: even ticks = speed, odd ticks = APD. Each gets 500Hz effective rate, which is sufficient for both. |
| SMO takes 23% of ISR budget | If profiling shows actual cycles higher, consider: (1) 5kHz current loop with 2x oversampling, (2) reduced-order observer, (3) CORDIC hardware for atan2. |
| Flash wait states | C28x Flash at 36MHz with 60MHz CPU = 0-3 WS. Code in Flash, LUT in RAM. ISR-critical code can be copied to RAM at boot. |

## Critical Path

The critical path is the 10kHz ISR. The slowest module is SMO at 3500 cycles. If SMO is profiled higher than estimated:

1. **First optimization**: Replace atan2 LUT lookup with CORDIC (saves ~100 cycles)
2. **Second optimization**: Reduce SMO from full-order to reduced-order (saves ~1000 cycles)
3. **Third option**: Drop to 5kHz current loop (doubles ISR budget to 30,000 cycles)

## Boot Sequence

1. System init (clock, GPIO, ADC calibration)
2. Copy ISR-critical code from Flash to RAM (optional, for 0 WS)
3. Initialize sin/cos LUT in RAM (quarter-wave, 256 entries)
4. Initialize control state to safe defaults (zero current, speed = 0)
5. Start PWM outputs (duty = 50% for precharge)
6. Enable ADC + ISR
7. Enter background loop (diagnostics, communication)
