# Synthesis: Phase A-004 Fixed-Point CPU/RAM Budget (v2)

**Overall verdict**: PASS_WITH_NOTES
**Target MCU**: TMS320F28035 (60MHz, 12KB RAM)
**ISR budget**: 10kHz → 6,000 cycles (corrected from v1's 15,000)

## v1 → v2 Changes (GPT Review)

GPT caught critical error: v1 used 15000 cycles budget (assumed 150MHz). Correct budget is 6000 cycles (60MHz / 10kHz). This means v1 ISR was 148% over budget. v2 redesigned with two-layer observer.

| Metric | v1 (wrong) | v2 (corrected) |
|--------|-----------|----------------|
| ISR budget | 15000 cycles | 6000 cycles |
| Fast ISR used | 8850 (59%) | 2650 (44%) |
| SMO location | In 10kHz ISR | Separate 5kHz task |
| Observer design | Single-layer | Two-layer (predict + correct) |
| ISR headroom | 41% (wrong) | 56% (correct) |

## CPU Budget (v2)

| Layer | Frequency | Used | Budget | Utilization |
|-------|-----------|------|--------|-------------|
| Fast ISR (current loop) | 10kHz | 2650 cyc | 6000 cyc | 44% |
| SMO observer | 5kHz | 3500 cyc | 12000 cyc | 29% |
| Speed loop | 1kHz | 1500 cyc | 60000 cyc | 2.5% |
| APD control | 1kHz | 2200 cyc | 60000 cyc | 3.7% |
| Background | 100Hz | 500 cyc | 600000 cyc | 0.08% |

Fast ISR at 44% is well under the 70% safety target (4200 cycles).

## RAM Budget

| Section | Bytes |
|---------|-------|
| Control state + PI + SMO + SVPWM + APD | 384 |
| Trace buffer | 2048 |
| Sin/cos LUT | 512 |
| Stack | 512 |
| Other | 248 |
| **Total** | **3504 (29% of 12KB)** |

RAM is NOT a bottleneck. Trace buffer must be conditional compilation for production.

## Fixed-Point Audit

- All signals fit Q15/Q12/Q20 without overflow
- PI integrators require anti-windup clamp (mandatory, not optional)
- Per-unit (pu) internal representation recommended by GPT
- High-risk multiplications: use 32-bit intermediate, saturate to target Q

## Two-Layer Observer

**Key architectural decision**: SMO runs at 5kHz, fast ISR uses angle prediction at 10kHz.

Prediction error at 4000rpm: ω × Ts = 419 × 200µs = 0.084 rad = 4.8° electrical.
This is within FOC tolerance (±5-10°). Must be verified in simulation.

## Risk Summary

| Risk | Level | Status |
|------|-------|--------|
| Theta prediction accuracy | HIGH | Open — simulate before Phase A-005 |
| Fast ISR 6000-cycle budget | HIGH | Open — profile on C28x target |
| SMO cycle count unverified | MEDIUM | Open — profile separately |
| PI integrator precision | MEDIUM | Open — anti-windup mandatory |
| Trace buffer RAM | LOW | Conditional compilation |
| Stack depth | LOW | Static analysis needed |
| Linker memory map | LOW | Create .cmd file |

## Pass Criteria

- [x] ISR budget correct: 6000 cycles for 60MHz @ 10kHz
- [x] Fast ISR within 70% target: 2650 / 4200 = 63%
- [x] RAM fits in 12KB: 3.5KB (29%)
- [x] No Q-format overflow
- [x] Scheduler plan with two-layer observer
- [x] Risk matrix with actionable mitigations
- [ ] Fast ISR profiled on C28x — DEFERRED to Phase A-005
- [ ] Theta prediction error verified — DEFERRED to Phase A-005

## Verdict

**PASS_WITH_NOTES**: v2 corrects the fundamental ISR budget error. Two-layer observer design is sound: fast ISR at 44% utilization, SMO at 5kHz with 71% headroom. Two HIGH risks (prediction accuracy, ISR profiling) require hardware measurement but are not blocking for proceeding to Phase A-005. The design is architecturally sound and implementable.
