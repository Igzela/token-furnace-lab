# Task: derivation-005 — FOC + APD + 22µF Joint Dynamic Simulation Model

## Goal

Verify coupled behavior of DC-link energy, APD energy buffer, FOC voltage saturation, current limit, torque ripple, and protection boundaries through low-order dynamic simulation.

## Why First (Before Phase A-002 Implementation)

GPT: "你现在的关键风险已经不是单个公式，而是 APD、DC-Link、FOC、SMO、限流、过压/欠压保护之间的动态耦合。如果不先做联合仿真，你很可能把 Phase A 的 FOC 实现写成'稳定母线 FOC'，后面接 APD 时再返工。"

## Simulation Model Components

1. Single-phase input: Pin(t) = Pavg · [1 - cos(2ωt)]
2. Main DC-Link: dE_dc/dt = Pin - Pmotor - Papd, E_dc = 0.5 Cdc Vdc²
3. APD capacitor: dE_apd/dt = Papd - Ploss_apd, E_apd = 0.5 Capd Vapd²
4. APD power command: Papd_ref = D_apd · Pavg · cos(2ωt)
5. PMSM FOC voltage limit: sqrt(Vd² + Vq²) ≤ m_limit · Vdc / √3
6. Iq limit: Iq_cmd ≤ min(I_rated, Iq_voltage_max(Vdc, ω))
7. Mechanical side: J dω/dt = Te - TL, TL = kω²

## Sweep Parameters

| Parameter | Values |
|-----------|--------|
| Pavg | 100 / 200 / 300W |
| Vnom | 237 / 300 / 354V |
| Capd | 12 / 16 / 22µF |
| Vapd window | 250-400 / 250-430 / 200-450V |
| APD decoupling | 80 / 90 / 95% |
| Speed | 3000 / 4000rpm |

## Pass Criteria

1. Vdc ripple < 10%pp (or at least < 15%pp)
2. Torque ripple < 30% rated torque
3. No voltage saturation at target speed
4. Vmax < 400V if using 400V-rated bus components
5. Vapd stays within capacitor/device rating
6. APD current within device and inductor limit

## Deliverables

1. Simulation model (Python/Matlab)
2. Parameter sweep results table
3. Operating region map with all constraints
4. Updated dc_link_constraints YAML
5. Go/no-go recommendation for 300W/22µF/APD system

## Model Assignment

- **Claude Code**: Build simulation model, run sweeps, generate results
- **GPT**: Verify model setup, check results, identify edge cases
