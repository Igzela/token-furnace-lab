# Phase C-002: Single-Phase vs Three-Phase Ripple Comparison

## Goal

Compare 22µF DC-link feasibility under single-phase and three-phase rectified input, as GPT recommended benchmark.

## Cases to Simulate

1. Single-phase 50Hz, no APD
2. Single-phase 50Hz, 90% APD
3. Single-phase 50Hz, 95% APD
4. Three-phase 50Hz, no APD
5. Three-phase 50Hz, 90% APD

## Key Difference

- Single-phase: 100Hz ripple (2×50Hz)
- Three-phase: 300Hz ripple (6×50Hz, six-pulse rectification)
- Three-phase ripple amplitude is ~1/3 of single-phase for same power

## Required Outputs

1. Vdc ripple map across load/speed
2. Medium-load pass/fail comparison
3. APD requirement vs load for each input type
4. Minimum Cdc for each input type
5. GPT review
