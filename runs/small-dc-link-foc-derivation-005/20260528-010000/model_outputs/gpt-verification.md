# GPT Verification of derivation-005

## Verdict: NEEDS_MODEL_FIX

GPT reviewed the derivation-005 simulation results and identified multiple model bugs. The core conclusion ("16µF APD insufficient for 300W") is **not supported** — the analytical energy balance shows 16µF/250-450V should be sufficient.

## Key Corrections

### 1. APD Energy is Sufficient in Ideal Model

| Metric | Value |
|--------|-------|
| ΔE_required (90%) | 0.86J |
| ΔE_required (100%) | 0.955J |
| ΔE_available (16µF, 250-450V) | 1.12J |
| Verdict | energy_sufficient_in_ideal_model |

16µF is not large-margin but not insufficient. 22µF/500V recommended for practical margin.

### 2. Vdc Collapse is a Model Bug

Expected with 90% APD: Vdc ≈ 292-307V (14.5Vpp)
Simulation shows: Vdc ≈ 124-154V (21.5%pp)

This contradiction indicates model errors, not physical limitation.

### 3. Root Cause: Pmotor Uses Mechanical Power Instead of Electrical Power

The simulation calculates:
```
Pmotor = Te × ω = Kt × Iq × ω_mech
```

But for DC-link energy balance, the motor draws **electrical** power:
```
P_elec = Vq × Iq + Vd × Id ≈ (Rs × Iq + ωe × ψf) × Iq
```

At 300V, Iq=3A: P_elec ≈ 603W vs P_mech ≈ 302W. The simulation underloads the DC-link by ~300W, causing artificial Vdc collapse.

### 4. Back-EMF Calculation Error in Equilibrium Analysis

The derivation-005 equilibrium analysis used:
```
Vemf = ωe × ψf = 837.8 × 0.08 = 67V (correct for p=2)
```

GPT flagged that if p=4 were used: Vemf = 1675.5 × 0.08 = 134V, making Vdc=131V completely unworkable.

### 5. Missing Sanity Checks

Required checks that failed:
- mean(Pin) should equal Pavg ✓
- mean(Pmotor) should equal load power
- mean(Papd) should ≈ 0
- E_dc should not monotonic drift
- Vdc should stay above Vemf limit

## GPT's Recommended Fix Priority

1. Fix Pmotor to use electrical power (Vq×Iq + Vd×Id) in DC-link energy balance
2. Add sanity checks for average power balance
3. Rerun simulation
4. If 16µF still insufficient after fix, increase Capd to 22µF/500V
5. Keep Cdc = 22µF (do not increase main DC-link)

## Corrected Expected Results (GPT prediction)

With fixed model, 300W/22µF/16µF APD/90% decoupling:
- Vdc: 292.7-307.2V (14.5Vpp, 4.8%pp)
- Torque ripple: ~5% rated (not binding)
- APD voltage: 250-450V (within window)
