# GPT Architect Audit Output

Experiment: hermes-perm-audit-001  
Target repo: hermes-gateway-lab  
Target branch: harness-onboarding  
Target commit: 05092f09  
Basis: Claude Code repo-reader output only  
Write status: target repo reported unmodified  

## Scope Boundary

This audit is based only on the repo-reader summary provided by Claude Code. I did not inspect the target repository directly. Findings below are classified as:

- Grounded: directly supported by the repo-reader output
- Inferred: reasonable architectural implication, but needs file-level verification
- Unknown: insufficient evidence

No files are assumed to exist unless named in the repo-reader output.

## Architecture Assessment

The current permission architecture appears safety-first and deliberately conservative.

The strongest architectural controls are:

1. Explicit scope model with five scopes: `read`, `plan`, `approval.local`, `dry_run`, and `live`.
2. `live` scope exists but is effectively disabled through `allowed: []` and `not_enabled`.
3. Risk classes R4 and R5 are not enabled.
4. Live execution requires 13 preconditions, including `LIVE_ENABLED=true`, local Charlie approval, TTL, idempotency key, and rollback plan.
5. ChatGPT is explicitly disallowed from being the final approver.
6. Human operator remains final authority.
7. Secret handling policy includes never-commit rules and pre-commit leakage scanning.
8. Recovery policy distinguishes read-only health checks, queue recovery, and bridge recovery requiring explicit approval.

Architecturally, this is the right direction. The main risk is not that the policy is too permissive; the main risk is that policy, implementation, and evidence may drift apart.

## Architecture Risks

### Risk 1: Policy-to-runtime enforcement gap

Classification: Inferred  
Severity: High  
Evidence: Scope model, live gate checklist, and approval flow exist; unknowns include `approval_queue` idempotency and `local_execution_worker` gate enforcement.

The design defines strong execution boundaries, but the repo-reader output does not prove that the local execution worker enforces every required gate at runtime.

Risk pattern:

