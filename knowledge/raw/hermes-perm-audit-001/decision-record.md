# Decision Record: hermes-perm-audit-001

Generated: 2026-05-27T18:45:00

## Accepted Findings

### DR-0001: Worker gate function diverges from canonical (Critical)
- **Source**: Codex Finding 1-7, GPT Risk 1
- **Decision**: ACCEPTED as critical bug
- **Evidence**: `check_worker_gates` in `local_execution_worker.py` omits 6+ required gates that `local_marker_executor.check_gates` enforces
- **Action**: hermes-gateway-lab must unify gate enforcement before any live execution path is enabled
- **Priority**: P0 - blocks live execution

### DR-0002: Missing DECISION_RECORD.md (Medium)
- **Source**: GPT Risk 2, Claude Code Observation #6
- **Decision**: ACCEPTED
- **Evidence**: Quality gates reference it; file does not exist
- **Action**: Create with initial entries covering scope model, disabled live mode, human approval authority
- **Priority**: P1 - governance gap

### DR-0003: Dirty systemd worker draft (Medium)
- **Source**: GPT Risk 3, Claude Code Observation #7
- **Decision**: ACCEPTED - classify before audit-stable
- **Evidence**: `drafts/hermes-local-execution-worker.service.draft` is modified and uncommitted
- **Action**: Review, classify as benign/permission-relevant/must-remove, then commit or discard
- **Priority**: P2 - audit hygiene

### DR-0004: Approval re-approval replay (High)
- **Source**: Codex Finding 8
- **Decision**: ACCEPTED
- **Evidence**: `transition()` does not block `approved_local -> approved_local`
- **Action**: Add terminal state check or idempotency guard
- **Priority**: P1 - state machine integrity

### DR-0005: No task-level TTL (Medium)
- **Source**: Codex Finding 10, GPT Risk 5
- **Decision**: ACCEPTED
- **Evidence**: `approve_task` stores `approval_timestamp` but no `expires_at`
- **Action**: Add TTL constant and validation
- **Priority**: P2 - staleness risk

### DR-0006: Secret handling in runtime artifacts (Medium)
- **Source**: GPT Risk 6, Codex Findings 12/14, Claude Code Suggestion #3
- **Decision**: ACCEPTED
- **Evidence**: Audit log captures unsanitized reason text; reliability monitor captures unsanitized command output
- **Action**: Extend `sanitize_text` to scrub secrets; redact tailscale URLs in reliability reports
- **Priority**: P2 - data hygiene

## Rejected Findings

### DR-R001: "Recovery replay is unsafe" (GPT Risk 7)
- **Decision**: REJECTED as overstated
- **Reason**: Codex confirmed atomic writes + arm gate + state machine make accidental replay unlikely. Schema validation on load would be a nice-to-have but is not a blocking risk.

### DR-R002: "Systemd service target is wrong" (Codex Finding 15)
- **Decision**: REJECTED - draft only
- **Reason**: File is a draft, not deployed. Target selection is a deployment concern, not a security risk.

### DR-R003: "Double save in create_task" (Codex Finding 18)
- **Decision**: REJECTED - not a bug
- **Reason**: Double save is intentional for data consistency (task + audit event). Minor I/O cost is acceptable.

## Verdict

**Experiment Status**: COMPLETE
**Overall Risk Assessment**: The hermes-gateway-lab permission architecture is well-designed but has a critical implementation gap: the worker daemon's gate function diverges from the canonical gate function. This must be resolved before any live execution path is enabled.

**Next Steps**:
1. Create `knowledge/decisions/DR-0001-hermes-permission-baseline.md`
2. Create `knowledge/evaluator-rules/live-gate-deny-checks.md`
3. Create `knowledge/failures/permission-policy-runtime-drift.md`
4. Plan hermes-perm-audit-002 (deny-path implementation audit)
