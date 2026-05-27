# Codex Risk Reviewer Output

Experiment: hermes-perm-audit-001
Target: hermes-gateway-lab
Basis: direct code inspection of 12 files

---

## High-risk findings

**1. Worker bypasses global kill switch (LIVE_ENABLED)**
- **File**: `scripts/local_execution_worker.py`, lines 113-193 (`check_worker_gates`)
- **Classification**: Grounded
- **Severity**: High
- **Description**: `check_worker_gates` never reads `LIVE_ENABLED` or `LOCAL_MARKER_LIVE_ENABLED` environment variables. By contrast, `local_marker_executor.check_gates` (lines 361-363) properly blocks execution when either flag is false. The worker path has its own independent gate function that omits the global kill switch entirely. An operator who sets `LIVE_ENABLED=false` to halt all live execution will not stop the worker daemon if an arm gate is present.
- **Evidence**: `local_execution_worker.py` never imports `LiveFlags` or `flags_from_env` from `local_marker_executor`. The `check_worker_gates` function constructs its own `gates` dict without any flag fields.

**2. Worker does not check if marker file already exists (double-write on crash recovery)**
- **File**: `scripts/local_execution_worker.py`, lines 276-296, 306-312
- **Classification**: Grounded
- **Severity**: High
- **Description**: If the worker process crashes between the marker file write (line 296) and the request state save (line 312), on restart the arm gate is still unconsumed, the request is still in state `ready_for_local_execution`, and `check_worker_gates` has no check for marker file existence. The worker will overwrite the marker with a new `live_execution_id`, producing two audit trail entries for the same task. The `local_marker_executor.check_gates` function properly blocks this at line 359: `if path.exists(): _block(...)`.
- **Evidence**: Compare `local_execution_worker.py` lines 146-147 (hardcoded `"marker_path_under_tmp_live_execution_markers": True`) with `local_marker_executor.py` lines 359-360 (actual existence check).

**3. Worker omits idempotency key validation**
- **File**: `scripts/local_execution_worker.py`, lines 113-193
- **Classification**: Grounded
- **Severity**: High
- **Description**: `check_worker_gates` records the idempotency key in the `gates` dict (indirectly, via the task) but never validates its presence or correctness. The `local_marker_executor.check_gates` function validates this at line 351-352. Without this check, a task that lost its idempotency key due to corruption could still be executed.

**4. Worker does not enforce task scope restriction**
- **File**: `scripts/local_execution_worker.py`, lines 113-193
- **Classification**: Grounded
- **Severity**: High
- **Description**: `check_worker_gates` never checks `task.get("requested_scope")` against an allowlist. The gates doc (`live-execution-gates.md` line 30) lists "task scope is allowed" as a required check. The dry_run_executor validates scope at line 113-114 (`ALLOWED_SCOPE = "hermes.plan"`), but the worker does not re-validate it. If a task's scope field were mutated in the queue after dry-run, the worker would not catch it.

**5. Worker does not check approval timestamp TTL**
- **File**: `scripts/local_execution_worker.py`, lines 113-193
- **Classification**: Grounded
- **Severity**: High
- **Description**: The worker checks arm gate expiry (lines 175-176) but never checks the task's `approval_timestamp` against any TTL. The gates doc (`live-execution-gates.md` line 29) requires "approval timestamp is within TTL". An approval from weeks ago could be executed as long as a fresh arm gate is created. There is no TTL enforcement anywhere in the codebase -- `approve_task` in `approval_queue.py` (line 238) stores `approval_timestamp` but no `expires_at`.

**6. Worker does not check rollback plan existence**
- **File**: `scripts/local_execution_worker.py`, lines 113-193
- **Classification**: Grounded
- **Severity**: High
- **Description**: No gate check verifies that a rollback plan exists for the task. The gates doc (`live-execution-gates.md` line 33) requires "rollback plan is present". The recovery doc (`recovery-and-rollback.md` lines 57-63) states "If rollback is not possible, the tool must remain disabled." Without this gate, execution proceeds regardless of rollback readiness.

**7. Worker does not verify audit log is writable**
- **File**: `scripts/local_execution_worker.py`, lines 113-193
- **Classification**: Inferred
- **Severity**: High
- **Description**: The gates doc (`live-execution-gates.md` line 34) requires "audit log is writable" as a precondition. The worker calls `audit()` as its first action (line 229) but does not pre-check writability. If the audit path is read-only, the worker will proceed through gates and then fail mid-execution when trying to write audit events, potentially leaving the system in a partially-executed state.

**8. Transition function allows re-approval of already-approved tasks**
- **File**: `scripts/approval_queue.py`, lines 326-360
- **Classification**: Grounded
- **Severity**: High
- **Description**: The `transition` function's terminal state check (line 341) only blocks `dry_run_completed`, `rejected_local`, and `cancelled`. It does not block transitions from `approved_local` to `approved_local`. The `approve-local` CLI command (line 452) calls `transition(task_id, "approved_local", ...)`, which will succeed on an already-approved task. This could be used to replay approvals and reset state fields. By contrast, `approve_task` (line 231) properly enforces `pending_review -> approved_local` as the only valid transition.

