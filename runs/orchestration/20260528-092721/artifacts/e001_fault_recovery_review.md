# Phase E-001: Runtime Fault Recovery Model -- Structured Review

**Reviewer**: Implementer (structured review)
**Model under review**: `runs/small-dc-link-foc-phase-e-001/20260528-130000/model_outputs/fault_recovery_model.md`
**GPT review reference**: `runs/small-dc-link-foc-phase-e-001/20260528-130000/model_outputs/gpt-review.md`
**Date**: 2026-05-28

---

## Score

**76 / 100**

---

## Verdict

**PASS_WITH_NOTES**

The model is substantially correct and GPT's 7 corrections (v1 to v2) are all properly applied. However, secondary issues remain: missing state definitions in the transition matrix, incomplete fault coverage in degraded/recovery states, underspecified cold-start timing, and two orphaned fault codes. None of these are blocking for understanding, but they would block clean implementation without interpretation.

---

## Findings

### F-01: Undefined states PRECHARGE and ALIGN referenced in transition matrix (Severity: HIGH)

The RESTART_PENDING state (model line 91) references `PRECHARGE` and `ALIGN` as destinations in the cold start sequence:

```
cooldown_done + speed_zero -> PRECHARGE -> ALIGN (cold start)
```

However, PRECHARGE and ALIGN do not appear in the State Definitions table (model lines 5-16). The table defines 10 states; these two are absent. Without defined behavior, output actions, and timeout conditions for these states, the cold-start path is underspecified.

**Evidence**: `fault_recovery_model.md:91` references undefined states; `fault_recovery_model.md:5-16` state table omits them.

### F-02: Two fault codes missing from fault code table (Severity: MEDIUM)

The fault code table (model lines 287-308) lists 20 entries (codes 0-19). However, the fault classes section (model lines 246-266) references:
- `precharge_fail` (manual_intervention class, line 263)
- `startup_tmo` (recoverable_fault_retry_3 class, line 253)

Neither appears in the fault code table. Code 4 is `PRECHARGE_TMO` which may correspond to `precharge_fail`, but the naming is inconsistent. `startup_tmo` has no corresponding code at all.

**Evidence**: `fault_recovery_model.md:253` references `startup_tmo`; `fault_recovery_model.md:263` references `precharge_fail`; `fault_recovery_model.md:287-308` fault code table omits both.

### F-03: OBSERVER_DEGRADED missing hard-fault transitions (Severity: MEDIUM)

The OBSERVER_DEGRADED state (model lines 50-54) defines only 3 transitions: obs_recovered, obs_extrapolate_max, vdc_uvlo, timeout_500ms_2s. It does not define transitions for:
- oc_trip
- gate_driver_fault
- pwm_tripzone
- emergency_stop
- adc_invalid
- over_temperature

If any of these occur while in OBSERVER_DEGRADED (a plausible scenario -- the motor is running with degraded angle estimation), the model provides no defined behavior. The fault-state transition matrix only partially covers degraded states.

**Evidence**: `fault_recovery_model.md:50-54` -- OBSERVER_DEGRADED has 4 transitions; `fault_recovery_model.md:22-41` -- FOC_NORMAL has 15 transitions.

### F-04: FLYING_RESTART missing electrical fault transitions (Severity: MEDIUM)

The FLYING_RESTART state (model lines 56-60) defines 4 transitions: sync_ok, sync_fail, timeout_3s, vdc_uvlo. Missing:
- oc_trip (motor is running with active PWM during re-sync)
- gate_driver_fault
- emergency_stop
- over_temperature

These are safety-critical. During re-sync, the controller applies I-f current patterns, which could trigger overcurrent if the motor has seized or the load changed.

**Evidence**: `fault_recovery_model.md:56-60` -- FLYING_RESTART has 4 transitions.

### F-05: CONTROLLED_DECEL missing electrical fault transitions (Severity: MEDIUM)

The CONTROLLED_DECEL state (model lines 66-69) defines only 3 transitions: speed_zero, vdc_uvlo, timeout_5s. Missing:
- oc_trip
- gate_driver_fault
- emergency_stop

During active deceleration with PWM enabled, overcurrent or gate faults could occur.

**Evidence**: `fault_recovery_model.md:66-69` -- CONTROLLED_DECEL has 3 transitions.

