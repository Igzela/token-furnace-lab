# Policy-Runtime Drift

Observation: Documented safety model (13 live gates) diverged from actual worker implementation (check_worker_gates enforced only ~7 gates). This was the critical finding of hermes-perm-audit-001.

Rule candidate: Security-critical gate functions must have a conformance test that proves implementation matches documentation. Documentation alone is insufficient.

Evaluator: For any gate/checklist document, verify that a corresponding test exists that intentionally omits each gate and asserts denial. If tests don't exist, flag as drift risk.

Source: hermes-perm-audit-001, Codex risk reviewer confirmed GPT architect's inferred risk.
