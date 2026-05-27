# GPT Test Architecture Reviewer Output

Experiment: hermes-perm-audit-002
Role: Test Architecture Reviewer
Target: Hermes Gateway Lab deny-path implementation audit
Basis: Claude Code Gate Mapper summary, path-aware deny-path matrix, experiment.yaml, current 002 status report
Review status: architecture review complete
Codex review status: pending / not included in this review

## Architecture Verdict

experiment_verdict: COMPLETE
target_control_verdict: FAIL

The experiment should be considered COMPLETE because it achieved its primary experimental goal: it converted the original 25-case deny-path matrix into a path-aware verification structure and exposed the difference between the canonical `marker_executor` path and the actual `worker_daemon` path.

The target control should be considered FAIL because the current evidence does not prove default-deny behavior across both execution paths. More importantly, the evidence confirms policy-runtime drift: several deny cases are complete in the canonical path but missing in the worker daemon path.

The most important result of 002 is not the raw coverage percentage. The important result is this:

- marker_executor has stronger gate coverage than worker_daemon.
- worker_daemon is an actual execution path.
- therefore canonical policy coverage does not prove runtime safety.

This is a valid and useful failure. It means Token Furnace Lab is doing the right kind of work: turning model findings into testable control evidence instead of treating documentation or single-path code review as proof.

## Coverage Assessment

Current reported coverage:
- marker_executor: 12/25 complete, 8/25 partial, 5/25 missing
- worker_daemon: 10/25 complete, 6/25 partial, 9/25 missing
- conformance: 19/25 pass, 6/25 divergent

This is enough to complete the experiment, but not enough to pass the target control.

The matrix is directionally sound because it now asks the right question: "Does each deny case hold for each execution path?" That is a major improvement over the original single-status matrix. A deny case marked `complete` globally would have hidden the worker drift. The path-aware matrix prevents that false confidence.

However, the current coverage does not satisfy the 002 target PASS criteria because:
- Worker daemon has more missing gates than marker executor.
- Some P0 cases are complete only on marker executor.
- Rollback plan enforcement is missing across both paths.
- Secret-like reason redaction is missing across both paths.
- Audit fail-closed behavior remains partial, not proven.
- Several `complete` statuses appear to be based on static evidence rather than executable deny assertions.

The coverage is good enough for experiment completion, but not good enough for safety acceptance.

## P0 Case Assessment

### D001/D002: LIVE_ENABLED missing/false

Verdict: FAIL for target control

Reason: marker_executor is complete, worker_daemon is missing.

This is a critical path-conformance failure. If the canonical path checks `LIVE_ENABLED` but the worker daemon does not, the system cannot claim default-deny behavior for live execution gating.

The correct interpretation is not: "Hermes does not check LIVE_ENABLED anywhere."

The correct interpretation is: "The canonical marker executor checks LIVE_ENABLED, but the worker daemon path does not prove equivalent enforcement."

This should remain a P0 blocker for target PASS.

### D004: scope not allowed

Verdict: PASS_WITH_NOTES for this case

Reason: both paths are reported complete, but worker evidence says it trusts upstream validation.

This is acceptable only if worker cannot receive unvalidated tasks from any bypass path. If worker consumes queue items that can be manually written, recovered, replayed, or mutated, upstream validation alone is not enough.

Required follow-up: verify whether worker_daemon validates scope directly or whether queue ingestion is tamper-resistant.

### D005: missing local approval

Verdict: PASS for current evidence

Reason: both paths reportedly check for local approval.

This is one of the strongest controls in the current matrix. It supports the design principle that ChatGPT cannot be final local execution authority.

Required follow-up: ensure the local approval marker cannot be replayed or reused across unrelated tasks.

### D006: ChatGPT-only approval

Verdict: PASS for current evidence

Reason: both paths reportedly reject ChatGPT-only approval.

This is a critical control and appears covered. It should remain in every future regression matrix because it is central to the human authority model.

### D007: approval TTL expired

Verdict: PARTIAL

Reason: both paths appear to check arm gate expiry, but not necessarily task approval timestamp.

This is not enough for full target PASS. TTL semantics need to be defined clearly:
- approval creation time
- approval expiry time
- arm gate expiry time
- execution attempt time

If only one of these is checked, stale approval may still be possible through queue or recovery edge cases.

Required follow-up: define a single canonical TTL model and test it across both paths.

### D010: missing idempotency key

Verdict: FAIL for target control

Reason: marker_executor is complete, worker_daemon is missing.

This is a high-severity conformance gap. A daemon path that can execute without idempotency protection risks duplicate execution, replay, and unsafe recovery behavior.

