# Motor Parameter Convention (Corrected)

## Resolved Parameters (from derivation-003)

| Parameter | Symbol | Value | Unit | Notes |
|-----------|--------|-------|------|-------|
| Pole pairs | p | 4 | — | 8 poles total |
| Stator resistance | Rs | 2.0 | Ω | |
| Stator inductance | Ls | 5.0 | mH | |
| Rotor flux linkage | ψ_f | 0.08 | Wb | Revised from 0.15 (derivation-003) |
| Rated current | I_rated | 3.0 | A | |
| Rated speed | N_rated | 4000 | rpm | |

## Derived Constants

| Constant | Formula | Value | Unit | Convention |
|----------|---------|-------|------|------------|
| ke (phase, per elec rad/s) | ψ_f | 0.08 | V/(rad/s elec) | Back-EMF = ω_e × ψ_f |
| Kt (torque constant) | 1.5 × p × ψ_f | 0.48 | Nm/A | T = Kt × Iq |
| ω_e at rated | p × 2π × N/60 | 1675.5 | rad/s elec | |
| Back-EMF at rated | ω_e × ψ_f | 134.0 | V phase peak | |

## Verification

At 4000rpm:
- ω_e = 4 × 2π × 4000/60 = 1675.5 rad/s
- E_bemf = 1675.5 × 0.08 = 134.0V (phase peak)
- Vlim at Vdc=300V: m_limit × Vdc/√3 = 0.9 × 300/1.732 = 155.9V
- 134.0V < 155.9V ✓ (motor can reach 4000rpm)

With ψ_f=0.15 (OLD, incorrect):
- E_bemf = 1675.5 × 0.15 = 251.3V > 155.9V ✗ (cannot reach 4000rpm)

## Impact on Phase B-001

The startup model used ke=0.15, which is wrong. Corrected values:

| Quantity | Old (ke=0.15) | Corrected (ψ_f=0.08) | Impact |
|----------|---------------|----------------------|--------|
| E_bemf at 30 rad/s mech | 4.5V | 9.6V | Observer sees 2× more signal |
| E_bemf at 4000rpm | 62.9V | 134.0V | 2× higher voltage requirement |
| Kt | 0.9 Nm/A | 0.48 Nm/A | 2× less torque per amp |
| T_rated at 3A | 2.7 Nm | 1.44 Nm | Below 3.0 Nm target |

**Note**: The rated torque with ψ_f=0.08 is 1.44 Nm, not 3.0 Nm. The "3.0 Nm" in task.md was from the old ψ_f=0.15. This needs reconciliation — either the motor is undersized for 300W at 4000rpm, or I_rated should be higher.

## Recommendation

Use ψ_f = 0.08 Wb consistently across all derivations. The motor may need:
- Higher I_rated (6A) for 300W at 4000rpm, OR
- Accept lower torque rating (1.44 Nm) and correspondingly lower power capability
