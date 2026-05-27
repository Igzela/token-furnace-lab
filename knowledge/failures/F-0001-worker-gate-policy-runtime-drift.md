# F-0001: Worker Gate Policy-Runtime Drift

Failure: `check_worker_gates` in `local_execution_worker.py` uses independent gate logic instead of importing `local_marker_executor.check_gates`. The risk is not absence of LIVE_ENABLED in the canonical gate; the risk is duplicated gate logic and worker-path divergence.

Refined from "missing LIVE_ENABLED globally" to "duplicated worker gate diverges from canonical marker executor gate."

Divergent cases (6/25):
- D001: LIVE_ENABLED missing - marker denies, worker allows
- D002: LIVE_ENABLED=false - marker denies, worker allows
- D003: live scope not enabled - marker denies, worker allows
- D010: idempotency key missing - marker denies, worker allows
- D012: idempotency key mismatch - marker denies, worker allows

Conformant cases (19/25): D004-D009, D011, D013-D025 pass on both paths.

Impact: Critical. An operator setting LIVE_ENABLED=false would not stop the worker daemon. Tasks without idempotency keys could execute via the worker path.

Root cause: Worker developed its own gate function instead of importing the canonical one. No conformance test existed to catch the divergence.

Recovery: Make worker_daemon use the same canonical gate logic as marker_executor, or prove behavioral equivalence through shared tests.

Source: hermes-perm-audit-001 (Codex), hermes-perm-audit-002 (gate conformance matrix)