### F-06: Cold start sequence timing undefined (Severity: MEDIUM)

The cold start sequence (model line 282) defines the path:

```
PRECHARGE -> ALIGN -> IF_RAMP -> OBSERVER_CHECK -> BLEND -> FOC
```

No timing constants are defined for:
- PRECHARGE phase duration (voltage settling time for 22uF DC-link)
- ALIGN phase duration (rotor alignment pulse width)
- IF_RAMP duration (I-f frequency ramp from 0 to target)
- OBSERVER_CHECK window (how long to verify observer lock before blending)

The Timing Constants table (model lines 312-329) does not cover any cold-start phase durations. This is a gap relative to the task requirement for restart/retry logic (task.md line 22).

**Evidence**: `fault_recovery_model.md:282` cold start path; `fault_recovery_model.md:312-329` timing table lacks cold-start entries.

### F-07: Speed extrapolation mechanism underspecified (Severity: LOW)

The observer extrapolation (model line 104) uses:

```
theta_est = theta_last + omega_last * dt
```

This is correct in form, but:
1. What if `omega_last` is zero or stale (observer lost lock at standstill)?
2. What is the extrapolation update rate? Should it be the PWM frequency (10kHz)?
3. Is there a maximum extrapolation angle error threshold before declaring extrapolation failed?

The model says "extrapolation is accurate for 10-20ms at moderate speed" (line 119) but does not define the accuracy check.

**Evidence**: `fault_recovery_model.md:104` extrapolation formula; `fault_recovery_model.md:119` accuracy claim without validation mechanism.

### F-08: FOC_DERATED incomplete transition set (Severity: LOW)

FOC_DERATED (model lines 42-47) has 6 transitions but is missing:
- apd_fault (APD failure during derated operation)
- gate_driver_fault
- over_temperature
- emergency_stop
- adc_invalid

**Evidence**: `fault_recovery_model.md:42-47`.

### F-09: Observer recovery window vs extrapolation_max ambiguity (Severity: LOW)

The timing table defines:
- observer_extrapolate_max: 10-20ms (line 315)
- observer_recovery_window: 0.5-2s (line 316)

The recovery strategy (line 109-116) says:
- Phase 1 (0-10ms): extrapolated-theta bridge
- Phase 2 (10-100ms): recovery check
- Phase 3 (>100ms): PASSIVE_COAST

There is a contradiction: the timing table says extrapolation max is 10-20ms and recovery window is 0.5-2s, but the strategy phases say recovery window is 10-100ms and coast happens at >100ms. The recovery_window value of 0.5-2s does not match the 10-100ms recovery phase. One of these is stale from v1 (the 2s freeze was removed per GPT correction).

**Evidence**: `fault_recovery_model.md:109-116` phase timing vs `fault_recovery_model.md:315-316` timing table.

### F-10: APD_DEGRADED single-phase path may need controlled decel (Severity: LOW)

For single-phase APD fault (model line 75):

```
ripple_exceeds_limit (1ph) -> PASSIVE_COAST (immediate)
```

Immediate PASSIVE_COAST with PWM disabled is the safest option, but a controlled deceleration (CONTROLLED_DECEL) might be preferable if the motor is at high speed and sudden coast causes water hammer. This depends on the pump installation (vertical vs horizontal, check valve presence). The model does not discuss this tradeoff.

**Evidence**: `fault_recovery_model.md:75` immediate PASSIVE_COAST for single-phase APD.

---

## Corrections

### C-01: Add PRECHARGE and ALIGN to state definitions table

Add two rows to the State Definitions table:

| State | Description | Motor | PWM | Controller |
|-------|-------------|-------|-----|------------|
| PRECHARGE | DC-link voltage ramp-up | Stopped | Disabled | Precharge relay control, Vdc monitoring |
| ALIGN | Rotor alignment pulse | Stopped | Active | Fixed current vector, fixed angle |

Define timeout and exit conditions for each. Suggested values:
- PRECHARGE: timeout 500ms, exit when Vdc > target (e.g., 270V), else FAULT_LATCHED
- ALIGN: timeout 200ms (1-2 electrical periods at standstill), exit when flux established, else RESTART_PENDING

### C-02: Complete the fault code table