---

## Medium-risk findings

**9. Hardcoded True gate values create false sense of coverage**
- **File**: `scripts/local_execution_worker.py`, lines 146-150
- **Classification**: Grounded
- **Severity**: Medium
- **Description**: Four gate values are hardcoded to `True` without any validation: `marker_path_under_tmp_live_execution_markers`, `no_arbitrary_path_input`, `no_hermes_write_tool_required`, `no_external_network_required`. These appear in the gate results dict and could mislead auditors into believing these checks are enforced. They are assertions, not checks.

**10. No task-level TTL or staleness enforcement anywhere in the codebase**
- **File**: `scripts/approval_queue.py`, lines 222-258
- **Classification**: Grounded
- **Severity**: Medium
- **Description**: `approve_task` stores `approval_timestamp` but never sets an `expires_at`. No code path ever checks whether an approval is stale. Tasks remain in `approved_local` state indefinitely until manually cancelled. The arm gate has a TTL, but the underlying approval does not. An operator could arm a request for a task that was approved months ago.

**11. Permission deny execution path has no duplicate-execution guard**
- **File**: `scripts/local_execution_worker.py`, lines 581-703
- **Classification**: Grounded
- **Severity**: Medium
- **Description**: `worker_execute_permission_deny` does not check whether the request has already been executed (no check for `request["executed"]` or `request["state"] == "permission_deny_ready"`). The arm gate provides some protection, but if the process crashes between writing the execution file (line 654) and consuming the arm gate (line 685), on restart the same permission deny could be written to the executions index a second time.

**12. Audit log can capture sensitive text via "reason" fields**
- **File**: `scripts/approval_queue.py`, lines 82-87
- **Classification**: Inferred
- **Severity**: Medium
- **Description**: The `audit()` function writes the full payload to `audit.jsonl`. The `sanitize_text` helper truncates to 500 chars but does not scrub secrets. If a user provides a reason containing a token, credential, or other sensitive material (e.g., `--reason "approving because token is sk-abc123..."`), it persists in the audit log on disk. The audit file is under `tmp/` (gitignored) but remains on the local filesystem.

**13. Queue file schema has no version migration or field validation**
- **File**: `scripts/approval_queue.py`, lines 66-72
- **Classification**: Inferred
- **Severity**: Medium
- **Description**: `load_queue` checks that the file contains a dict with a `tasks` list, but does not validate individual task schema or the `version` field value. If the schema evolves (e.g., new required fields), restoring an old backup queue file would load tasks with missing fields that pass through validation silently.

**14. reliability_monitor captures unsanitized command output**
- **File**: `scripts/reliability_monitor.py`, lines 24-37, 54-64
- **Classification**: Inferred
- **Severity**: Medium
- **Description**: `run_cmd` captures full stdout/stderr. `serve_funnel_summary` runs `tailscale serve status` and `tailscale funnel status`, which may include URLs containing path secrets. The function marks `sensitive_output_included: False` (line 63) but does not actually redact the output stored in `result["stdout"]`. If the reliability report JSON is shared, these URLs could leak.

---

## Low-risk findings

**15. Systemd service uses WantedBy=multi-user.target for a user-specific service**
- **File**: `drafts/hermes-local-execution-worker.service.draft`, line 31
- **Classification**: Grounded
- **Severity**: Low
- **Description**: The service runs as `User=igzela` but installs to `multi-user.target`. Since this is a user-specific service, `default.target` or a user session target would be more appropriate. This is a draft, so the risk is limited.

**16. No file locking on queue or request file operations**
- **File**: `scripts/approval_queue.py`, lines 66-79; `scripts/local_marker_executor.py`, lines 68-80
- **Classification**: Inferred
- **Severity**: Low
- **Description**: The atomic write pattern (write to .tmp, then replace) prevents file corruption, but does not prevent lost updates if two processes read-modify-write concurrently. The worker daemon and the CLI could theoretically race. In practice, the arm gate mechanism serializes execution, reducing this risk.

**17. permission_deny_dry_run uses raw .strip() instead of sanitize_text**
- **File**: `scripts/permission_deny_dry_run.py`, lines 77, 82
- **Classification**: Grounded
- **Severity**: Low
- **Description**: `create_preview` uses `permission_id.strip()` and `reason.strip()` for input validation, while all other modules use `approval_queue.sanitize_text()` which also truncates to 500 chars. This inconsistency means permission_id and reason fields in previews are not length-bounded.

