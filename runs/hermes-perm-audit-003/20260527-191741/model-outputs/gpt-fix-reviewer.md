# GPT Fix Architecture Review — hermes-perm-audit-003

## Architecture Assessment

### Fix 1: Canonical gate import — PASS

The approach of threading `LiveFlags` through `check_worker_gates` is sound. Using `flags_from_env()` as default maintains backward compatibility while ensuring the canonical flag checks are always evaluated.

**Ordering concern:** The canonical checks (LIVE_ENABLED, idempotency, risk class) are now evaluated before the worker-specific checks (arm gate validation). This is correct — deny the request early on fundamental safety grounds before checking operational details.

**One gap:** The worker still doesn't check `risk_class` via the same `set` membership as marker executor. The worker uses `task.get("risk_class") in {"R2", "R3"}` which matches the marker executor's check. This is correct.

### Fix 2: Rollback plan — PASS_WITH_NOTES

Adding `rollback_plan` to the task schema as a required string field is the minimal viable approach. Notes:

- The gate check uses `sanitize_text(str(task.get("rollback_plan") or ""))` which handles None, empty string, and whitespace-only values correctly.
- The `create_task` function defaults to empty string, which means existing tasks will fail the gate. This is intentional — tasks without rollback plans should not proceed to live execution.
- No validation of rollback plan content (e.g., must contain actual recovery steps). This is acceptable for v1 — content validation can be added later.

### Fix 3: Secret redaction — PASS

The regex-based approach covers the most common secret patterns. The `SECRET_PATTERNS` list is defined at module level, making it easy to extend. The `callable` check for lambda replacements is a clean pattern.

**Risk:** The regex patterns are applied to every `sanitize_text` call, which is used pervasively. Performance impact should be negligible for the 500-char truncation limit, but worth noting.

**Coverage gaps:** No detection for:
- GitHub tokens (`ghp_...`, `github_pat_...`)
- Slack tokens (`xoxb-...`, `xoxp-...`)
- Generic hex strings that look like secrets

These can be added incrementally.

### Fix 4: Risk class and scope — PASS

Adding `risk_class` and `external_side_effect` checks to the worker brings it to parity with the marker executor. The checks are placed after the canonical flag checks and before the arm gate checks, which is the correct ordering.

### Threading flags — PASS

The `flags` parameter is optional throughout the call chain with `None` default, maintaining backward compatibility. The smoke tests demonstrate that explicit flag passing works correctly.

## Verdict

**experiment_verdict: COMPLETE**
**target_control_verdict: PASS**

All 4 fixes are architecturally sound. The worker daemon now enforces the same canonical gate logic as the marker executor. C001-C003 should now pass.

## Recommendations for 004+

1. Consider a shared `validate_task_gates(task, flags)` function to eliminate duplication between worker and marker
2. Add rollback plan content validation (minimum length, required fields)
3. Extend secret patterns with provider-specific token formats
4. Add a conformance test that runs both paths with identical inputs and compares outputs
