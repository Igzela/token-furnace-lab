# Synthesis — derivation-002: 22µF DC-Link Energy Balance Envelope

## Metadata

- Experiment: small-dc-link-foc-derivation-002
- Models: Claude Code (derivation) + GPT (verification)
- Date: 2026-05-27
- Score: 85/100

## Verdict: PASS_WITH_NOTES

Energy balance formula is correct. Numerical error in voltage envelope was caught and corrected. Critical findings: torque ripple is the binding constraint (not voltage), 300W not achievable with mechanical inertia alone, low-line derating required.

## Model Agreement

| Aspect | Claude Code | GPT | Agreement |
|--------|-------------|-----|-----------|
| Formula P_max = 2πfC(Vnom²-Vreq²) | Derived | Verified correct | YES |
| Vdc envelope at 300W/300V | 173-415V (WRONG) | 216-365V (corrected) | GPT caught error |
| Low-line feasibility | Not analyzed | 300W NOT feasible at 168Vac | GPT added |
| Mechanical inertia absorption | Speed ripple 0.48% OK | Torque ripple ≈ average torque | GPT found hidden cost |
| Torque ripple cost | Not analyzed | 100% modulation at full power | GPT added |

## Key Corrections Applied

1. **Voltage envelope**: 173-415V → 216-365V (GPT caught numerical error)
2. **Low-line analysis**: Added 168Vac derating table (GPT contribution)
3. **Pmax vs Vnom vs Vreq table**: Added 3×3 lookup table (GPT request)
4. **Speed ripple vs inertia table**: Added J×speed×power lookup table (GPT request)
5. **Torque ripple cost**: Documented 100% modulation at full power (GPT finding)
6. **Operating region**: Updated to show torque ripple is binding constraint

## Critical Findings

### Finding 1: Torque Ripple is Binding (NOT Voltage)
- Voltage allows 383W at 3000rpm (Vnom=237V)
- Torque ripple constraint (T_ripple/T_avg < 30%) limits to 170W
- **300W NOT achievable with mechanical inertia absorption alone**

### Finding 2: Low-Line Derating Required
- At 168Vac (237Vdc): 300W feasible only below ~2500rpm
- At 4000rpm low-line: Pmax = 107W (derate from 300W)
- At 3000rpm low-line: Pmax = 383W (marginal)

### Finding 3: Three-Phase Input is Strongest Lever
- Reduces 100Hz energy swing by ~3x
- Makes 22µF much more practical for 300W
- Should be confirmed before proceeding

## Corrected dc_link_constraints

```yaml
dc_link_constraints:
  Pout_avg_max_by_speed:
    1000rpm: 57W
    2000rpm: 113W
    3000rpm: 170W
    4000rpm: 107W
  note: "300W NOT achievable with mechanical inertia absorption alone"
```

## Score Breakdown

| Dimension | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Formula correctness | 30 | 28 | GPT verified formula, caught numerical error |
| Numerical accuracy | 25 | 18 | Had to correct voltage envelope |
| Engineering insight | 25 | 22 | Torque ripple finding is critical |
| Completeness | 20 | 17 | Added lookup tables per GPT request |

**Total: 85/100 — PASS_WITH_NOTES**

## Next Steps

1. **Confirm input topology**: Single-phase or three-phase? (GPT: "单相输入100Hz功率缺口到底由谁吸收？")
2. **If single-phase**: APD or larger capacitance required for 300W
3. **If three-phase**: Re-derive with 3× reduced energy swing
4. **Proceed with Phase A FOC baseline**: Independent of 22µF
