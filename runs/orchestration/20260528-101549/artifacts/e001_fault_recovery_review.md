# Phase E-001: Fault Recovery Model Review

**Reviewer**: implementer (token-furnace orchestration)
**Date**: 2026-05-28
**Model reviewed**: runs/small-dc-link-foc-phase-e-001/20260528-130000/model_outputs/fault_recovery_model.md
**Model version**: v2 (GPT-corrected)
**Previous review**: GPT review scored 72/100 PASS_WITH_NOTES

---

## Score

**82 / 100**

## Verdict

**PASS_WITH_NOTES**

## Confidence

**HIGH** — Review grounded in the fault recovery model, the GPT review corrections, the phase-b-004 startup state machine spec, and the technical route document. All claims have evidence paths.

---

## Findings

### F01: Missing `current_sensor_fault` in UNIVERSAL Hard-Fault Section

- **Severity**: HIGH
- **Blocking**: Yes — current sensor loss in any PWM-active state is catastrophic for sensorless FOC
- **Evidence path**: fault_recovery_model.md, UNIVERSAL section (line 24-33) vs FOC_NORMAL section (line 55)
- **Claim**: The UNIVERSAL transition block covers oc_trip, gate_driver_fault, pwm_tripzone, emergency_stop, watchdog_reset, adc_invalid, and over_temperature. It does NOT include `current_sensor_fault`. However, `current_sensor_fault → FAULT_LATCHED + PWM disable` appears only in the FOC_NORMAL state. If a current sensor fails while in FOC_DERATED, OBSERVER_DEGRADED, or APD_DEGRADED, there is no defined transition. In sensorless FOC, loss of current feedback makes the observer and current loop blind — this must fault from every PWM-active state.
- **Correction**: Add `current_sensor_fault → FAULT_LATCHED + PWM disable` to the UNIVERSAL section. This is a hardware-level fault (like OC or gate driver) and must apply from every state where PWM is active.

### F02: Missing `Vapd_ov` (APD Overvoltage) Fault Path

- **Severity**: MEDIUM
- **Blocking**: No — but a safety gap for single-phase systems
- **Evidence path**: fault_recovery_model.md, APD_DEGRADED section (line 89-93); gpt-review.md section 1 (line 24-30)
- **Claim**: The GPT review explicitly lists `vapd_ov` as a missing hard-fault path. The fault recovery model mentions "Vapd out of range" as the APD fault trigger but does not explicitly define a transition for Vapd overvoltage. For single-phase systems, APD overvoltage could indicate capacitor failure or regenerative energy with no dump path, which is a hardware-safety event.
- **Correction**: Add `vapd_ov → FAULT_LATCHED + PWM disable` to the UNIVERSAL section (or at minimum to FOC_NORMAL and APD_DEGRADED). This should be treated as a hard fault, not a degraded-mode transition.

### F03: Undefined States in Cold-Start Sequence (IF_RAMP, OBSERVER_CHECK, BLEND)

- **Severity**: MEDIUM
- **Blocking**: No — but creates implementation ambiguity
- **Evidence path**: fault_recovery_model.md, Restart/Retry Logic section (line 310-323); state_machine_spec.md states table
- **Claim**: The cold-start sequence in RESTART_PENDING references `IF_RAMP → OBSERVER_CHECK → BLEND → FOC` as intermediate steps. However, the State Definitions table (lines 1-18) does not define IF_RAMP, OBSERVER_CHECK, or BLEND as states. These states ARE defined in the phase-b-004 startup state machine (state_machine_spec.md, lines 10-21), but the fault recovery model treats them as implicit. This creates a gap: the fault recovery model defines 12 states, but the actual runtime needs 15+ states to cover the full startup sequence. Transitions from IF_RAMP, OBSERVER_CHECK, and BLEND back to fault states are not defined in the fault recovery transition matrix.
- **Correction**: Either (a) formally add IF_RAMP, OBSERVER_CHECK, and BLEND to the State Definitions table with their own fault transitions, or (b) add an explicit cross-reference to the phase-b-004 state machine and define the fault transitions from each of those states. Option (a) is preferred for a self-contained fault recovery model.

### F04: `retry_count` Increment Semantics Ambiguous

