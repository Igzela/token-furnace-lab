# derivation-006: Synthesis

## Score: 84/100 (PASS_WITH_NOTES)

**Rationale**: APD hardware sizing is realizable with standard components. 650V MOSFETs sufficient under Case A topology. Inductor 1.5-6.8mH range. Total APD loss ~3-6W (1-2%). GPT notes: 650V must be confirmed by actual schematic, 22µF preferred over 16µF for engineering baseline.

## Key Findings

### 1. APD Hardware Bill of Materials

| Component | Specification | Notes |
|-----------|--------------|-------|
| L_apd | 1.56mH nominal (1.5-6.8mH range) | ≥3A sat, ≥1A RMS |
| Capd | 22µF / 500V film | ≥1.5A RMS, low ESR |
| MOSFETs (×4) | 650V / 5A / Rds_on < 1Ω | Case A topology required |
| f_sw | 40kHz | Balance of L size vs DT error |
| Deadtime | 200-300ns | With compensation |
| APD control bw | ≥500Hz | Voltage loop |

### 2. Sweep Results

- 160 configs swept, 100 passed (62.5%)
- Best: L=1.56mH, f_sw=40kHz, MOSFET=650V, Loss=3.65W
- Failures: deadtime error >3% (60kHz), inductor too large (VL_max=300V)

### 3. GPT Notes

1. **650V MOSFET**: PASS_IF_CASE_A_CONFIRMED — needs actual schematic proof
2. **Deadtime error**: high fsw (60kHz) causes >3%, not low fsw
3. **APD loss**: 3.65W simulated, 3-6W engineering range, 1-2% efficiency penalty
4. **22µF preferred**: 16µF at -20% tolerance drops to 12.8µF
5. **Capacitance tolerance**: must be checked in sweep

## Decision Record

**APD hardware is realizable** with standard components.
- No showstopper found for APD implementation
- 650V MOSFET sufficient under Case A (unipolar switching)
- Engineering baseline: 22µF/500V APD, 3.3mH inductor, 650V MOSFETs
- Total APD loss ~3-6W (1-2% of 300W)
