# Phase A-003: GPT Final Review

**Score: 88/100 — PASS_WITH_NOTES**
**Verdict**: Implementation-ready after adding fixed-point scaling tests and safety interlocks

## Required Additions

### A-003.0: Fixed-Point Scaling Dry Test (MANDATORY)

Test without motor power:
- Q15 current conversion: ADC raw → amps → Q15 → amps
- Vdc conversion: ADC raw → volts → Q15/q12
- angle_t wrap: 0°, 90°, 180°, 270°, 360°
- sin/cos lookup correctness
- Park/Inverse Park round-trip
- SVPWM known vectors
- IqLimiter known cases
- PI gain KiTs scaling

### Safety Interlocks (Before Any PWM-to-Motor)

- Hardware emergency stop
- PWM trip-zone verified
- Overcurrent comparator verified
- DC bus precharge/discharge check
- UVLO/OV thresholds tested with simulated input
- ADC saturation detection
- PWM disabled on watchdog reset
- Fault latch requires manual clear
- Maximum duty clamp
- Maximum Iq clamp
- Startup timeout

### Conservative Initial Limits

- OC threshold: 2A (lower than final 5A)
- Iq max: 0.5A initially
- PWM duty clamp: conservative
- Use current-limited source if possible

## Updated Milestone Sequence

```
A-003.0: Fixed-point and safety dry test
A-003.1: ADC/PWM sanity
A-003.2: Open-loop voltage vector
A-003.3: Current-loop validation
A-003.4: SVPWM + Vdc feedforward + IqLimiter
A-003.5: Passive SMO observer validation
A-003.6: Sensorless handover dry run
A-003 closeout: Phase D readiness verdict
```

## Phase D Entry Gate

```yaml
phase_d_entry_requirements:
  phase_a_003: PASS
  current_loop:
    stable_at: 1A
  vdc_feedforward: verified
  iq_limiter: verified
  observer_passive: plausible
  trace_buffer: working
  trip_zone: verified
```
