# derivation-005: Synthesis

> Handoff note (2026-05-28): this model-output synthesis is under review, not an accepted design decision. Use `status.md` and `synthesis/synthesis.md` as the authoritative run status until final verification reconciles the corrected model with GPT's `NEEDS_MODEL_FIX` review.

## Score: 72/100 (NEEDS_REVIEW)

**Rationale**: Model corrections applied (electrical power, quadratic Iq, APD energy center) produce correct results for ideal case. However, the 90% APD case still fails due to clamping asymmetry — a real physical effect that GPT may dispute. Awaiting GPT's final verification.

## Key Findings

### 1. Model Corrections (Applied)
- **Electrical power**: Pmotor = 1.5 × Vq × Iq (3-phase, includes copper losses)
- **Iq from power command**: Quadratic solution of Pavg = 1.5 × (Rs×Iq + ωe×ψf) × Iq
- **APD energy center**: Vapd_center = √((Vmin² + Vmax²) / 2) instead of voltage midpoint

### 2. Ideal APD Verification ✓
- D=1.0, unlimited window → Vdc=300V, 0%pp ripple
- Pmotor = 300.0W exact match to Pavg
- Model is correct for ideal case

### 3. 300W Infeasible with Practical APD
- 0/162 300W configs pass
- Root cause: APD voltage window clamping asymmetry
  - Absorption: APD hits Vapd_max, excess → DC-link
  - Release: APD from lower energy, can't release full power
  - Net: APD +4.7W average (should be ~0), DC-link -1.9W → Vdc collapses

### 4. 100W Achievable
- 62/324 100W configs pass
- Lower power reduces clamping severity

### 5. 470µF Works Without APD
- Vdc ripple 3.2%pp, no APD needed

## Decision Record

**Solution fork revision**: Path A (22µF + APD) works for ≤100W but not 300W. Options:
1. Accept 100W target
2. Increase Cdc to ≥470µF for 300W
3. Wider APD voltage or larger Capd for 300W (needs further study)

## Next Steps
- Await GPT verification of clamping asymmetry analysis
- Based on GPT feedback, decide solution path
- Commit all derivation-005 files
