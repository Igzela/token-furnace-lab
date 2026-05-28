# Status: derivation-006

## Phase: COMPLETE

### Results
- Score: 84/100 (PASS_WITH_NOTES)
- Sweep: 160 configs, 100 passed (62.5%)
- Best: L=1.56mH, fsw=40kHz, 650V MOSFET, 3.65W (1.22%)

### Key Decisions
- 650V MOSFET sufficient under Case A topology (unipolar switching)
- 22uF/500V film capacitor preferred over 16uF (tolerance margin)
- 1.5-6.8mH inductor range, 3.3mH recommended baseline
- Deadtime 200-300ns with compensation
- APD control bandwidth >=500Hz

### GPT Notes
1. 650V: PASS_IF_CASE_A_CONFIRMED — verify from schematic
2. Deadtime: high fsw (60kHz) causes >3% error, not low fsw
3. APD loss: 3.65W simulated, 3-6W engineering range
4. 22uF preferred: 16uF at -20% tolerance drops to 12.8uF
5. Capacitance tolerance must be checked in sweep
