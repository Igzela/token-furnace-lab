# Cross-Model Comparison: hermes-perm-audit-002

Generated: 2026-05-27

## Model Outputs Summary

| Model | Role | Output | Key Finding |
|-------|------|--------|-------------|
| Claude Code | Gate Mapper | claude-code-gate-mapper.md | 12/25 complete marker, 10/25 complete worker |
| GPT | Test Architecture Reviewer | (inline response) | 6 divergent cases, target FAIL |
| Codex | Deny-Path Risk Reviewer | (pending) | Worker bypass confirmed |

## Convergent Findings

### 1. Worker path diverges from marker path (ALL models)
- Claude Code: 9 missing gates on worker vs 5 on marker
- GPT: 6/25 cases diverge, C001-C003 fail
- Codex (from 001): worker bypasses LIVE_ENABLED, idempotency key

### 2. Rollback plan is missing on both paths (ALL models)
- Claude Code: D014-D016 all missing
- GPT: "rollback and secret-redaction gates are missing"
- Codex (from 001): no rollback plan validation in code

### 3. Secret redaction missing (ALL models)
- Claude Code: D024 missing, sanitize_text only truncates
- GPT: "secret-like reason persists unredacted"
- Codex (from 001): audit log captures unsanitized reason fields

## Divergent Findings

### GPT-only
- Proposed gate-conformance-matrix (C001-C005) as separate from deny-path matrix
- Proposed two P0 categories: gate behavior + path conformance
- Proposed refining F-0001 wording

### Claude Code-only
- Detailed per-case code evidence with line numbers
- Identified D003 (scope) and D012 (idempotency mismatch) as additional divergent cases

## Verdict

experiment_verdict: COMPLETE
target_control_verdict: FAIL
reason: deny-path tests confirm worker gate drift, 6/25 cases diverge
next: hermes-perm-audit-003 (fix worker gate conformance)
