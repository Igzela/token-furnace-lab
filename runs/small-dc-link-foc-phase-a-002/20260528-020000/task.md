# Phase A-002: FOC Interface Design

## Goal

Define formal C header interfaces for all FOC modules on TMS320F28035. Interface design only — no implementation.

## Scope

Based on Phase A-001 module specs, create:
1. Fixed-point type definitions (Q-format shared types)
2. Per-module input/output struct definitions
3. ISR entry point signatures and data flow contracts
4. Module initialization interfaces
5. Vdc feedforward normalization interface
6. Observer output interface (theta_est, omega_est)

## Exclusions

- No APD interfaces (Phase C)
- No startup/I-f interfaces (Phase B)
- No 22µF ripple handling (Phase C)
- No actual implementation code

## Acceptance Criteria

- [ ] All 7 FOC modules have C struct definitions for I/O
- [ ] Fixed-point types consistently used (Q15, Q12, Q12-acc)
- [ ] ISR signature matches 10kHz current loop rate
- [ ] Data flow matches A-001 signal flow diagram
- [ ] Struct sizes match RAM budget (~1.6KB total)
