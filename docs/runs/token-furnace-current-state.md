# Token Furnace Lab — Current State Index

## Metadata

- Generated: 2026-05-28
- Maturity: L4-AUTONOMOUS
- Total Phases Completed: 5

## Completed Phases

| Phase | Target | Tag | Verdict | Commit |
|-------|--------|-----|---------|--------|
| Phase 1 | Hermes permission audit (001-008) | hermes-perm-audit-phase-1 | COMPLETE/PASS | 3e1b004 |
| Phase 2 | MCP bridge tool-boundary audit | mcp-bridge-boundary-audit-phase-1 | COMPLETE/PASS/PASS | a9615de |
| Phase 3 | Workflow quality-gate audit | workflow-quality-gate-audit-phase-1 | COMPLETE/PASS_WITH_NOTES/PASS | 6a7df2d |
| Phase 4 | PDF-to-algorithm extraction benchmark | pdf-to-algorithm-benchmark-phase-1 | COMPLETE/PASS_WITH_NOTES/PASS | 0e46c71 |
| Phase 5 | Multi-agent orchestration | multi-agent-orchestration | COMPLETE/PASS | 4313909 |
| Phase 6 | Schema enforcement + failure injection | orchestration-003 | COMPLETE/PASS (10/10) | eec471a |
| Phase 7 | Real multi-model cross-audit | orchestration-004 | COMPLETE/PASS_WITH_NOTES | 11bd806 |
| Phase 8 | Review fusion + multi-reviewer gate | orchestration-005 | COMPLETE/PASS | 95f11b6 |
| Phase 9 | Fused repair execution benchmark | orchestration-006 | COMPLETE/ACCEPT | 8074c82 |
| Phase 10 | Multi-worktree parallel dispatch | orchestration-007 | COMPLETE/PASS | 4a2b85e |
| Phase 11 | Confidence & escalation calibration | orchestration-008 | COMPLETE/PASS | 92cb116 |
| Phase 12 | Outcome memory + policy tuning loop | orchestration-009 | COMPLETE/PASS | 180e938 |
| Phase 13 | Safe policy application engine | orchestration-010 | COMPLETE/PASS | 9312000 |
| Phase 14 | Adaptive task routing | orchestration-011 | COMPLETE/PASS | 2071a08 |
| Phase 15 | Self-evaluation benchmark | orchestration-012 | COMPLETE/PASS | pending |

## Platform Consolidation

| Milestone | Tag | Verdict | Commit |
|-----------|-----|---------|--------|
| Platform v1 | token-furnace-platform-v1 | L3-VALIDATED | 9a0c4b8 |
| Methodology v1 | token-furnace-methodology-v1 | ACCEPTED | 6100a6c |
| Orchestrator v1 | multi-agent-orchestration | L4-AUTONOMOUS | 4313909 |

## Current Maturity

**L5-ADAPTIVE**: Multi-agent orchestration with adaptive routing, outcome memory, policy application, and self-evaluation benchmark.

Capabilities validated:
- Multi-model cross-audit (GPT + Claude Code + Codex)
- Structured knowledge distillation (decisions, evaluator-rules, failures, wiki, matrices)
- Automated workflow validators (3 scripts: state machine, review artifact, scope diff)
- Canonical run layout with legacy compatibility
- 30-case workflow quality-gate matrix
- 16-case MCP bridge boundary matrix
- 8-case hermes permission matrix
- PDF-to-algorithm extraction pipeline (Claude Code → GPT → quality assessment)
- **Multi-agent orchestrator** (queue/mock/command/bridge modes)
- **Deterministic quality gate** (score + verdict + validator errors + evidence validation)
- **Budget ledger** (iterations, wall time, per-round tracking)
- **Idempotent resume** (run_state.json survives interruption)
- **Rollback policy** (worktree quarantine on failure)
- **Closeout generator** (final_verdict.yaml + synthesis.md)
- **Agent bridge** (Claude Code CLI wrapper for automated execution)
- **E2E test**: queue → subagent → gate → ACCEPT (82/100)
- **Real cross-audit**: Claude reviews model, GPT cross-reviews Claude's artifact (orchestration-004)
- **JSON-block parsing**: parse_review() and validators handle structured JSON output from agents
- **Review fusion**: Merge multiple reviewer outputs into fused gate decision (review_fusion.py)
- **Fused gate**: evaluate_fused_gate() applies priority rules across merged findings
- **Confidence calibration**: 5-component weighted scoring (reviewer_confidence, evidence_quality, validator_agreement, cross_reviewer_convergence, repair_history)
- **Decision policy**: Priority-ordered ACCEPT/REPAIR/ESCALATE/REJECT based on conditions
- **Timeout classifier**: Heuristic-based classification of timeout transitions with negation handling
- **Escalation report**: Structured report for human decision when gate outputs ESCALATE
- **Outcome memory**: Machine-readable run history (outcome_memory.jsonl) with 20 fields per outcome
- **Learning extractor**: orchestrator_learn.py — ingest, suggest, stats, check-self-modify
- **Policy registry**: 10 active policies + 4 blocked, with risk-level classification
- **Self-modification gate**: Auto-tighten allowed, auto-loosen blocked without human approval

