# F-0001: Worker Gate Policy-Runtime Drift

Failure: `check_worker_gates` in `local_execution_worker.py` diverges from `local_marker_executor.check_gates`. Missing gates: LIVE_ENABLED, idempotency key, scope restriction, approval TTL, rollback plan, audit writability, marker existence check.

Impact: Critical. An operator setting LIVE_ENABLED=false would not stop the worker daemon. Tasks without idempotency keys or rollback plans could execute.

Root cause: Worker developed its own gate function instead of importing the canonical one. No conformance test existed to catch the divergence.

Recovery: Unify gate enforcement. Import `flags_from_env` and `check_gates` from `local_marker_executor`. Add deny-path tests for each missing gate.

Source: hermes-perm-audit-001, Codex risk reviewer grounded findings
