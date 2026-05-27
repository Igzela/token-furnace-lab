# Task: derivation-003 — Vreq(speed, torque) + Iq Limit + Voltage Saturation Envelope

## Goal

Connect the energy-based DC-link model (derivation-002) to actual FOC control constraints by deriving:

1. **Vreq(ω, iq, id)** — Motor voltage requirement as a function of speed and current
2. **Iq limit envelope** — Maximum q-axis current as a function of Vdc and speed
3. **Voltage saturation boundary** — Where SVPWM hits the Vdc limit

## Context

derivation-002 established:
- P_max = 2π·f_grid·C_dc·(Vnom² - Vreq²)
- Torque ripple is binding constraint (not voltage)
- 300W not achievable with 22µF + single-phase + mechanical inertia alone

GPT identified 4 missing checks in derivation-002:
1. Vnom = 237V is optimistic (real rectifier losses)
2. Vreq must be speed/torque dependent (not fixed)
3. High-line overvoltage check needed
4. Low-line current/thermal limits

## Deliverables

1. **Vreq(ω, iq, id) derivation**: back-EMF + Rs·Iq + L·dIq/dt + margin
2. **Iq_max(Vdc, ω) envelope**: Current limiting from voltage saturation
3. **Operating region map**: P_max_actual = min(P_max_voltage, P_max_torque, P_max_current)
4. **High-line overvoltage check**: Vmax at Vnom=354V vs component ratings
5. **Updated dc_link_constraints YAML**: With speed-dependent Vreq and Iq limits

## Model Assignment

- **Claude Code**: Derive Vreq function, Iq envelope, operating region
- **GPT**: Verify formulas, check numerical accuracy, identify edge cases
