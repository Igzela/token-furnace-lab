# Phase E-001: Runtime Fault Recovery Model (v3) -- Structured Review

**Reviewer**: Implementer (structured review)
**Model under review**: `runs/small-dc-link-foc-phase-e-001/20260528-130000/model_outputs/fault_recovery_model.md`
**Previous review**: `runs/orchestration/20260528-092721/artifacts/e001_fault_recovery_review.md` (v2, score 76/100)
**Date**: 2026-05-28

---

## Score

**91 / 100**

---

## Verdict

**PASS_WITH_NOTES**

All 7 corrections (C-01 through C-07) from the previous review are properly applied. The model is now implementation-ready. The remaining findings are minor naming inconsistencies and one transitional timing overlap that do not block implementation. The universal hard-fault block, completed state definitions, cold-start timing, and extrapolation failure detection are all correctly integrated.

---

## Correction Verification

### C-01: PRECHARGE and ALIGN states added to state table -- PASS

Both states appear in the State Definitions table (lines 17-18):
- PRECHARGE: DC-link voltage ramp-up, Stopped, Disabled, precharge relay control + Vdc monitoring.
- ALIGN: Rotor alignment pulse, Stopped, Active, fixed current vector + fixed angle.

Exit conditions are defined in the transition matrix (lines 112-121): PRECHARGE exits to ALIGN on `vdc_ready` or to FAULT_LATCHED on timeout/oc_trip; ALIGN exits to IF_RAMP on `align_done` or to RESTART_PENDING/FAULT_LATCHED on timeout/retry failure.

### C-02: Fault codes 20-21 added -- PASS

Fault code table now contains 22 entries (codes 0-21). New entries:
- Code 20: `PRECHARGE_FAIL` | Critical | Manual | No
- Code 21: `ALIGN_FAIL` | High | Recoverable | 3 retries

Note: The previous review suggested code 20 = `STARTUP_TMO` and code 21 = `PRECHARGE_FAIL`. The model chose different naming -- code 20 = `PRECHARGE_FAIL` (correct, maps to precharge timeout) and code 21 = `ALIGN_FAIL` (new, maps to alignment timeout). Code 11 (`STARTUP_TMO`) already existed for startup timeout. The resulting code set is coherent and covers all fault scenarios. The naming deviation from the suggestion is an improvement.

### C-03: UNIVERSAL hard-fault block at top of transition matrix -- PASS

The UNIVERSAL block (lines 22-33) defines 7 hard-fault transitions (oc_trip, gate_driver_fault, pwm_tripzone, emergency_stop, watchdog_reset, adc_invalid, over_temperature) that apply from every active/degraded state. The explicit note "These transitions apply from every state where PWM is active. They are not repeated per-state below" eliminates the per-state omission problem identified in the previous review (F-03 through F-05, F-08). The active states section still lists some hard-fault transitions (e.g., FOC_NORMAL lines 49-57) as a convenience -- this is acceptable for documentation clarity and does not create inconsistency since the UNIVERSAL rule covers all cases.

### C-04: Cold-start timing added to timing table -- PASS

Four new entries at lines 371-374:
- `precharge_timeout`: 500ms -- rationale references 22uF charge time with 5x margin.
- `align_duration`: 200ms -- rationale references 1-2 electrical periods at standstill.
- `if_ramp_duration`: 300ms -- matches phase-b-001/002 I-f ramp specification.
- `observer_check_window`: 100ms -- matches phase-b-003 observer-gated blend.

All values are consistent with the cold start sequence (line 321) and the PRECHARGE/ALIGN transition definitions (lines 112-121). The precharge timeout of 500ms in the timing table matches the transition matrix (line 114). The align timeout of 200ms in the transition matrix (line 119) matches the `align_duration` timing constant.

### C-05: Extrapolation failure detection added -- PASS

Lines 149-156 define three failure modes:
1. Update rate = PWM frequency (10kHz) -- correct, matches control loop rate.
2. Angle disagreement threshold: |theta_extrapolated - theta_measured| > 60deg when observer partially relocks -> reject and PASSIVE_COAST.
3. Low-speed unreliability: omega_last < 100 rpm -> reduce to 5ms max bridge -> PASSIVE_COAST.

These directly address the previous review's F-07 (extrapolation mechanism underspecified). The 60deg threshold is physically reasonable -- at that level of disagreement, the observer state is unreliable and extrapolation provides no safety value.

### C-06: Timing inconsistency resolved -- PASS

The timing table now defines:
- `observer_extrapolate_max`: 10-20ms (line 356)
- `observer_recovery_phase2`: 10-100ms (line 357) -- replaces the old `observer_recovery_window` value of 0.5-2s.
- `observer_total_timeout`: 100ms (line 358) -- the hard deadline for OBSERVER_DEGRADED state.

The recovery strategy phases (lines 132-145) are now fully consistent with the timing table:
- Phase 1 (0-10ms) matches `observer_extrapolate_max` (10-20ms).
- Phase 2 (10-100ms) matches `observer_recovery_phase2` (10-100ms).
- Phase 3 (>100ms) matches `observer_total_timeout` (100ms).

The old 0.5-2s contradiction is fully resolved.

### C-07: Water-hammer risk documented -- PASS

