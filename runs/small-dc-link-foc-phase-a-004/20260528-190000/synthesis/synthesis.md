# Synthesis: Phase A-004 Fixed-Point CPU/RAM Budget

**Overall verdict**: PASS_WITH_NOTES
**Target MCU**: TMS320F28035 (60MHz, 12KB RAM)
**ISR budget**: 10kHz → 15,000 cycles

## CPU Budget

| Module | Cycles | % of Budget |
|--------|--------|-------------|
| SMO observer | 3500 | 23.3% |
| SVPWM | 600 | 4.0% |
| Current PI (2x) | 500 | 3.3% |
| Clarke + Park + Inv Park | 550 | 3.7% |
| Fast fault checks | 400 | 2.7% |
| ADC + calibrate | 300 | 2.0% |
| IqLimiter | 120 | 0.8% |
| theta_mux | 80 | 0.5% |
| Trace + overhead | 1800 | 12.0% |
| **ISR total** | **8850** | **59%** |
| **ISR headroom** | **6150** | **41%** |

Speed loop (1kHz): 1500 cycles. APD loop (1kHz): 2200 cycles.
Alternating schedule: 8850 + 1500 = 10350 cycles (31% headroom).

## RAM Budget

| Section | Bytes |
|---------|-------|
| FOC control state | 128 |
| PI controllers (4x) | 96 |
| SMO state | 64 |
| SVPWM state | 32 |
| Startup SM | 16 |
| APD state | 48 |
| Fault state | 32 |
| Scheduler | 16 |
| Trace buffer | 2048 |
| Sin/cos LUT | 512 (full) or 256 (quarter-wave) |
| ADC calibration | 32 |
| Comm buffer | 64 |
| Stack | 512 |
| **Total** | **3504 (full) / 3016 (optimized)** |
| **Headroom** | **8784 (72%)** |

## Fixed-Point Audit

- No Q-format overflow for any signal in operating range
- All multiplications fit C28x 32-bit intermediate range
- PI integrators require anti-windup clamp (standard practice)
- Recommended: Q15 for currents/speeds, Q12 for voltages/gains, Q20 for angle

## Scheduler Plan

- 10kHz ISR: current loop (ADC → Clarke → Park → PI → SVPWM → SMO → fault)
- 1kHz even ticks: speed loop
- 1kHz odd ticks: APD control
- Background: diagnostics, logging, communication

## Risk Summary

| Risk | Level | Mitigation |
|------|-------|------------|
| SMO cycle count uncertainty | HIGH | Profile on actual C28x; reduced-order observer as fallback |
| ISR frequency conflict | HIGH | Alternate speed/APD at 500Hz; copy ISR to RAM |
| PI integrator precision | MEDIUM | Anti-windup clamp; verify with step response |
| Quarter-wave LUT accuracy | MEDIUM | 128-entry + interpolation or 256-entry full LUT |
| Stack depth | LOW | 512B assumed; add canary + static analysis |
| Flash wait states | LOW | Copy ISR to RAM or budget 1-2 WS |

## Pass Criteria

- [x] ISR budget within 15,000 cycles: 8850 (59%) — PASS
- [x] RAM fits in 12KB: 3.5KB (29%) — PASS
- [x] No Q-format overflow — PASS
- [x] Scheduler plan with priority ordering — PASS
- [x] Risk matrix with actionable mitigations — PASS
- [ ] SMO cycle count verified on hardware — DEFERRED to Phase A-005

## Verdict

**PASS_WITH_NOTES**: CPU and RAM budgets are well within constraints. Fixed-point analysis shows no overflow. Two HIGH risks (SMO cycle count, ISR frequency conflict) have clear mitigations but require hardware profiling to close. Proceed to Phase A-005 with SMO profiling as first validation gate.
