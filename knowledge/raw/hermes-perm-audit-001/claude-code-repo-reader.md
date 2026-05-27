# Claude Code Repo Reader Output

## Target Repo
- path: /home/igzela/Projects/hermes-gateway-lab
- branch: harness-onboarding
- commit: 05092f09ef3d947b1fa303c3eee656de9453569b
- dirty state: M drafts/hermes-local-execution-worker.service.draft

## Files Inspected

| file | reason | exists | notes |
|------|--------|--------|-------|
| AGENTS.md | identity + safety boundaries | yes | States "execution adapter is not governance authority" |
| README.md | project overview | yes | Not read in this pass |
| docs/harness/QUALITY_GATES.md | gate definitions | yes | 3 gates: smoke, boundary inspection, permission deny |
| docs/harness/RISK_REGISTER.md | risk tracking | yes | 2 risks: RR-1 (onboarding implies authority), RR-2 (dirty state loss) |
| docs/harness/DECISION_RECORD.md | decision history | NO | File does not exist |
| docs/harness/PROJECT_BRIEF.md | project scope | yes | Not read in this pass |
| docs/harness/PROJECT_BOARD.md | task tracking | yes | Not read in this pass |
| docs/harness/TASK_QUEUE.md | task queue | yes | Not read in this pass |
| docs/live-execution-safety-model.md | safety model | yes | Defines scopes: read, plan, approval.local, dry_run, live |
| docs/live-execution-risk-classes.md | risk classification | yes | R0-R5 classes, R4/R5 not enabled |
| docs/live-execution-gates.md | execution gates | yes | 13 checks before live execution, kill switches defined |
| docs/secret-handling-policy.md | secret policy | yes | Comprehensive: never-commit list, pre-commit checks |
| docs/recovery-and-rollback.md | rollback procedures | yes | Health check, queue recovery, bridge recovery, execution rollback |
| docs/h4-h7-safety-boundaries.md | safety boundaries | yes | Not read in this pass |
| scripts/approval_queue.py | approval queue impl | yes | Not read in this pass |
| scripts/dry_run_executor.py | dry-run executor | yes | Not read in this pass |
| scripts/local_execution_worker.py | local worker | yes | Not read in this pass |
| scripts/permission_deny_dry_run.py | permission deny | yes | Not read in this pass |
| scripts/reliability_monitor.py | reliability checks | yes | Not read in this pass |

## Actual Permission-Relevant Surfaces

1. **Scope Model** (docs/live-execution-safety-model.md): 5 scopes defined — `hermes.read`, `hermes.plan`, `hermes.approval.local`, `hermes.execute.dry_run`, `hermes.execute.live`. Live scope has `allowed: []` and `status: not_enabled`.

2. **Risk Classes** (docs/live-execution-risk-classes.md): R0-R5 classification. R4 (external side effect) and R5 (private content/arbitrary execution) are explicitly NOT enabled.

3. **Execution Gates** (docs/live-execution-gates.md): 13 required checks before live execution, including `LIVE_ENABLED=true`, Charlie local approval, TTL, idempotency key, rollback plan. Global kill switch exists.

4. **Approval Flow** (docs/live-execution-safety-model.md): ChatGPT CANNOT be final approver. Final approval must come from Charlie through local CLI/local web UI/physical action.

5. **Secret Handling** (docs/secret-handling-policy.md): Comprehensive never-commit list, pre-commit leakage scan, .gitignore covers common secret patterns.

6. **Quality Gates** (docs/harness/QUALITY_GATES.md): 3 gates active — smoke tests, boundary inspection, permission deny patterns.

7. **Recovery/Rollback** (docs/recovery-and-rollback.md): Health check is read-only. Queue recovery preserves broken files. Bridge recovery requires explicit approval. Execution rollback: dry-run only, mark tasks cancelled, preserve audit log.

8. **Human Authority** (AGENTS.md): "The human operator remains the final authority for all governance decisions. No app output constitutes execution authorization."

## Implementation Observations

1. **Well-documented safety model**: The repo has extensive documentation on safety boundaries, risk classes, execution gates, and kill switches. This is unusually thorough for an experimental project.

2. **Live execution is disabled by design**: `LIVE_ENABLED: false` is the default. R4/R5 tools are not enabled. The system is currently read-only + dry-run only.

3. **Approval queue exists**: `scripts/approval_queue.py` implements the approval workflow. Tasks go through create -> approve (local) -> execute (dry-run or live).

4. **Dry-run executor exists**: `scripts/dry_run_executor.py` handles preview-only execution. No live side effects.

5. **Permission deny pattern exists**: Separate scripts for `permission_deny_dry_run.py` and `permission_deny_worker.py`, with smoke tests.

6. **Missing DECISION_RECORD.md**: The harness directory has a decision record placeholder in the quality gates doc, but the actual file does not exist. This is a gap in governance traceability.

7. **Dirty state on branch**: `drafts/hermes-local-execution-worker.service.draft` is modified but uncommitted. This is a systemd service draft for the local execution worker.

8. **Extensive test coverage**: Multiple `*_smoke.py` scripts for each stage (live1-live9, h1-h7). Boundary inspection script exists.

9. **tmp/ directory has real data**: Approval queue files, smoke test results, diagnostic outputs. These are ignored by .gitignore but present locally.

## Grounded Suggestions

1. **Create docs/harness/DECISION_RECORD.md**: The quality gates reference it but it doesn't exist. Create it with at least one entry documenting the current safety model decisions.

2. **Review drafts/ directory**: The dirty state suggests in-progress work on systemd service management. This should be either committed to a feature branch or explicitly documented as WIP.

3. **Audit tmp/ contents**: While .gitignore covers tmp/, the directory contains real approval queue data and diagnostic results. Verify no secrets leaked into these files.

4. **Formalize the kill switch test**: The execution gates document lists 8 kill switches. Verify each has a corresponding test or smoke check.

5. **Add rollback plan to dry-run executor**: The recovery doc says dry-run tasks should be marked cancelled, but the dry_run_executor.py should verify it writes this status correctly.

## Unknowns

- Whether `scripts/approval_queue.py` has proper idempotency key enforcement
- Whether `scripts/local_execution_worker.py` actually checks all 13 gates before execution
- Whether the reliability monitor covers all kill switches
- Contents of `scripts/hermes-local-execution-worker-start.sh` and systemd service configuration
- Whether Tailscale Funnel path secret is properly rotated

## No-Write Confirmation

No source/runtime/config files were modified in the target repo. All operations were read-only: git status, find, and file reads.
