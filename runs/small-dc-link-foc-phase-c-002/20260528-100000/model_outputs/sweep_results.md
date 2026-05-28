# Phase C-002: Single-Phase vs Three-Phase Ripple Comparison

22µF DC-link, single-phase (100Hz) vs three-phase (300Hz) rectified input

## Pass Rate by Input Type and APD

| Input | K_apd | Cdc(µF) | Pass Rate |
|-------|-------|---------|-----------|
| single_phase | 0.0 | 22 | 5/16 (31%) |
| single_phase | 0.0 | 47 | 10/16 (62%) |
| single_phase | 0.0 | 100 | 14/16 (88%) |
| single_phase | 0.9 | 22 | 16/16 (100%) |
| single_phase | 0.9 | 47 | 16/16 (100%) |
| single_phase | 0.9 | 100 | 16/16 (100%) |
| single_phase | 0.95 | 22 | 16/16 (100%) |
| single_phase | 0.95 | 47 | 16/16 (100%) |
| single_phase | 0.95 | 100 | 16/16 (100%) |
| three_phase | 0.0 | 22 | 16/16 (100%) |
| three_phase | 0.0 | 47 | 16/16 (100%) |
| three_phase | 0.0 | 100 | 16/16 (100%) |
| three_phase | 0.9 | 22 | 16/16 (100%) |
| three_phase | 0.9 | 47 | 16/16 (100%) |
| three_phase | 0.9 | 100 | 16/16 (100%) |
| three_phase | 0.95 | 22 | 16/16 (100%) |
| three_phase | 0.95 | 47 | 16/16 (100%) |
| three_phase | 0.95 | 100 | 16/16 (100%) |

## Total: 269/288 passed (93.4%)

## Best Configs (Lowest Ripple, Pass)

| Input | Cdc(µF) | K_apd | T_load | ω_ref | Ripple(%) | Vdc_min(V) |
|-------|---------|-------|--------|-------|-----------|------------|
| single_phase | 47.0 | 0.95 | 0.1 | 200 | 0.0 | 300.0 |
| single_phase | 100.0 | 0.9 | 0.1 | 200 | 0.0 | 300.0 |
| single_phase | 100.0 | 0.95 | 0.1 | 200 | 0.0 | 300.0 |
| three_phase | 22.0 | 0.9 | 0.1 | 200 | 0.0 | 300.0 |
| three_phase | 22.0 | 0.95 | 0.1 | 100 | 0.0 | 300.0 |
| three_phase | 22.0 | 0.95 | 0.1 | 200 | 0.0 | 300.0 |
| three_phase | 47.0 | 0.9 | 0.1 | 100 | 0.0 | 300.0 |
| three_phase | 47.0 | 0.9 | 0.1 | 200 | 0.0 | 300.0 |
| three_phase | 47.0 | 0.95 | 0.1 | 100 | 0.0 | 300.0 |
| three_phase | 47.0 | 0.95 | 0.1 | 200 | 0.0 | 300.0 |
| three_phase | 100.0 | 0.9 | 0.1 | 100 | 0.0 | 300.0 |
| three_phase | 100.0 | 0.9 | 0.1 | 200 | 0.0 | 300.0 |
| three_phase | 100.0 | 0.95 | 0.1 | 100 | 0.0 | 300.0 |
| three_phase | 100.0 | 0.95 | 0.1 | 200 | 0.0 | 300.0 |
| single_phase | 22.0 | 0.95 | 0.1 | 200 | 0.01 | 300.0 |

## 22µF Medium Load Comparison (T=0.5, ω=200)

| Input | K_apd | Ripple(%) | Vdc_min(V) | Pass |
|-------|-------|-----------|------------|------|
| single_phase | 0.0 | 11.24 | 268.1 | FAIL |
| single_phase | 0.9 | 1.02 | 297.0 | PASS |
| single_phase | 0.95 | 0.51 | 298.5 | PASS |
| three_phase | 0.0 | 1.12 | 296.7 | PASS |
| three_phase | 0.9 | 0.11 | 299.7 | PASS |
| three_phase | 0.95 | 0.06 | 299.8 | PASS |