```text
docs say live requires 13 checks
but worker may enforce only a subset
or enforce them in a bypassable order

Why it matters: the strongest control set is only useful if the executor cannot bypass it.

Minimal control needed: a runtime gate verifier that fails closed when any required live condition is missing.

Risk 2: Missing decision record weakens auditability

Classification: Grounded
Severity: Medium
Evidence: DECISION_RECORD.md is referenced by quality gates but does not exist.

This is a concrete documentation integrity problem. If quality gates depend on decision records, missing DECISION_RECORD.md means reviewers cannot reconstruct why permission boundaries, risk classes, or live gating rules were accepted.

Why it matters: permission systems need historical accountability, not just current state.

Minimal control needed: create DECISION_RECORD.md with initial decisions covering scope model, disabled live mode, human approval authority, and R4/R5 non-enablement.

Risk 3: Dirty draft file may hide operational drift

Classification: Grounded
Severity: Medium
Evidence: dirty state: M drafts/hermes-local-execution-worker.service.draft.

A modified systemd worker draft is permission-relevant. Even if it is only a draft, it may represent planned execution behavior. Dirty state also makes audit reproducibility weaker.

Why it matters: systemd worker configuration can alter startup behavior, environment exposure, working directory, permissions, and restart policy.

Minimal control needed: review and classify this dirty draft before treating the branch as audit-stable.

Risk 4: Kill switch is described but not proven testable

Classification: Inferred
Severity: Medium
Evidence: suggested improvement: formalize kill switch tests; live execution gates include LIVE_ENABLED=true.

The architecture has live enablement gating, but there is no evidence that disable paths are tested.

Why it matters: a permission architecture should prove both allow and deny behavior. A kill switch that is only documented is not enough.

Minimal control needed: add a deny-path test proving that live execution cannot proceed when LIVE_ENABLED is unset, false, expired, or mismatched.

Risk 5: Rollback plan exists as live gate but may not exist in dry-run preview

Classification: Inferred
Severity: Medium
Evidence: live execution requires rollback plan; grounded suggestion says “Add rollback plan to dry-run executor.”

The design requires rollback before live, but dry-run should also preview rollback impact. Otherwise approval may be granted without knowing how failure recovery works.

Why it matters: rollback should be reviewed before execution, not discovered after failure.

Minimal control needed: dry-run output must include rollback plan, irreversible-operation warning, and expected touched paths.

Risk 6: Secret handling policy may not cover transient paths

Classification: Inferred
Severity: Medium
Evidence: secret handling is comprehensive; grounded suggestion says audit tmp/ for secret leaks; unknown includes path secret rotation.

The policy covers never-commit and pre-commit scanning, but transient directories may still leak sensitive material into run logs, tmp files, queue files, worker logs, or recovery artifacts.

Why it matters: not all leaks happen through committed files.

Minimal control needed: extend secret scan to generated artifacts, tmp/, queue files, worker logs, and run outputs.

Risk 7: Recovery flows may preserve unsafe artifacts

Classification: Inferred
Severity: Medium
Evidence: queue recovery preserves broken files; bridge recovery requires explicit approval.

Preserving broken queue files is good for auditability, but unsafe if those files contain secrets, executable payloads, stale approvals, or invalid idempotency keys.

Why it matters: recovery can accidentally reintroduce old authority or sensitive material.

Minimal control needed: recovered queue artifacts should be quarantined, redacted, and marked non-executable by default.

Missing Control Points
1. Runtime gate conformance test

Need a test that proves implementation matches the documented 13 live checks.

Expected test cases:

LIVE_ENABLED missing -> deny
local approval missing -> deny
TTL expired -> deny
idempotency key missing -> deny
rollback plan missing -> deny
risk class R4/R5 requested -> deny
ChatGPT-only approval -> deny
2. Decision record bootstrap

Need DECISION_RECORD.md because quality gates already reference it.

Minimum entries:

DR-0001: Scope model and live-disabled baseline
DR-0002: Human local approval as final authority
DR-0003: R4/R5 not enabled
DR-0004: ChatGPT cannot be final approver
DR-0005: Dry-run before live execution
3. Dirty state handling rule

Need a rule that permission-relevant dirty files must be classified before audit acceptance.

For this run:

drafts/hermes-local-execution-worker.service.draft

should be classified as one of:

benign draft
permission-relevant pending change
must-review before live
must-remove before merge
4. Artifact secret scanning

Need scanning beyond committed source.

Scan targets should include:

tmp/
runs/
queues/
logs/
drafts/
worker output
recovery artifacts
5. Dry-run output contract

Dry-run should produce a structured preview:

intended action
scope requested
risk class
files touched
external side effects
required approvals
rollback plan
irreversible operations
deny reason if blocked
6. Recovery quarantine contract

Queue and bridge recovery should preserve evidence but prevent accidental reuse.

Recommended states:

active
quarantined
redacted
manually-approved-for-replay
discarded
Recommended Minimal Changes
Change 1: Create DECISION_RECORD.md

Classification: Grounded
Priority: High
Type: docs/control-plane

Create the missing decision record referenced by quality gates.

Minimum content:

Markdown
# Decision Record

## DR-0001: Live execution disabled by default
Decision: live scope remains `allowed: []` and `not_enabled`.
Reason: prevent external side effects before full gate validation exists.

## DR-0002: Human local approval required
Decision: ChatGPT cannot be final approver.
Reason: browser-mediated or remote model approval is not sufficient for local execution authority.

## DR-0003: R4/R5 not enabled
Decision: external side effect and private content risk classes remain disabled.
Reason: current system is not yet validated for those risk levels.

## DR-0004: Dry-run before live
Decision: any future live path must require dry-run evidence and rollback plan.
Reason: approval must be based on previewable impact.
Change 2: Add live-gate deny tests

Classification: Inferred
Priority: High
Type: tests/validator

Add tests that intentionally omit each live gate and assert denial.

Do not test successful live execution yet. First prove deny behavior.

Change 3: Add dirty-state audit checklist

Classification: Grounded
Priority: Medium
Type: docs/control-plane

Add a checklist item:

Permission-relevant dirty files must be reviewed before PASS.

For this run, the dirty systemd draft should prevent a clean PASS unless explicitly classified.

Change 4: Extend secret scanning to artifacts

Classification: Inferred
Priority: Medium
Type: script/validator

Extend leakage scan from committed source to generated runtime artifacts.

At minimum:

tmp/
runs/
logs/
queue/
drafts/
Change 5: Require rollback plan in dry-run output

Classification: Inferred
Priority: Medium
Type: executor contract

Dry-run should not merely say “would execute.” It should show failure recovery.

Required fields:

rollback_available: true/false
rollback_steps:
irreversible_operations:
operator_confirmation_required:
Change 6: Quarantine recovered queue files

Classification: Inferred
Priority: Medium
Type: recovery contract

Queue recovery should preserve broken files, but recovered files should not be replayable until manually re-approved.

Findings That Need Code-Level Verification

These should be assigned to the code-level risk reviewer.

1. local_execution_worker gate enforcement

Question: does the worker enforce all 13 live gates, or only rely on upstream docs/config?

Need verification:

where live requests enter
where approval is checked
where TTL is checked
where idempotency key is checked
where rollback plan is checked
whether failure defaults to deny
2. approval_queue idempotency

Question: can an approval be replayed, duplicated, or reused after TTL expiry?

Need verification:

idempotency key generation
idempotency key storage
duplicate handling
expired approval handling
queue recovery behavior
3. Systemd worker draft risk

Question: does drafts/hermes-local-execution-worker.service.draft introduce permission, environment, restart, or working-directory risk?

Need verification:

ExecStart
WorkingDirectory
Environment / EnvironmentFile
Restart policy
User
Group
file permissions
log destination
4. Secret handling coverage

Question: does the scan cover transient artifacts or only committed files?

Need verification:

tmp/
logs/
runs/
queue files
worker stdout/stderr
.env-like files
browser/session artifacts
5. Recovery replay safety

Question: can broken queue files be accidentally replayed after recovery?

Need verification:

recovered file state
replay path
manual approval requirement
redaction behavior
stale approval invalidation
6. R4/R5 enforcement

Question: are R4/R5 only documented as disabled, or does runtime reject them?

Need verification:

risk class parser
risk-to-scope mapping
deny behavior for R4/R5
test coverage for disabled classes
Findings Rejected as Ungrounded

These should not be accepted unless more evidence is provided.

1. “The system is safe for live execution”

Rejected.

Reason: live scope is disabled and several enforcement points remain unknown. The architecture is conservative, but live safety is not proven.

2. “The 13 live checks are implemented”

Rejected.

Reason: the checks are documented in repo-reader output, but runtime enforcement was not proven.

3. “Secret handling is complete”

Rejected.

Reason: committed-source secret handling appears strong, but transient artifacts and path secret rotation remain unknown.

4. “Recovery is safe”

Rejected.

Reason: recovery behavior is partially described, but replay safety, stale approvals, and redaction behavior are not verified.

5. “The dirty systemd draft is harmless”

Rejected.

Reason: the dirty file is permission-relevant by category and must be reviewed before classification.

Architecture Verdict

Status: PASS_WITH_NOTES

Reason:

The documented permission model is strong enough for a first audit baseline. Live execution is disabled, high-risk classes are not enabled, ChatGPT is explicitly prevented from final approval, and human local authority is preserved.

However, this should not be marked clean PASS because:

DECISION_RECORD.md is missing despite being referenced.

A permission-relevant systemd worker draft is dirty.

Runtime enforcement of the documented live gates is not yet verified.

Secret handling coverage for transient artifacts is unknown.

Recovery replay safety is unknown.

Next Recommended Experiment

Run hermes-perm-audit-002 as a deny-path implementation audit.

Goal:

Verify that documented permission boundaries are enforced by executable tests or validators.

Scope:

read-only + test/validator review
no live execution
no source modification unless separately approved

Required evidence:

1. deny test for missing LIVE_ENABLED
2. deny test for missing local approval
3. deny test for expired TTL
4. deny test for missing idempotency key
5. deny test for missing rollback plan
6. deny test for R4/R5 request
7. deny test for ChatGPT-only approval

Recommended next artifact to create in Token Furnace Lab:

knowledge/decisions/DR-0001-hermes-permission-baseline.md
knowledge/evaluator-rules/live-gate-deny-checks.md
knowledge/failures/permission-policy-runtime-drift.md"