## Reusable Templates

- `templates/experiment.yaml` — Experiment definition
- `templates/synthesis.md` — Synthesis report
- `templates/matrix.yaml` — Conformance/risk matrix
- `templates/phase-closeout.md` — Phase closeout
- `templates/agent_contract.yaml` — Agent task contract

## Runnable Validators

```bash
# Run layout validation
python3 scripts/validate_run.py runs/<experiment>/<timestamp>/

# Matrix consistency
python3 scripts/validate_matrix_consistency.py knowledge/matrices/<matrix>.yaml

# Synthesis evidence
python3 scripts/validate_synthesis_evidence.py runs/<experiment>/<timestamp>/

# Orchestrator validation
python3 scripts/tf_orchestrator.py validate <artifact> --type <state_machine|review>
python3 scripts/tf_orchestrator.py gate <run_dir> <round>
python3 scripts/tf_orchestrator.py closeout <run_dir>

# Full orchestration run
python3 scripts/tf_orchestrator.py run <task.yaml> --mode <mock|queue|bridge>
```

## Why PASS_WITH_NOTES (Not Strict PASS)

1. **Legacy layout still supported**: `model-outputs/` (hyphen) works with warnings, not errors
2. **Optional files not enforced**: `run.yaml`, `status.md` generate warnings, not failures
3. **Codex role is contract-based**: Not globally mandatory, only checked if declared
4. **No CI/CD integration**: Validators run locally, not in pipeline

## Phase 5 Candidates

1. **Small DC-link FOC source acquisition** — Find papers directly covering electrolytic-capacitorless or small-DC-link PMSM sensorless FOC
2. **OpenClaw runtime permission audit** — Another agent security target
3. **Public exposure / tunnel security audit** — Network boundary testing

**Recommended**: Small DC-link FOC source acquisition (GPT recommendation)

## Current Active Research Handoff

- Canonical cloud handoff branch: `main`
- Research branch retained: `exp/hermes-perm-audit-001`
- Active thread: `small-dc-link-foc-derivation`
- Latest sealed run: `runs/small-dc-link-foc-phase-e-001/20260528-130000`
- Latest run status: `PASS_WITH_NOTES` (72/100)
- New session entrypoint: `docs/SESSION_START_HERE.md`

Phase-e-001 runtime fault recovery model is complete. 12 states, 19 fault codes, 4 fault classes. GPT caught 7 major corrections (observer freeze, CONTROLLED_COAST split, Vdc derating formula, APD topology awareness, restart logic, hard-fault paths, retry policy). All corrections applied in v2. Next recommended: Phase A-004 Fixed-Point CPU/RAM Budget.

Coding agents must update this file, the active run status, and the relevant `knowledge/wiki/` page before committing any accepted experiment result.

Responsible coding agents may autonomously advance research tasks from run creation to committed handoff. They must finish or explicitly preserve any in-progress run visible in `git status`, record cross-audit before knowledge acceptance, run validators, update canonical docs, commit in English, and push the active branch when the tree contains only the intended changes.

## Tags

```bash
git tag hermes-perm-audit-phase-1
git tag mcp-bridge-boundary-audit-phase-1
git tag token-furnace-platform-v1
git tag token-furnace-methodology-v1
git tag workflow-quality-gate-audit-phase-1
git tag pdf-to-algorithm-benchmark-phase-1
```