- **Severity**: LOW
- **Blocking**: No — implementation detail, but could cause off-by-one
- **Evidence path**: fault_recovery_model.md, Cold Start Sequence section (line 311-316)
- **Claim**: The cold-start sequence shows `retry_count++` at the top of the RESTART_PENDING handler, followed by `if retry_count >= 3 → FAULT_LATCHED`. This means: entry 1 (count=1), entry 2 (count=2), entry 3 (count=3 → fault). This gives 2 actual retry attempts before latching, not 3. If the intent is 3 retries (as stated in the fault class definition `recoverable_fault_retry_3`), the counter should start at 0 and latch at `>= 3`, or the increment should happen after the check. The fault code table (line 326) says "3 retries" for recoverable faults, but the transition matrix implements only 2.
- **Correction**: Clarify the retry semantics. Either: (a) initialize retry_count=0, check `>= 3` after increment (gives 3 attempts: counts 1, 2, 3), or (b) document that the first attempt is attempt 1 and only 2 retries are allowed. Align with the fault class definition which says "3 retries with escalation."

### F05: `observer_extrapolate_max` Upper Bound May Be Too Short at Low Speed

- **Severity**: LOW
- **Blocking**: No — the model already handles this case
- **Evidence path**: fault_recovery_model.md, Observer Lock Loss strategy (line 149-156)
- **Claim**: The extrapolation bridge is stated as 10-20ms. At low speed (<100 rpm), the model correctly reduces this to 5ms max. However, the 10-20ms range itself is stated without specifying what happens at moderate speeds (e.g., 1000-2000 rpm). At 2000 rpm (209 rad/s mech, ~6000 elec rad/s for 3-pole-pair), 10ms of extrapolation accumulates ~6 degrees of error from speed estimation uncertainty alone. This is within the 30-degree relock threshold but consumes budget. The model should specify whether the 10ms vs 20ms choice depends on speed.
- **Correction**: Add a speed-dependent note: at speeds > 3000 rpm, use 10ms max; at 1000-3000 rpm, 15ms; below 1000 rpm, 20ms (but the 5ms limit for <100 rpm already covers the worst case). This is a refinement, not a correction.

### F06: No Thermal Derating Before Over-Temperature Fault

- **Severity**: MEDIUM
- **Blocking**: No — but a robustness gap
- **Evidence path**: fault_recovery_model.md, State Definitions (line 18), UNIVERSAL section (line 32)
- **Claim**: The model defines `over_temperature → FAULT_LATCHED + PWM disable` as a hard fault. There is no intermediate thermal derating state (e.g., reduce Iq when motor temperature exceeds 80% of limit but is below the trip threshold). For a water pump application where thermal time constants are long (minutes), an immediate hard fault on over-temperature is aggressive. A derated mode could keep the pump running at reduced power while alerting the user, rather than an immediate shutdown that could cause water hammer.
- **Correction**: Add an `over_temp_warning` event that transitions to FOC_DERATED with reduced Iq_limit, and only use `over_temperature` (hard trip) for the actual hardware limit. This parallels the sensor_offset_drift strategy (warning before fault).

### F07: `passive_coast_timeout` (5s) May Be Insufficient for High-Inertia Loads

- **Severity**: LOW
- **Blocking**: No — application-dependent
- **Evidence path**: fault_recovery_model.md, Timing Constants table (line 369), PASSIVE_COAST section (line 105-106)
- **Claim**: The model assumes the motor stops within 5 seconds of passive coast. For a water pump with high inertia or in a vertical riser installation with backflow, coast time could exceed 5 seconds. If the timeout fires before speed reaches zero, the system transitions to FAULT_LATCHED while the motor is still spinning — this is safe (PWM is already disabled) but means the retry logic is never reached and the restart path is lost.
- **Correction**: Make `passive_coast_timeout` configurable via a system parameter (e.g., 5-15 seconds depending on pump inertia and installation). The 5s default is reasonable for horizontal installations but should be a tunable constant, not hardcoded.

### F08: `flying_restart_timeout` (3s) May Be Too Short for High-Speed Re-sync

- **Severity**: LOW
- **Blocking**: No — but affects recovery availability
- **Evidence path**: fault_recovery_model.md, Timing Constants table (line 370), FLYING_RESTART section (line 74-77)
- **Claim**: At 4000 rpm, the observer re-acquisition window is narrow because the speed is changing. The 3-second timeout for flying restart may not be enough if the observer needs multiple angle acquisition attempts. However, if the motor is spinning fast, the BEMF is strong and re-acquisition should be fast. The risk is at moderate speeds (1000-2000 rpm) where BEMF is moderate and the observer needs more time.
- **Correction**: Consider making `flying_restart_timeout` speed-dependent, or increase to 5 seconds. The current 3s is acceptable but conservative.

