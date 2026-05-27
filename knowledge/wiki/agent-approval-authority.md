# Agent Approval Authority

Observation: ChatGPT is explicitly disallowed from being the final approver for local execution. Human (Charlie) must provide local CLI/UI/physical approval.

Rule candidate: Remote or browser-mediated model approval is insufficient for local execution authority. Final approval must come through a local channel that the execution environment can verify.

Evaluator: Check that approval source is validated at runtime, not just documented. Verify that ChatGPT-only approval is rejected.

Source: hermes-perm-audit-001, all 3 models converged on this point.
