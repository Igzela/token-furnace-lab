# Phase A-004: Fixed-Point CPU/RAM Budget and Overflow Audit

## Goal

Verify that FOC + SMO + startup state machine + APD control can run on TMS320F28035 (60MHz, 12KB RAM, 10kHz ISR) without exceeding cycle budget, RAM, or fixed-point range.

## Target MCU Constraints

- **CPU**: TMS320F28035, 60MHz, 150 MIPS peak
- **ISR budget**: 10kHz = 15,000 cycles per current loop iteration
- **RAM**: 12KB total (control structs + trace + stack + LUTs)
- **Flash**: 128KB (code + constants + sin/cos LUT)
- **PWM**: 10kHz switching, ADC sync

## Questions to Answer

1. How many cycles does each module consume in the 10kHz current ISR?
2. Is the total ISR budget (Clarke + Park + SVPWM + PI + SMO + IqLimiter + fault checks) within 15,000 cycles?
3. What is the APD control update rate — 10kHz, 20kHz, or PWM高频 but 低频 update?
4. Do Q15/Q12/Q16 gains overflow for any signal range?
5. Are Q formats sufficient for omega_e, Vdc, Iq, PI integrator, SMO state?
6. Does 2KB trace buffer + control state + stack fit in 12KB RAM?
7. Should sin/cos LUT go in Flash or RAM?
8. Which modules must run at reduced frequency?

## Required Outputs

1. **cpu_budget_table.yaml** — Per-module cycle estimates, 10kHz ISR total budget
2. **ram_budget_table.yaml** — Control structs, trace, stack, LUT, driver buffer breakdown
3. **fixed_point_range_audit.md** — Q format, base unit, max value, overflow risk per signal
4. **scheduler_plan.md** — 10kHz / 1kHz / APD / background task layering
5. **risk_matrix.yaml** — Must-optimize, can-downclock, can-LUT, can-defer items

## Initial Scheduling Hypothesis

```
10kHz_current_ISR:
  - ADC read/calibrate
  - Clarke transform
  - theta_source_mux (observer vs encoder vs open-loop)
  - Park transform
  - IqLimiter fast path
  - Current PI (Id + Iq)
  - Inverse Park
  - SVPWM
  - fast fault checks
  - minimal trace/event logging

1kHz_task:
  - Speed PI
  - Speed ramp
  - startup state machine counters
  - observer validity dwell logic
  - derating policy

APD_task:
  - 100Hz power feedforward
  - APD energy loop
  - APD current reference

background:
  - diagnostics
  - synthesis logs
  - noncritical counters
```

## Key Assumptions from Previous Derivations

- Motor: 300V, 4000rpm, ψ_f = 0.08-0.103
- DC-link: 22µF + 16µF APD (H-bridge)
- Current loop: 10kHz (ISR)
- Speed loop: 1kHz (task)
- SMO: sliding mode observer, needs quantization
- SVPWM: space vector modulation, per-cycle update
- APD: active power decoupling, 100Hz energy loop + fast current loop

## Evaluation Criteria

- All cycle budgets within 15,000 cycles at 10kHz
- All RAM fits in 12KB with 2KB trace buffer
- No Q-format overflow for any signal in operating range
- Scheduler plan with clear priority ordering
- Risk matrix with actionable mitigation for each HIGH/MEDIUM risk
