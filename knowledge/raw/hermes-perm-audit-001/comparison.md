# Cross-Model Comparison: hermes-perm-audit-001

Generated: 2026-05-27T18:45:00

## Model Outputs Summary

| Model | Role | Findings | High | Medium | Low | Verdict |
|-------|------|----------|------|--------|-----|---------|
| GPT-4 | Architect | 7 risks, 6 missing controls | 1 | 6 | 0 | PASS_WITH_NOTES |
| Claude Code | Repo Reader | 9 permission surfaces, 5 suggestions | 0 | 0 | 0 | N/A (inventory) |
| Codex | Risk Reviewer | 18 findings | 8 | 6 | 4 | N/A (code-level) |

## Convergent Findings (agreed by 2+ models)

### 1. Policy-to-runtime enforcement gap
- **GPT**: Risk 1 (High) - worker may not enforce all 13 gates
- **Codex**: Finding 1-7 (High) - confirmed: worker bypasses LIVE_ENABLED, idempotency, scope, TTL, rollback, audit writability
- **Claude Code**: Unknown #2 - "Whether local_execution_worker actually checks all 13 gates"
- **Status**: CONFIRMED by Codex code inspection. Worker has independent gate function diverging from canonical.

### 2. Missing DECISION_RECORD.md
- **GPT**: Risk 2 (Medium) - referenced by quality gates but doesn't exist
- **Claude Code**: Observation #6 - "Missing DECISION_RECORD.md: gap in governance traceability"
- **Status**: CONFIRMED. Both models independently identified this gap.

### 3. Dirty state risk
- **GPT**: Risk 3 (Medium) - systemd worker draft may hide operational drift
- **Claude Code**: Observation #7 - "Dirty state on branch: modified but uncommitted"
- **Status**: CONFIRMED. File is `drafts/hermes-local-execution-worker.service.draft`.

### 4. Secret handling coverage gaps
- **GPT**: Risk 6 (Medium) - may not cover transient paths
- **Codex**: Finding 12, 14 (Medium) - audit log captures sensitive text, reliability monitor unsanitized
- **Claude Code**: Suggestion #3 - "Audit tmp/ contents: verify no secrets leaked"
- **Status**: PARTIALLY CONFIRMED. Git coverage is good; runtime artifact leaks are the real risk.

### 5. Recovery replay safety
- **GPT**: Risk 7 (Medium) - may preserve unsafe artifacts
- **Codex**: Finding B (Low) - atomic writes reduce risk, but no schema validation
- **Status**: LOW RISK in practice. Arm gate + state machine provide adequate protection.

### 6. Kill switch testability
- **GPT**: Risk 4 (Medium) - described but not proven testable
- **Codex**: Finding 1 (High) - worker bypasses LIVE_ENABLED entirely
- **Status**: CONFIRMED BUG. Not just untested; the kill switch is missing from the worker path.

## Divergent Findings

### GPT-only (not confirmed by Codex)
- Risk 5 (rollback in dry-run): Codex did not find this as a code-level issue; dry-run executor has its own scope.

### Codex-only (not predicted by GPT)
- Finding 8 (re-approval replay): `transition()` allows `approved_local -> approved_local`. GPT did not identify this state machine gap.
- Finding 9 (hardcoded True values): Four gate values are assertions, not checks. GPT did not identify this.
- Finding 10 (no task-level TTL): Approval timestamps have no expiry. GPT mentioned TTL but not the missing `expires_at` field.
- Finding 11 (permission deny duplicate): `worker_execute_permission_deny` lacks duplicate guard.

### Claude Code-only (unique perspective)
- Suggestion #5 (rollback plan in dry-run executor): Not confirmed by either other model.
- Unknown #5 (Tailscale Funnel path secret rotation): Not investigated by other models.

## Cross-Validation Score

| Dimension | GPT | Claude Code | Codex | Agreement |
|-----------|-----|-------------|-------|-----------|
| Policy-runtime gap | High risk | Unknown | 8 findings | 2/3 confirmed |
| Decision record missing | Yes | Yes | N/A | 2/2 |
| Dirty state risk | Yes | Yes | N/A | 2/2 |
| Secret handling gaps | Yes | Yes | 2 findings | 3/3 |
| Recovery safety | Medium risk | N/A | Low risk | 1/2 |
| Kill switch broken | Untested | N/A | Missing code | 1/2 confirmed |

## Token Usage Estimate

| Model | Estimated Tokens | Notes |
|-------|-----------------|-------|
| GPT-4 | ~8,000 | Architect audit, single prompt |
| Claude Code | ~25,000 | Repo scan, 8 file reads, output generation |
| Codex | ~45,000 | 12 file reads, detailed code analysis |
| **Total** | **~78,000** | |