This should be a must-fix in 003.

### D014: missing rollback plan

Verdict: FAIL for target control

Reason: missing on both marker_executor and worker_daemon.

This is a design-level gap, not just worker drift. The system currently does not appear to enforce rollback plan presence before execution.

The immediate consequence is that even if approval and scope gates work, failure recovery may not be reviewable before action.

Required 003/004 decision: Either rollback_plan becomes mandatory for all live-intent tasks, or the system explicitly scopes rollback enforcement to a later hardening stage. For a live-capable system, this cannot remain missing.

### D018/D019: R4/R5 requested

Verdict: PASS for current evidence

Reason: both paths reportedly deny R4 and R5.

This is a strong control. It reduces risk while the system is still in non-live or controlled live-readiness stages.

Required follow-up: keep these cases as permanent regression tests.

### D022/D023: audit fail-closed

Verdict: PARTIAL / FAIL for target PASS

Reason: no pre-write writability check and no clear audit() error handling.

This is important because audit failure should normally fail closed for live or live-intent execution. A system that executes but cannot write audit evidence is not safe enough for permissioned local automation.

For live-intent execution:
- audit unavailable -> deny
- audit write failure -> deny

For read-only dry-run or purely diagnostic modes, a weaker behavior may be acceptable, but it must be explicitly scoped.

### D024: secret in reason field

Verdict: FAIL for target control

Reason: missing on both paths.

This is a cross-path logging/sanitization failure. If `reason` can contain secret-like material and only truncation is applied, then the system may persist sensitive data into audit logs, run artifacts, queues, or failure records.

This should be treated as P0 for any system that stores model-generated or user-provided reason strings.

Required redaction targets:
- API keys
- tokens
- passwords
- path secrets
- approval comments
- model output snippets
- Tailscale URLs
- audit log fields
- recovery artifacts

## Evidence Gaps

The current gate mapper provides useful evidence, but several `complete` statuses appear to be based on code inspection rather than executed test assertions.

For 002, that is acceptable if the experiment is framed as "implementation audit / matrix classification."

For target PASS, it is not enough.

Future matrix fields should separate:
- `coverage_status`: complete | partial | missing
- `behavior_test_status`: pass | fail | untested | blocked
- `evidence_type`: static_inspection | unit_test | integration_test | manual_trace

A case should not be considered truly safe unless it has behavior evidence, not only source-level evidence.

## Invalid Claims

The following claims should be rejected unless new evidence is provided.

### "The system has default-deny behavior"

Reason: default-deny is not proven across both execution paths. Worker daemon has missing gates in P0 cases.

### "LIVE_ENABLED is checked"

Reason: marker_executor coverage does not prove worker_daemon coverage. D001/D002 are missing on worker path.

### "Idempotency is enforced"

Reason: D010 is complete on marker_executor but missing on worker_daemon. D011-D013 remain partial or missing in edge cases.

### "Rollback plan exists"

Reason: D014-D016 are missing on both paths.

### "Audit logging is safe"

Reason: D022/D023 are partial, and D024 is missing.

### "Coverage is X% complete"

Reason: completeness must be path-specific and evidence-type-specific.

### "Worker bugs are fixed in 002"

Reason: 002 is a verification experiment. Mixing production fixes into 002 would contaminate the audit baseline. Fixes belong in 003.

## PASS/PASS_WITH_NOTES/FAIL Decision

### Experiment verdict: COMPLETE

002 should be marked COMPLETE because:
- The deny-path matrix was converted into path-aware form.
- 25 cases were classified across marker_executor and worker_daemon.
- P0 cases were identified.
- Critical path divergence was found.
- The experiment preserved the intended verification-first boundary.
- The result gives a clear basis for 003.

This is a successful experiment even though the target control fails.

### Target control verdict: FAIL

The target control should be marked FAIL.

Primary reasons:
- D001 worker_daemon missing LIVE_ENABLED missing check.
- D002 worker_daemon missing LIVE_ENABLED=false check.
- D010 worker_daemon missing idempotency key check.
- D012 worker_daemon missing idempotency key match re-validation.
- D014-D016 rollback plan enforcement missing on both paths.
- D024 secret-like reason redaction missing on both paths.
- D022/D023 audit fail-closed behavior remains partial.
- Worker daemon has 9 missing gates versus marker_executor 5 missing gates.
- Canonical gate coverage is stronger than actual daemon path coverage.
- Path conformance is not proven.

This is not PASS_WITH_NOTES because the gaps are not merely documentation or P1 hardening issues. They affect P0 live enablement, idempotency, rollback, auditability, and secret safety.

## Scoring

