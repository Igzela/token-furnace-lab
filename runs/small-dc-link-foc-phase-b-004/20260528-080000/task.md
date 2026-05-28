# Phase B-004: Startup State Machine Implementation Spec

## Goal

Translate Phase B-003's validated three-threshold blend into a TMS320F28035 C implementation spec with deterministic state transitions, dwell counters, fallback profiles, and trace logging.

## GPT Requirements (from B-003 review)

1. **Exact state transitions** — define in spec, don't let implementation infer from comments
2. **Deterministic α rollback** — specific rollback_step or freeze
3. **Dwell counters** — observer_detect_counter, blend_valid_counter, handover_valid_counter, observer_invalid_counter
4. **Fallback startup profiles** — nominal(0.5A), fallback(0.8A), strong-start(1.0A)
5. **Trace logging** — theta_ramp, theta_obs, theta_blend, theta_err, alpha, omega_ref, omega_est, iq_ref, iq_meas, vdc, vapd, svpwm_saturated, observer_valid, state, fault_code

## Implementation Constraints

- TMS320F28035: 12.5MHz SYSCLK, fixed-point (q15_t, q12_t, angle_t)
- ISR rate: 10kHz (100µs period)
- PWM: 40kHz (symmetric)
- Memory: 128KB flash, 20KB RAM
- Timer: 32-bit, 150MHz (for timestamps)

## Required Outputs

1. State machine spec (state transitions, guards, dwell counters)
2. Fallback profile definitions
3. Trace buffer format and DMA logging strategy
4. C header with all constants and types
5. GPT review