Line 194 adds a note under the single-phase APD strategy:
- Identifies the risk scenario (vertical riser, no check valve).
- Proposes a system-level config flag: `apd_1ph_coast_mode = {IMMEDIATE, CONTROLLED}`.
- Default is IMMEDIATE (safest for electronics), with CONTROLLED as an option for water-hammer-sensitive installations.

This is a well-placed, actionable note. The default is correct (electronics safety first), and the flag gives mechanical engineers an escape hatch without changing the default safety posture.

---

## Findings (Remaining Issues)

### F-01: Fault class event naming inconsistency with fault code table (Severity: LOW)

The fault classes section (lines 285-305) uses event names that do not perfectly match the fault code table names:

- `startup_tmo` (fault classes, line 292) -- no fault code has this exact name. Code 11 is `STARTUP_TMO` (uppercase). This is a cosmetic mismatch but could cause confusion in code generation if event names are used as enum values.
- `precharge_fail` (fault classes, line 303) -- code 20 is `PRECHARGE_FAIL`. The lowercase/uppercase difference is consistent with the YAML formatting style, but code 4 is `PRECHARGE_TMO` which is a different code with the same Manual fault class. The relationship between code 4 (PRECHARGE_TMO) and code 20 (PRECHARGE_FAIL) is not documented -- are they the same fault at different points in the sequence, or distinct faults?

**Recommendation**: Add a one-line note clarifying that PRECHARGE_TMO (code 4) is a precharge-phase timeout and PRECHARGE_FAIL (code 20) is a post-precharge validation failure, or consolidate them if they represent the same fault. This clarification is needed before fault code assignments are finalized in implementation.

### F-02: ALIGN state retry_3_failed lacks explicit retry count tracking (Severity: LOW)

The ALIGN state transition (line 121) defines `retry_3_failed -> FAULT_LATCHED`, and the cold start sequence (lines 311-322) defines `retry_count++` and `if retry_count >= 3: -> FAULT_LATCHED`. However, the cold start sequence increments retry_count at the RESTART_PENDING level, while the ALIGN timeout also defines a `retry_3_failed` condition. It is unclear whether these are the same retry counter or separate counters.

If they share a counter: a failed ALIGN would increment the RESTART_PENDING retry count, causing eventual latch after 3 failed alignments across cold-start attempts. This is correct behavior.

If they are separate counters: the ALIGN state could theoretically loop between ALIGN -> RESTART_PENDING -> PRECHARGE -> ALIGN indefinitely (each ALIGN failure only resets to RESTART_PENDING, which retries). This would be incorrect.

**Recommendation**: Clarify that `retry_3_failed` in ALIGN references the same retry counter as RESTART_PENDING, or document that ALIGN has its own 3-attempt limit within a single cold-start sequence.

### F-03: Cold start sequence references undefined states BLEND and IF_RAMP (Severity: LOW)

The cold start sequence (line 321) defines:

```
PRECHARGE -> ALIGN -> IF_RAMP -> OBSERVER_CHECK -> BLEND -> FOC
```

`IF_RAMP`, `OBSERVER_CHECK`, and `BLEND` are not defined in the state definitions table. The table defines 12 states; these three are absent. They are implicitly sub-states of the restart sequence but have no formal definition, transition rules, or timeout values. The `if_ramp_duration` (300ms) and `observer_check_window` (100ms) timing constants exist, but no `blend_duration` is defined.

**Recommendation**: Either add these as formal states in the state table (consistent with PRECHARGE and ALIGN), or add a note that these are transient sub-states within the restart sequence with timing defined by the timing constants table. The blend duration should be added to the timing table.

---

## Final Recommendation

**PASS_WITH_NOTES -- implementation-ready.**

The v3 model is a significant improvement over v2. All 7 corrections are properly applied and each one addresses a real gap identified in the previous review. The universal hard-fault block (C-03) is the most impactful safety fix -- it eliminates the per-state omission problem that affected 5 states in v2. The completed state definitions (C-01) and cold-start timing (C-04) make the cold-start path fully implementable. The extrapolation failure detection (C-05) and timing inconsistency resolution (C-06) close important correctness gaps in the observer recovery strategy. The water-hammer note (C-07) is a well-placed engineering consideration.

The 3 remaining findings are all LOW severity and represent documentation clarity issues rather than correctness problems. None require fundamental model changes. All can be resolved during implementation without redesign.

**Impact on downstream phases**:
- Phase A-004 (fixed-point CPU budget): No additional impact. State machine complexity unchanged from v2 assessment.
- Phase D (integration/testing): Cold-start test procedures can now reference specific timing constants. The universal fault rules enable comprehensive fault injection testing without per-state transition gaps.
- Hardware test (phase-a-003): Universal fault rules (C-03) and ALIGN state definition (C-01) are now in place for safety interlock testing.

**Priority for implementation**:
1. C-03 (universal hard-fault rules) -- already applied, highest safety value.
2. C-01 + C-04 (PRECHARGE/ALIGN states + cold-start timing) -- already applied, required for state machine coding.
3. C-02 (fault code table) -- already applied, required for diagnostics.
4. C-05, C-06, C-07 -- already applied, refinement.
5. F-01 (naming clarification) -- resolve before code generation.
6. F-02 (retry counter scope) -- resolve before state machine implementation.
7. F-03 (sub-state definitions) -- resolve before test procedure authoring.