- matrix_coverage: 22/25 — Reason: all 25 cases classified, but some evidence needs stronger executable backing.
- p0_deny_behavior: 10/35 — Reason: several P0 cases fail or remain partial/missing on one or both paths.
- evidence_quality: 10/15 — Reason: useful static evidence exists, but executable assertions are not yet systematic.
- safety_boundary: 15/15 — Reason: 002 appears to preserve non-live, non-production-fix boundaries.
- synthesis_quality: 9/10 — Reason: experiment verdict and target verdict are separated correctly.
- estimated_total: 66/100

Experiment passes as an audit artifact.
Target control fails as a safety control.

## Required Follow-up

### 003: Worker Gate Conformance Fix

Recommended experiment id: hermes-perm-audit-003
Recommended name: Worker Gate Conformance Fix

Goal: Make worker_daemon enforce the same canonical gate logic as marker_executor, or prove behavioral equivalence through shared deny-path tests.

Unlike 002, 003 should allow limited production code changes, but only inside a narrow boundary.

Allowed:
- Modify worker gate enforcement
- Add shared gate adapter if needed
- Add unit tests / fixtures
- Add conformance tests
- Add audit redaction function
- Add rollback_plan schema validation for live-intent tasks

Forbidden:
- Enable live execution
- Execute live actions
- Broaden risk class allowlist
- Remove human local approval requirement
- Treat ChatGPT as final approver
- Reduce audit logging
- Patch around tests without unifying behavior

### 003 P0 success criteria

1. D001 worker_daemon denies when LIVE_ENABLED missing.
2. D002 worker_daemon denies when LIVE_ENABLED=false.
3. D010 worker_daemon denies when idempotency key is missing.
4. D012 worker_daemon re-validates or safely trusts a signed/immutable dry-run idempotency match.
5. D014 live-intent task without rollback_plan is denied.
6. D022 audit path unavailable causes deny for live-intent execution.
7. D023 audit write failure causes deny for live-intent execution.
8. D024 secret-like reason is redacted or denied before persistence.

### 003 P1 success criteria

1. D007 TTL semantics clarified and tested.
2. D008 approval marker format validation added.
3. D009 approval mismatch made explicit.
4. D011 duplicate idempotency semantics defined as deny or safe no-op.
5. D013 stale key after queue recovery tested.
6. D015/D016 rollback empty/mismatch cases tested.

### Recommended architecture

worker_daemon imports and calls canonical gate logic.

Avoid maintaining two independent gate functions. The 002 result shows that duplicated gate logic is the root cause of policy-runtime drift.

Recommended architecture:
```
gate_policy.py
  - flags_from_env()
  - check_gates()
  - validate_scope()
  - validate_risk_class()
  - validate_approval()
  - validate_idempotency()
  - validate_rollback_plan()
  - validate_audit_ready()
  - sanitize_or_reject_reason()

local_marker_executor.py
  - imports gate_policy.check_gates

local_execution_worker.py
  - imports gate_policy.check_gates
  - no independent check_worker_gates except thin wrapper
```

If extracting a shared module is too large for 003, then minimal acceptable step:
`local_execution_worker.check_worker_gates` delegates to `local_marker_executor.check_gates`

But the better long-term form is a neutral shared policy module, not worker importing executor.

### Conformance test shape

Minimum conformance test shape:
```python
for each P0 fixture:
    marker_result = marker_executor_gate(fixture)
    worker_result = worker_daemon_gate(fixture)
    assert marker_result == worker_result
    assert worker_result == deny
```

Required fixtures:
- D001-live-enabled-missing.yaml
- D002-live-enabled-false.yaml
- D004-scope-not-allowed.yaml
- D005-missing-local-approval.yaml
- D006-chatgpt-only-approval.yaml
- D007-ttl-expired.yaml
- D010-missing-idempotency-key.yaml
- D014-missing-rollback-plan.yaml
- D018-r4-requested.yaml
- D019-r5-requested.yaml
- D022-audit-path-not-writable.yaml
- D023-audit-write-failure.yaml
- D024-secret-in-reason.yaml

### 003 verdict criteria

PASS:
1. All P0 deny cases pass on both paths.
2. Worker and marker gate decisions are equivalent for P0 fixtures.
3. Worker no longer has independent drift-prone gate logic.
4. D014 rollback missing denies live-intent tasks.
5. D024 secret-like reason is redacted or denied before persistence.
6. Audit fail-closed behavior is tested.
7. No live execution occurs during test.

PASS_WITH_NOTES:
1. All authority gates pass.
2. Worker imports or delegates to canonical gate.
3. Rollback or audit hardening is partially implemented but explicitly scoped.
4. No P0 execution bypass remains.

