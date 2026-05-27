# Synthesis — derivation-004: APD Sizing for 300W/22µF Single-Phase Drive

## Metadata

- Experiment: small-dc-link-foc-derivation-004
- Models: Claude Code (derivation) + GPT (verification)
- Date: 2026-05-28
- Score: 78/100

## Verdict: PASS_WITH_TWO_CORRECTIONS

Direction correct. Two critical errors caught by GPT: capacitor formula missing factor of 2, and torque ripple conclusion wrong. After corrections, 300W is achievable with 90% APD decoupling.

## Model Agreement

| Aspect | Claude Code | GPT | Agreement |
|--------|-------------|-----|-----------|
| ΔE_peak = 0.477J | Derived | Verified | YES |
| ΔE_pp = 0.955J | Derived | Verified | YES |
| C_apd formula | Wrong (missing 2×) | Corrected | GPT caught error |
| C_apd values | 12µF (WRONG) | 19.6µF (corrected) | GPT caught error |
| Residual ripple | 19.6V / 6.5%pp | 14.5V / 4.8%pp | GPT corrected |
| Torque ripple with APD | "not solved" | "solved — 5% rated" | GPT caught error |
| APD topology | H-bridge | Verified correct | YES |
| APD peak power | 300W | Verified | YES |

## Key Corrections Applied

1. **APD capacitor formula**: Added factor of 2: C = 2·ΔE_pp/(Vmax²-Vmin²)
2. **APD capacitor values**: 12µF → 16µF (recommended design)
3. **Torque ripple conclusion**: APD DOES reduce motor-side torque ripple
4. **Residual DC-link ripple**: 19.6V → 14.5V (corrected formula)

## Critical Findings

### Finding 1: APD Solves Both Voltage and Torque Constraints
At 90% decoupling:
- DC-link residual: 4.8%pp (within SMO tolerance)
- Motor torque ripple: 5% rated (within 30% limit)
- **300W is achievable at 3000-4000rpm**

### Finding 2: APD Capacitor is Moderate Size
16µF/500V film capacitor — comparable to main DC-link (22µF)

### Finding 3: APD Power is Significant
270W peak at 100Hz — full power stage, not small auxiliary

### Finding 4: Remaining Constraints
- High-line overvoltage: 240W at 354V
- Low-line speed limit: 3670rpm at 237V

## Score Breakdown

| Dimension | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Formula correctness | 30 | 20 | C_apd formula had factor-of-2 error |
| Numerical accuracy | 25 | 17 | Capacitor values doubled after correction |
| Engineering insight | 25 | 22 | APD solving torque constraint is key finding |
| Completeness | 20 | 19 | Good coverage of topology, control, stress |

**Total: 78/100 — PASS_WITH_TWO_CORRECTIONS**

## Next Steps

1. **derivation-005**: Combined system simulation (FOC + APD + 22µF)
2. **Phase A-002**: FOC implementation on simulator (independent of APD)
3. **APD hardware sizing**: Select specific capacitor and switches
4. **Control implementation**: APD feedforward + voltage loop
