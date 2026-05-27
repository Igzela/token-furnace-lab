# Deny-Path Testing

Observation: A permission architecture should prove both allow and deny behavior. Documenting that live is disabled is not sufficient; runtime must reject when conditions are missing.

Rule candidate: Before enabling any execution path, implement deny-path tests for all required gates. Do not test successful execution first; prove denial works.

Evaluator: Count deny-path tests vs documented gates. If deny tests < documented gates, the deny surface is incomplete.

Source: hermes-perm-audit-001, GPT architect Risk 4 + Codex Finding 1 convergence.