FAIL:
1. Any P0 fixture allows execution.
2. Worker and marker disagree on deny decision.
3. LIVE_ENABLED=false still does not stop worker.
4. Missing idempotency key still passes worker.
5. Secret-like reason can persist unredacted.

## Methodology Improvements

### 1. Dual verdict is now a core rule

This is now a core methodological rule.

```
experiment_verdict: COMPLETE | INCOMPLETE
target_control_verdict: PASS | PASS_WITH_NOTES | FAIL
```

This prevents the common error: "The experiment completed successfully, therefore the target is safe."

002 proves the opposite: the experiment completed successfully by showing the target fails.

### 2. Path-aware matrix is now standard

Any system with multiple execution paths must never use a single global status.

```yaml
D001:
  status: complete  # WRONG
  paths:
    marker_executor:
      status: complete
    worker_daemon:
      status: missing  # CORRECT
```

This should become a Token Furnace Lab standard.

### 3. Evidence type must be explicit

Every matrix entry should say what kind of evidence supports it.

Recommended enum:
- static_inspection
- unit_test
- integration_test
- manual_trace

This prevents static inspection from being mistaken for tested behavior.

### 4. Assertion strength must be explicit

Recommended enum:
- strong: asserts deny/redact/no-execution
- medium: asserts error or blocked state
- weak: only checks no crash or log presence
- none: not tested

This will catch weak tests that look like coverage but do not prove fail-closed behavior.

### 5. Conformance matrix is now standard

For safety controls, the key question is often not "does any code check this?" but: "do all execution paths enforce the same policy?"

Recommended matrix:
```yaml
conformance_matrix:
  canonical_path: marker_executor
  runtime_paths:
    - worker_daemon
  cases:
    - id: C001
      name: worker uses canonical gate
      expected: true
      actual: false
```

### 6. Revised findings should be preserved

001 showed a useful pattern:
- Codex found worker risk.
- Gate mapper clarified marker path vs worker path.
- GPT reframed the issue as policy-runtime drift.

This is the correct workflow. A model being partially wrong can still expose a real structure. The lab should preserve "revised findings," not just accepted/rejected findings.

Recommended: `revised_findings/` or a section in synthesis:
```
## Revised Findings
- F-0001 refined from "missing LIVE_ENABLED" to "duplicated worker gate"
```

### 7. Evaluator rules should be generated per experiment

The 002 result should create or update evaluator rules:
- ER: No global PASS from single-path evidence.
- ER: Worker must not duplicate canonical gate logic without conformance tests.
- ER: Any live-intent gate must have deny-path fixture.
- ER: Secret-bearing free-text fields must be redacted before persistence.
- ER: Audit failure must fail closed for live-intent execution.

### 8. Experiment taxonomy

Suggested taxonomy:
```
audit experiment:
  goal: find and classify gaps
  production patch: forbidden

verification experiment:
  goal: prove or disprove behavior
  production patch: usually forbidden

fix experiment:
  goal: repair a known control gap
  production patch: allowed in narrow scope

regression experiment:
  goal: prove the bug stays fixed
  production patch: forbidden
```

Current classification:
- 001: audit experiment
- 002: verification experiment
- 003: fix experiment
- 004: regression experiment

### 9. Healthy failure is a success signal

002 did this correctly.

Healthy failure means: The experiment succeeds by proving the target fails.

This is essential for safety work. Without it, agents may try to force PASS by softening findings.

### 10. Machine-readable output should be standardized

The lab should eventually require:
- run_verdict.yaml
- matrix_status.yaml
- synthesis.md
- evidence_index.yaml

Markdown is good for review, but YAML/JSON is better for automation.

Minimum future artifact:
```yaml
experiment_id: hermes-perm-audit-002
experiment_verdict: COMPLETE
target_control_verdict: FAIL
critical_findings:
  - D001: worker missing LIVE_ENABLED
  - D002: worker missing LIVE_ENABLED=false
  - D010: worker missing idempotency key
  - D014: rollback missing on both paths
  - D024: secret redaction missing
next_experiment: hermes-perm-audit-003
```

## Final Summary

experiment_verdict: COMPLETE
target_control_verdict: FAIL
next_experiment: hermes-perm-audit-003: fix-worker-gate-conformance

The highest-value 003 fix is not to patch each missing worker condition independently. The right fix is to remove or reduce duplicated gate logic by making worker_daemon use the same canonical gate policy as marker_executor, then add P0 dual-path conformance tests.

The key methodological lesson is: A permission system is not verified when one path is safe. It is verified only when every execution path enforces the same policy, with evidence strong enough to catch drift.