### F09: No Explicit Shutdown / Power-Down Sequence

- **Severity**: LOW
- **Blocking**: No — but a completeness gap
- **Evidence path**: fault_recovery_model.md, full document
- **Claim**: The model defines fault transitions and recovery but has no explicit "normal shutdown" path. When the user requests a stop (not emergency stop), the system should decelerate gracefully (CONTROLLED_DECEL) and then enter a defined idle state. Currently, `emergency_stop → FAULT_LATCHED` covers the safety case, but a controlled shutdown path (user disable → CONTROLLED_DECEL → speed_zero → PASSIVE_COAST → off) is not explicitly defined.
- **Correction**: Add a `user_disable` event that transitions to CONTROLLED_DECEL (distinct from `emergency_stop` which goes to FAULT_LATCHED). This allows normal shutdown without latching a fault.

### F10: APD Single-Phase `apd_1ph_coast_mode` Configuration Not Formalized

- **Severity**: LOW
- **Blocking**: No — the model mentions this but does not formalize it
- **Evidence path**: fault_recovery_model.md, APD Fault strategy (line 194)
- **Claim**: The model includes a water-hammer risk note suggesting `apd_1ph_coast_mode = {IMMEDIATE, CONTROLLED}` as a system-level config flag. This is a good idea but remains a suggestion rather than a formal part of the state machine. For implementation, this needs to be a defined configuration parameter with a default value and validation.
- **Correction**: Formalize `apd_1ph_coast_mode` as a required system configuration parameter in the model, with default = IMMEDIATE and documented behavior for both modes.

---

## Timing Constants Assessment

| Constant | Model Value | Assessment | Notes |
|----------|-------------|------------|-------|
| observer_detect | 5ms (50 samples @ 10kHz) | **Reasonable** | Fast enough for safety, 50 samples prevents false triggers |
| observer_extrapolate_max | 10-20ms | **Reasonable** | Corrected from 2s freeze; physically valid for extrapolated theta |
| observer_recovery_phase2 | 10-100ms | **Reasonable** | Gives observer time to relock without excessive delay |
| observer_total_timeout | 100ms | **Reasonable** | Aligns with extrapolate_max + recovery window |
| svpwm_sat_short | 50ms | **Reasonable** | Fast enough to prevent voltage collapse |
| svpwm_sat_long | 500ms | **Reasonable** | Distinguishes transient from persistent saturation |
| iq_clamp_derate | 2s | **Reasonable** | Appropriate for pump load thermal mass |
| iq_clamp_coast | 5s | **Reasonable** | Persistent clamp = unrecoverable, correct to coast |
| stall_detect | 3s | **Reasonable** | Matches pump inertia; shorter risks false stalls |
| vdc_recovery | Vdc > 270V for 1s | **Reasonable** | Hysteresis prevents chatter; 1s is conservative |
| restart_cooldown | 2s | **Reasonable** | Thermal protection between retries |
| passive_coast_timeout | 5s | **Marginal** | May be short for high-inertia pumps (see F07) |
| flying_restart_timeout | 3s | **Marginal** | Could be longer at moderate speeds (see F08) |
| precharge_timeout | 500ms | **Good** | 22uF charges in <100ms; 5x margin is correct |
| align_duration | 200ms | **Good** | Matches phase-b-004 spec; 1-2 electrical periods |
| if_ramp_duration | 300ms | **Good** | Matches phase-b-001/002 specification |
| observer_check_window | 100ms | **Good** | Consistent with phase-b-003 blend timing |

**Summary**: All timing constants are physically reasonable. Two (passive_coast_timeout, flying_restart_timeout) are marginal and should be configurable.

---

## Restart Logic Assessment

The restart logic is **correct in structure** but has one semantic ambiguity:

1. **Cold start path** (RESTART_PENDING → PRECHARGE → ALIGN → IF_RAMP → FOC): Correctly routes through the full startup sequence when motor is stopped. The PRECHARGE step is essential for the 22uF DC-link.

2. **Flying restart path** (RESTART_PENDING → FLYING_RESTART → FOC): Correctly handles the case where the motor is still spinning. The 3-retry limit with 2s cooldown is appropriate.

3. **Retry escalation**: The model defines 3 startup profiles (fallback_0.8A, nominal_1.0A, strong_1.2A). The escalation from weaker to stronger profiles on retry is correct — it attempts a gentler restart first.

