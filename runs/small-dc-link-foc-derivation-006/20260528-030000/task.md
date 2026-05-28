# derivation-006: APD Hardware Sizing

## Goal

Size APD H-bridge hardware components: inductor, capacitor RMS current, MOSFET voltage/current rating, switching frequency, and first-order losses.

## Baseline (from derivation-005)

- Pavg: 300W
- Vdc_nom: 300V, Cdc: 22µF
- Capd: 22µF / 500V film (target), 16µF / 500V (optimization candidate)
- Vapd window: 250–450V
- Decoupling: 90–95%
- Motor speed: 3000–4000rpm

## Required Outputs

1. APD inductor sizing: L_apd vs fsw, ΔI_L, VL_max parameter sweep
2. Capacitor RMS current requirements
3. MOSFET voltage rating: Case A (max(Vdc,Vapd)) vs Case B (Vdc+Vapd)
4. MOSFET current rating with safety margins
5. MOSFET loss estimation (conduction + switching)
6. Deadtime requirements
7. APD control bandwidth requirements
8. Component parameter sweep (not single values)

## Key Formulas (from GPT)

- P_apd_peak = D × Pavg
- I_apd_peak ≈ P_apd_peak / Vapd_min
- I_apd_lf_rms ≈ P_apd_peak / (√2 × Vapd_center)
- L_apd ≥ VL_max / (2 × ΔI_L_pp × fsw)
- I_L_rms² ≈ I_lf_rms² + ΔI_L_pp² / 12
- I_L_peak ≈ I_lf_peak + ΔI_L_pp / 2
