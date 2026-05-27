# Claude Code Gate Mapper Output

Experiment: hermes-perm-audit-002
Target: hermes-gateway-lab
Basis: direct code inspection of 8 files

## Gate Mapping: 25 Deny Cases

| Gate ID | Doc Reference | Code Location | Coverage | Notes |
|---------|--------------|---------------|----------|-------|
| D001: LIVE_ENABLED missing | `docs/live-execution-gates.md:8,39` | `scripts/local_marker_executor.py:50-54` (`flags_from_env`), `:361-362` (`check_gates` blocks) | **complete** | When env var is unset, `os.environ.get("LIVE_ENABLED", "")` returns `""`, parsed as `False`. The `_block` call at line 362 fires. |
| D002: LIVE_ENABLED=false | `docs/live-execution-gates.md:8,39` | `scripts/local_marker_executor.py:52` (env parsed), `:361-362` (`check_gates` blocks) | **complete** | Same code path as D001. No separate explicit-vs-unset distinction. |
| D003: live scope requested but not enabled | `docs/live-execution-safety-model.md:50-52` | `scripts/local_marker_executor.py:361-364`, `scripts/approval_queue.py:129-130` | **partial** | Code uses boolean flags instead of scope-based allowlist. No check verifies specific live scope is in allowed set. |
| D004: scope not in allowed list | `docs/live-execution-safety-model.md:22-53` | `scripts/approval_queue.py:129-130`, `scripts/dry_run_executor.py:113-114` | **complete** | Scope validation at task creation and dry-run entry. Worker trusts upstream validation. |
| D005: missing Charlie local approval | `docs/live-execution-gates.md:28` | `scripts/local_execution_worker.py:160-164`, `scripts/local_marker_executor.py:345-348` | **complete** | All gate functions hardcode comparison against `LIVE2_LOCAL_CLI_SOURCE`. |
| D006: ChatGPT-only approval | `docs/live-execution-safety-model.md:7` | `scripts/approval_queue.py:237` (hardcodes source), `:376` (`chatgpt_final_approval_enabled: False`) | **complete** | ChatGPT has no code path to set approval source. |
| D007: approval TTL expired | `docs/live-execution-gates.md:29` | `scripts/local_execution_worker.py:175-176` (arm_gate expires_at only) | **partial** | Doc says "approval timestamp within TTL" but code only checks arm gate expiry, not task approval_timestamp. |
| D008: approval marker format error | Not explicitly documented | `scripts/local_marker_executor.py:359-360` (existence check only) | **missing** | No marker file content/format validation. |
| D009: approval mismatch | `docs/live-execution-gates.md:18` | `scripts/local_execution_worker.py:178-182` (arm_gate matching) | **partial** | Distributed across multiple if-statements. No single "approval mismatch" gate. |
| D010: missing idempotency key | `docs/live-execution-gates.md:31` | `scripts/local_marker_executor.py:332,351-352`, `scripts/dry_run_executor.py:117-118` | **complete** | Both executors validate idempotency key presence. |
| D011: duplicate idempotency key | Not explicitly documented | `scripts/local_execution_worker.py:187-188` (arm_gate consumed) | **partial** | Per-task duplicate prevented by arm gate. No cross-task duplicate detection. |
| D012: idempotency key mismatch | Not explicitly documented | `scripts/dry_run_executor.py:142-143` | **partial** | Dry-run validates match. Worker does not re-validate. |
| D013: stale key after queue recovery | Not explicitly documented | `scripts/local_execution_worker.py:187-188` | **partial** | Arm gate consumption prevents re-execution. No explicit staleness detection. |
| D014: missing rollback plan | `docs/live-execution-gates.md:33,57-63` | No code validates rollback plan presence | **missing** | Doc requires "rollback plan is present". Zero gate code validates. |
| D015: empty rollback plan | `docs/live-execution-gates.md:33` | No code validates rollback plan content | **missing** | No rollback plan field exists on tasks. |
| D016: rollback path mismatch | `docs/live-execution-gates.md:59` | No code validates rollback path pre-execution | **missing** | Rollback is purely reactive. |
| D017: undeclared irreversible operation | `docs/live-execution-risk-classes.md:15-17` | `scripts/local_marker_executor.py:353-354` | **partial** | Risk class validation is a proxy. Concept not modeled directly. |
| D018: R4 external side effect | `docs/live-execution-risk-classes.md:11,17` | `scripts/local_marker_executor.py:355-356`, `scripts/dry_run_executor.py:111-112` | **complete** | Explicitly blocked at creation, dry-run, and executor. |
| D019: R5 private content | `docs/live-execution-risk-classes.md:12,18` | `scripts/local_marker_executor.py:357-358`, `scripts/local_execution_worker.py:190-191` | **complete** | Explicitly blocked in both executor and worker. |
| D020: unknown risk class | `docs/live-execution-risk-classes.md:6-13` | `scripts/local_marker_executor.py:353-354` | **complete** | Any class outside allowed set is rejected. |
| D021: missing risk class | Implicit in risk class validation | `scripts/approval_queue.py:117` (default R2) | **complete** | Default R2 + allowlist check catches None. |
| D022: audit path not writable | `docs/live-execution-gates.md:33` | `scripts/approval_queue.py:63,82-87` | **partial** | No pre-write writability check. OSError would crash, not deny. |
| D023: audit write failure | `docs/live-execution-gates.md:33` | `scripts/approval_queue.py:82-87` (no try/except) | **partial** | No error handling. Write failure crashes execution. |
| D024: secret in reason field | `docs/live-execution-safety-model.md:73` | `scripts/approval_queue.py:90-94` (truncate only) | **missing** | No secret detection or redaction. Only truncates to 500 chars. |
| D025: missing dry-run preview | `docs/live-execution-gates.md:35` | `scripts/dry_run_executor.py:91-95`, `scripts/local_marker_executor.py:322,349-350` | **complete** | Must exist and have status "success". |

## Coverage Summary

| Coverage | Count | Gate IDs |
|----------|-------|----------|
| **Complete** | 12 | D001, D002, D004, D005, D006, D010, D018, D019, D020, D021, D025 |
| **Partial** | 8 | D003, D007, D009, D011, D012, D013, D017, D022, D023 |
| **Missing** | 5 | D008, D014, D015, D016, D024 |

**Total: 25 gates mapped. 12 complete (48%), 8 partial (32%), 5 missing (20%).**

## Key Discrepancies

1. **D007 (approval TTL)**: Doc says "approval timestamp within TTL" but code only checks arm gate expiry (max 1 hour). Task approval timestamp staleness never validated.
2. **D008, D014-D016 (marker format, rollback plan)**: Documented requirements with zero code implementation. Rollback plan checks are the largest gap.
3. **D024 (secret in reason)**: `sanitize_text` only truncates. No secret detection despite explicit safety-model requirement.
4. **D022-D023 (audit writability)**: No error handling. Write failure crashes execution instead of structured deny.

## No-Write Confirmation

No source files were modified in the target repo. All operations were read-only.