4. **Off-by-one risk** (F04): The retry_count increment before the >= 3 check means only 2 retries may be executed instead of 3. This needs clarification.

5. **ALIGN timeout handling**: The ALIGN state transitions to RESTART_PENDING on timeout (200ms), and RESTART_PENDING increments retry_count. If ALIGN fails 3 times, the system correctly latches. This is correct.

---

## Safety Assessment

### Well-Covered Safety Paths

- Hardware trip-zone (OC, gate driver, PWM tripzone): Immediately disable PWM, latch fault. Correct.
- Emergency stop: Immediate PWM disable, latch fault. Correct.
- Watchdog reset: Latch fault. Correct for MCU lockup detection.
- Over-temperature: Immediate PWM disable, latch. Correct for hardware safety.
- ADC fault: Latch. Correct — bad ADC data is catastrophic for FOC.
- Vdc OV: Latch. Correct — overvoltage damages hardware.
- Vdc UVLO: Passive coast. Correct — motor must freewheel when power is lost.
- Observer extrapolation failure: Immediate passive coast. Correct — running FOC on bad angle is dangerous.
- Extrapolation at low speed: 5ms max bridge then coast. Correct — extrapolation is unreliable at low speed.

### Safety Gaps

1. **No thermal derating** (F06): Jump from normal to hard fault on temperature. Should have intermediate derating.
2. **No controlled shutdown path** (F09): User disable goes to FAULT_LATCHED, which is overly aggressive for normal shutdown.
3. **Missing current_sensor_fault in UNIVERSAL** (F01): Could leave FOC running blind in degraded states.
4. **Missing Vapd_ov** (F02): APD overvoltage not explicitly handled.

---

## Corrections

| ID | Finding | Priority | Effort | Recommendation |
|----|---------|----------|--------|----------------|
| C01 | Add `current_sensor_fault` to UNIVERSAL | HIGH | Low | Add one line to UNIVERSAL section |
| C02 | Add `vapd_ov` to UNIVERSAL or relevant states | MEDIUM | Low | Add one line to UNIVERSAL section |
| C03 | Define IF_RAMP, OBSERVER_CHECK, BLEND as states | MEDIUM | Medium | Add 3 rows to State Definitions + transitions |
| C04 | Clarify retry_count increment semantics | LOW | Low | Document whether first attempt counts as retry |
| C05 | Add speed-dependent extrapolation note | LOW | Low | Add one sentence to observer strategy |
| C06 | Add over_temp_warning derating before hard trip | MEDIUM | Medium | Add new event + FOC_DERATED transition |
| C07 | Make passive_coast_timeout configurable | LOW | Low | Change to parameter with default 5s |
| C08 | Consider increasing flying_restart_timeout | LOW | Low | Increase to 5s or make configurable |
| C09 | Add user_disable → CONTROLLED_DECEL path | LOW | Low | Add one transition to FOC_NORMAL |
| C10 | Formalize apd_1ph_coast_mode parameter | LOW | Low | Add to state machine config |

---

## Final Recommendation

**PASS_WITH_NOTES** at 82/100.

The Phase E-001 fault recovery model is a strong, well-structured document that correctly addresses the 8 required fault cases and covers the vast majority of hardware fault paths. The GPT corrections (extrapolated-theta bridge, coast state split, topology-aware APD, restart through startup sequence, fault classes) have been properly applied in v2.

**Before implementation, address these items:**

1. **Must fix** (HIGH priority): Add `current_sensor_fault` to the UNIVERSAL hard-fault section (C01). This is the only finding that could leave the system running blind in a degraded state.

2. **Should fix** (MEDIUM priority): Add `vapd_ov` hard-fault path (C02), define the missing startup states formally (C03), and add thermal derating before over-temperature hard trip (C06).

3. **Nice to have** (LOW priority): Clarify retry semantics (C04), make coast/restart timeouts configurable (C07, C08), add controlled shutdown path (C09).

The model is implementation-ready after addressing the HIGH and MEDIUM findings. The LOW findings are refinements that can be addressed during implementation or in a subsequent iteration.

**Alignment with project trajectory**: The model correctly integrates with the phase-b-004 startup state machine and the phase-c DC-link management. The fault codes (0-21) provide sufficient granularity for diagnostics. The 4 fault classes (hard_fault, recoverable, degraded, manual) enable correct retry behavior. The timing constants are consistent with the 10kHz PWM frequency and F28035 processing budget.
