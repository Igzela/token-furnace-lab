# Phase B-004: GPT Final Review

**Score: 78/100 — PASS_WITH_NOTES**
**Verdict**: Not implementation-ready until trace RAM and angle format fixed

## Status by Component

| Component | Status |
|-----------|--------|
| State machine | PASS |
| Dwell logic | PASS_WITH_NOTES |
| Alpha rollback | PASS_WITH_NOTES |
| Fallback profiles | PASS |
| Trace buffer | FAIL (56KB > 12KB RAM) |
| Fixed-point angles | NEEDS_FIX (q12 → angle_t) |
| Fault coverage | PARTIAL |

## Required Corrections

### 1. Trace Buffer — FAIL
- 28 bytes × 2048 = 56KB exceeds 12KB RAM budget
- Fix: 16 bytes × 128 = 2KB compact trace, fault_capture_only mode
- Full 2048 trace only for host simulation

### 2. Angle Type — NEEDS_FIX
- Replace q12 angles with `uint16_t angle_t` (0-65535 = 0-2π)
- Angle thresholds: 45°≈8192, 35°≈6372, 30°≈5461, 20°≈3641
- Use `angle_diff()` for wrapped delta

### 3. Alpha Rollback — TOO_AGGRESSIVE
- 1% per sample at 10kHz = full rollback in 10ms (too fast vs 100ms blend)
- Fix: advance 0.1%/sample, rollback 0.5-1.0%/sample, with hysteresis

### 4. Transition Gates — NEED CONDITION+DWELL
- Each transition needs both dwell AND conditions (not dwell-only)
- Add SVPWM_saturated, current_tracking_stable, observer_input_valid

### 5. Missing Faults
- Add: APD_PRECHARGE_TIMEOUT, OBSERVER_LOCK_TIMEOUT, SVPWM_SATURATED_TIMEOUT, STARTUP_TIMEOUT, THETA_JUMP_FAULT
- Add escalation: first fail→fallback, second→strong, third→FAULT_LATCHED

### 6. Counter Tick Rate
- Must explicitly state all counters tick at 10kHz ISR rate

## GPT Recommended Trace Format

```c
typedef struct {
    uint16_t tick;          // 16-bit timestamp
    uint8_t  state;
    uint8_t  fault_code;
    int16_t  theta_err;     // millidegrees
    uint16_t alpha_x1000;
    int16_t  omega_ref_x10;
    int16_t  omega_est_x10;
    int16_t  iq_ref_ma;
    int16_t  iq_meas_ma;
    uint16_t vdc_mv;
    uint16_t vapd_mv;
    uint8_t  flags;         // packed: observer_valid|speed_valid|svpwm_sat|iq_lim|apd_ready|uvlo|ov|oc
} CompactTraceEntry;       // 16 bytes × 128 = 2KB
```
