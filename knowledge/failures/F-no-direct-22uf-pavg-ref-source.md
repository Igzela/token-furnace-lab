---
id: F-no-direct-22uf-pavg-ref-source
name: "No Direct 22µF DC-Link or Pavg_ref Source in Seed Corpus"
severity: High
source_experiment: pdf-to-algorithm-benchmark-002
created: 2026-05-27
status: open
---

## Observation

The 3 arXiv seed papers (A1/A2/A3) do not provide:
1. Pavg_ref (average power reference) calculation method
2. 22µF DC-link voltage ripple model
3. Sensorless FOC behavior under large DC-link voltage ripple

## Rule Candidate

When building a technical roadmap from literature, verify that critical system-specific constraints (capacitance, power reference, ripple model) are either directly available or flagged for custom derivation.

## Evaluator

Check if the source corpus covers all system-level parameters before declaring the roadmap complete.

## Impact

Without Pavg_ref and 22µF ripple model, the DC-link management layer (Phase C) cannot be implemented from literature alone. Custom mathematical derivation is required.

## Mitigation

1. Derive Pavg_ref from power balance equations
2. Model 22µF DC-link ripple analytically
3. Assess sensorless FOC robustness under large ripple
4. Consider A3's harmonic observer as conceptual reference only

## Cross-References

- Wiki: small-dc-link-foc-technical-route
- Experiment: pdf-to-algorithm-benchmark-002
- Next: small-dc-link-foc-model-derivation-001