Add entries for:
- Code 20: `STARTUP_TMO` | High | Recoverable | 3 retries (maps to `startup_tmo` in fault classes)
- Code 21: `PRECHARGE_FAIL` | Critical | Manual | No (maps to `precharge_fail` in fault classes)

Or reconcile the existing naming: rename `PRECHARGE_TMO` (code 4) to match `precharge_fail`, and add `STARTUP_TMO` as a new code.

### C-03: Add universal hard-fault transitions to all active/degraded states

Add a universal rule at the top of the transition matrix:

```
UNIVERSAL (all active and degraded states):
  oc_trip              -> FAULT_LATCHED + PWM disable
  gate_driver_fault    -> FAULT_LATCHED + PWM disable
  pwm_tripzone         -> FAULT_LATCHED + PWM disable
  emergency_stop       -> FAULT_LATCHED + PWM disable
  watchdog_reset       -> FAULT_LATCHED
  adc_invalid          -> FAULT_LATCHED + PWM disable
  over_temperature     -> FAULT_LATCHED + PWM disable
```

This eliminates the per-state omission problem (F-03 through F-05, F-08).

### C-04: Define cold-start phase timing

Add to the Timing Constants table:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| precharge_timeout | 500ms | 22uF charges in <100ms through限流 resistor; 5x margin |
| align_duration | 200ms | 1-2 electrical periods at standstell, sufficient for flux buildup |
| if_ramp_duration | 300ms | Matches phase-b-001/002 I-f ramp specification |
| observer_check_window | 100ms | Verify observer lock before blend, matches phase-b-003 |

**Evidence**: phase-b-002 specifies 300ms I-f ramp; phase-b-003 specifies observer-gated blend.

### C-05: Specify extrapolation failure detection

Add to the observer recovery strategy (after line 106):

```
Extrapolation failure detection:
  - If |theta_extrapolated - theta_measured| > 60deg when observer partially relocks:
    -> reject extrapolation -> PASSIVE_COAST immediately
  - If omega_last < min_speed_threshold (e.g., 100 rpm):
    -> extrapolation unreliable -> reduce to 5ms max bridge -> PASSIVE_COAST
  - Extrapolation update rate = PWM frequency (10kHz)
```

### C-06: Resolve observer recovery timing inconsistency

Either:
(a) Update timing table: observer_recovery_window to 100ms (matching strategy Phase 2/3), OR
(b) Update strategy: extend recovery check to 0.5-2s and add PASSIVE_COAST at >2s

Recommendation: option (a) -- the 10-100ms window is physically correct for extrapolated theta validity. Remove the 0.5-2s value or reclassify it as "total OBSERVER_DEGRADED state timeout" rather than recovery window.

### C-07: Document water-hammer risk for single-phase APD immediate coast

Add a note under the single-phase APD strategy:

```
Note: If pump installation has water-hammer risk (vertical riser, no check valve),
consider CONTROLLED_DECEL before PASSIVE_COAST. Add a system-level configuration
flag: apd_1ph_coast_mode = {IMMEDIATE, CONTROLLED} with default IMMEDIATE.
```

---

## Final Recommendation

**PASS_WITH_NOTES -- implementation-ready with corrections.**

The model is structurally sound. All 8 task-required fault cases are addressed. The GPT v1-to-v2 corrections are properly applied. The 10-state design is the right granularity for this system. The fault class separation (hard_fault / recoverable / degraded / manual) is correct for a safety-critical pump drive.

The 10 findings are all secondary -- they represent underspecification rather than incorrectness. None require a fundamental redesign. The corrections (C-01 through C-07) are all additive: adding missing states, completing the transition matrix, and filling timing gaps.

**Priority for implementation**:
1. C-03 (universal hard-fault rules) -- most impactful safety fix
2. C-01 (PRECHARGE/ALIGN states) -- required for cold-start implementation
3. C-04 (cold-start timing) -- required for state machine coding
4. C-02 (fault code table completion) -- required for diagnostics
5. C-05, C-06, C-07 -- refinement, can be addressed during implementation

**Impact on downstream phases**:
- Phase A-004 (fixed-point CPU budget): no impact -- state machine complexity is within budget
- Phase D (integration/testing): C-01 and C-04 must be resolved before test procedure can reference cold-start phases
- Hardware test (phase-a-003): universal fault rules (C-03) must be in place before safety interlock testing

