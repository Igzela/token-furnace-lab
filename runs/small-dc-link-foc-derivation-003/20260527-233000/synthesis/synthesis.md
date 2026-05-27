# Synthesis — derivation-003: FOC Voltage Requirement and Saturation Envelope

## Metadata

- Experiment: small-dc-link-foc-derivation-003
- Models: Claude Code (derivation) + GPT (verification)
- Date: 2026-05-27
- Score: 82/100

## Verdict: PASS_WITH_NOTES

All formulas correct. One numerical error caught (Iq_max at 4000rpm/Vdc=216V). Key finding: 300W requires ≥6632rpm under 30% rated-torque ripple limit — far above rated speed.

## Model Agreement

| Aspect | Claude Code | GPT | Agreement |
|--------|-------------|-----|-----------|
| dq voltage equations | Derived | Verified correct | YES |
| SVPWM voltage limit | Vlim = m_limit·Vdc/√3 | Verified with assumption | YES |
| Iq_max quadratic | Derived | Verified | YES |
| ψ_f ≤ 0.103 boundary | Derived | Verified | YES |
| Iq_max at 4000rpm/Vdc=216V | 3.85A (WRONG) | INFEASIBLE (corrected) | GPT caught error |
| Max speed table | Derived | Verified | YES |
| Torque ripple: 300W needs ≥6632rpm | Derived | Verified | YES |
| High-line overvoltage: 240W safe | Derived | Verified | YES |

## Key Corrections Applied

1. **Iq_max at 4000rpm/Vdc=216V**: 3.85A → INFEASIBLE (back-EMF 134V > Vlim 124.7V)
2. **m_limit assumption**: Must be explicitly stated (used 0.90)
3. **Torque formula**: T = 1.5 × p × ψ_f × I_q (with three-phase factor)

## Critical Findings

### Finding 1: Maximum Speed Limited by Vdc
| Vdc (V) | Max Speed (rpm) |
|---------|-----------------|
| 216 | 3349 |
| 237 | 3670 |
| 300 | 4655 |

At Vdc=216V (300W energy minimum), motor cannot exceed 3349 rpm.

### Finding 2: 300W Requires ≥6632 rpm
Under 30% rated-torque ripple limit with mechanical absorption:
P_max = 0.432 × ω_m ≥ 300 → ω_m ≥ 694 rad/s → n ≥ 6632 rpm

This is 66% above rated speed (4000 rpm).

### Finding 3: Torque Ripple Always Binds
With ψ_f = 0.08 and mechanical absorption, torque ripple is always the binding constraint. Maximum power at 4000rpm: 181W.

### Finding 4: High-Line Overvoltage
At Vnom=354V (250Vac), 300W: Vmax = 410.8V > 400V capacitor rating.
Maximum safe power: 240W.

### Finding 5: Low-Line 4000rpm Infeasible
At Vdc=237V (168Vac), 4000rpm: Back-EMF > Vlim. Maximum speed: 3670 rpm.

## Solution Fork (GPT Recommended)

```yaml
solution_fork:
  A_keep_22uF:
    action: "must add APD or significantly derate"
  B_keep_300W:
    action: "increase DC-link capacitor or add active buffer"
  C_keep_no_APD:
    action: "accept high torque/speed ripple and acoustic risk"
  D_keep_400V_devices:
    action: "high-line power capped at 240W, or increase voltage rating"
```

## Score Breakdown

| Dimension | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Formula correctness | 30 | 28 | GPT verified all formulas |
| Numerical accuracy | 25 | 17 | Had to correct Iq_max error |
| Engineering insight | 25 | 22 | 6632rpm requirement is critical |
| Completeness | 20 | 15 | Missing field-weakening analysis |

**Total: 82/100 — PASS_WITH_NOTES**

## Next Steps

1. **Solution fork decision**: Choose path A/B/C/D before proceeding
2. **Phase A-002**: FOC implementation with corrected ψ_f = 0.08
3. **If APD path**: Derive APD sizing for 300W
4. **If larger capacitor**: Re-derive with C_dc = 100µF or 470µF