**18. Double save in create_task**
- **File**: `scripts/approval_queue.py`, lines 158-162
- **Classification**: Grounded
- **Severity**: Low
- **Description**: `create_task` calls `save_queue` twice -- once after appending the task and once after appending the audit event ID. This is correct for data consistency but doubles I/O. Not a correctness issue.

---

## False positives / not enough evidence

**A. GPT architect finding: "13 live gates not all enforced"** -- Partially confirmed. The worker does enforce 7+ substantive gates (request state, task state, approval, approval source, dry-run status, arm gate validity, private content). However, the missing gates (LIVE_ENABLED, idempotency key, scope, rollback plan, audit writability, approval TTL, per-tool disable) are real omissions. The count of "13" from the doc maps to a superset of what the code documents; the worker implements its own subset.

**B. GPT architect finding: "Recovery replay can re-execute broken tasks"** -- Partially confirmed. The atomic write pattern (tmp+replace) makes replay of partially-written files unlikely on Linux. However, there is no schema validation on load, so restoring an old backup could introduce stale tasks. The actual replay risk is low given the arm gate + state machine protections.

**C. GPT architect finding: "Secrets in transient artifacts"** -- Partially confirmed. The `.gitignore` covers `tmp/` comprehensively. The real risk is not git commit of secrets but rather audit log accumulation of sensitive text in reason fields and unsanitized command output in reliability reports.

---

## Minimal patches recommended

**Patch 1 (Critical)**: Add `LiveFlags` check to `local_execution_worker.py` `check_worker_gates`. Import `flags_from_env` from `local_marker_executor` and add checks:
```python
flags = local_marker_executor.flags_from_env()
if not flags.live_enabled:
    raise WorkerError("LIVE_ENABLED is false")
if not flags.local_marker_live_enabled:
    raise WorkerError("LOCAL_MARKER_LIVE_ENABLED is false")
```
Insert after line 118, before the gate dict construction.

**Patch 2 (Critical)**: Add marker existence check to `check_worker_gates` in `local_execution_worker.py`. After line 146, replace the hardcoded True with an actual path existence check:
```python
mpath = local_marker_executor.marker_path(task_id, paths.marker_dir)
if mpath.exists():
    raise WorkerError("marker already exists for this task")
```

**Patch 3 (High)**: Add idempotency key validation to `check_worker_gates` in `local_execution_worker.py`. After line 160, add:
```python
if not approval_queue.sanitize_text(str(task.get("idempotency_key") or "")):
    raise WorkerError("idempotency key is required")
```

**Patch 4 (High)**: Add approval timestamp TTL check. Introduce a constant (e.g., `APPROVAL_TTL_SECONDS = 86400`) in `local_execution_worker.py` and validate:
```python
approval_ts = task.get("approval_timestamp")
if approval_ts:
    # parse and check against TTL
```
This requires adding timestamp parsing. Alternatively, store `expires_at` at approval time in `approval_queue.py`.

**Patch 5 (High)**: Add `approved_local` to the terminal states in `approval_queue.py` `transition` function (line 341), or add a more specific check that prevents re-transitioning to the same state.

**Patch 6 (Medium)**: Add rollback plan check to `check_worker_gates` -- validate that the task metadata contains a `rollback_plan` or equivalent field before allowing execution.

---

## Tests or validators recommended

1. **Kill switch test**: Set `LIVE_ENABLED=false` in environment, arm a request, run `worker_run_once`. Assert `WorkerError` is raised with "LIVE_ENABLED is false". Currently this test would fail (bug confirmed).
2. **Double-write crash recovery test**: Write a marker file manually, set up an arm gate and request in ready state, run `worker_run_once`. Assert that the existing marker is not overwritten and execution is blocked.
3. **Idempotency key absence test**: Create a task with empty idempotency key, advance through states, run `worker_run_once`. Assert gate failure.
4. **Approval TTL test**: Create and approve a task, wait or mock time past TTL, arm and run worker. Assert gate failure.
5. **Transition replay test**: Call `transition(task_id, "approved_local", ...)` on an already-approved task. Assert either success with idempotency or explicit rejection.
6. **Permission deny duplicate test**: Set up a permission deny request and arm gate, execute once, then re-create the arm gate (simulating crash before gate consumption). Assert second execution either blocked or idempotent.
7. **Queue schema migration test**: Load a queue file with a future version number or missing required fields. Assert appropriate error handling.
8. **Audit log redaction test**: Submit a task with a reason containing a simulated secret string. Assert the audit log entry is sanitized or the secret is not present in plaintext.

---

**Summary**: The most critical finding is that the `local_execution_worker` has its own independent gate function (`check_worker_gates`) that diverges significantly from the canonical gate function in `local_marker_executor.check_gates`. The worker path bypasses the global kill switch, omits idempotency and scope checks, and does not prevent double marker writes on crash recovery. These are not theoretical risks -- they are concrete code-level omissions that can be verified by reading the two functions side by side.
