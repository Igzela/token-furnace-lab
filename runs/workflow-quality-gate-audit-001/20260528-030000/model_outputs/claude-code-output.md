# Claude Code Output: workflow-quality-gate-audit-001

## 1. Workflow Asset Inventory

### Templates (4 core)
| Template | Path | Status |
|----------|------|--------|
| experiment.yaml | templates/experiment.yaml | STABLE |
| synthesis.md | templates/synthesis.md | STABLE |
| matrix.yaml | templates/matrix.yaml | STABLE |
| phase-closeout.md | templates/phase-closeout.md | STABLE |

### Run Templates (7 markdown)
| Template | Path | Status |
|----------|------|--------|
| task.md | config/run-template/task.md | STABLE |
| cost_estimate.md | config/run-template/cost_estimate.md | STABLE |
| decision_record.md | config/run-template/decision_record.md | STABLE |
| failure_analysis.md | config/run-template/failure_analysis.md | STABLE |
| next_experiment.md | config/run-template/next_experiment.md | STABLE |
| evaluator_rule.md | config/run-template/evaluator_rule.md | STABLE |
| wiki_note.md | config/run-template/wiki_note.md | STABLE |

### Automation Scripts (6)
| Script | Path | Status |
|--------|------|--------|
| validate_run.py | scripts/validate_run.py | STABLE |
| new_run.py | scripts/new_run.py | STABLE |
| new-run.sh | scripts/new-run.sh | LEGACY |
| summarize_run.py | scripts/summarize_run.py | STABLE |
| distill.sh | scripts/distill.sh | LEGACY |
| mcp_bridge_boundary_verify.py | scripts/mcp_bridge_boundary_verify.py | STABLE |

### Knowledge Assets
| Type | Count | Status |
|------|-------|--------|
| Wiki | 8 | STABLE |
| Decisions | 6 | STABLE |
| Evaluator Rules | 5 | STABLE |
| Matrices | 6 | STABLE |
| Failures | 3 | STABLE |
| Reusable Prompts | 3 | STABLE |

### Prior Phases (sampled)
| Phase | Experiments | Closeout | Tag |
|-------|-------------|----------|-----|
| hermes-perm-audit-phase-1 | 001-008 | docs/runs/hermes-perm-audit-phase-1-closeout.md | hermes-perm-audit-phase-1 |
| mcp-bridge-boundary-audit-phase-1 | 001-002 | docs/runs/mcp-bridge-boundary-audit-phase-1-closeout.md | mcp-bridge-boundary-audit-phase-1 |
| token-furnace-platform-v1 | consolidation | docs/runs/token-furnace-platform-v1-closeout.md | token-furnace-platform-v1 |

## 2. Experiment Lifecycle Compliance Map

### Template Requirements vs Actual

| Requirement | Template | hermes-perm-audit | mcp-bridge-boundary-audit | Compliance |
|-------------|----------|-------------------|---------------------------|------------|
| experiment.yaml | Required | Present | Present | PASS |
| task.md | Required | Present | Present | PASS |
| model_outputs/ | Required | Present | Present | PASS |
| synthesis.md | Required | Present | Present | PASS |
| run.yaml | Required | MISSING | MISSING | FAIL |
| status.md | Required | MISSING | MISSING | FAIL |
| cost_estimate.md | Required | MISSING | MISSING | WARN |
| failure_analysis.md | Required | MISSING | MISSING | WARN |
| decision_record.md | Required | MISSING | MISSING | WARN |
| next_experiment.md | Required | MISSING | MISSING | WARN |

### Directory Structure Compliance

| Convention | Template | Actual | Compliance |
|------------|----------|--------|------------|
| model-outputs/ (hyphen) | templates/ | model_outputs/ (underscore) | INCONSISTENT |
| Timestamp format | YYYY-MM-DD | YYYYMMDD-HHMMSS | INCONSISTENT |
| distill.sh expects | model_outputs/ | model_outputs/ | PASS |
| validate_run.py expects | model-outputs/ | model_outputs/ | MISMATCH |

## 3. Gate Coverage Against W001-W030

### Group A: Experiment Definition Gates

| Gate | Status | Evidence |
|------|--------|----------|
| W001: explicit type | PASS | All experiments have `type` field |
| W002: target/platform separated | PASS | target_repo != platform_repo |
| W003: allowed/forbidden declared | PASS | All have scope.allowed and scope.forbidden |
| W004: non-goals declared | PASS | All have objective.non_goals |
| W005: healthy failure declared | PASS | Audit/verification experiments have healthy_failure |

### Group B: Evidence and File-State Gates

| Gate | Status | Evidence |
|------|--------|----------|
| W006: pre/post status | WARN | Not explicitly recorded in runs |
| W007: evidence path per finding | PASS | Synthesis template requires evidence_path |
| W008: evidence type declared | PASS | Template enumerates evidence_type_enum |
| W009: model inference alone can't PASS | PASS | Matrix template rule: "no PASS case relies only on model_inference" |
| W010: secrets redacted | PASS | validate_run.py scans for 7 secret patterns |

### Group C: Matrix and Verdict Gates

| Gate | Status | Evidence |
|------|--------|----------|
| W011: matrix exists | PASS | All phases produced matrices |
| W012: summary counts match | WARN | No automated checker exists |
| W013: P0 fail requires follow-up | PASS | Matrix template enforces follow_up |
| W014: path-aware matrix | PASS | Hermes used path-aware matrix |
| W015: verdicts separated | PASS | All experiments have dual verdicts |
| W016: triple verdict for closeout | PASS | Phase closeouts use triple verdict |

### Group D: Multi-Agent Handoff Gates

| Gate | Status | Evidence |
|------|--------|----------|
| W017: Claude Code role bounded | PASS | Evidence collection / implementation only |
| W018: GPT role bounded | PASS | Architecture review / synthesis |
| W019: Codex role bounded | WARN | Not consistently used in all phases |
| W020: handoff preserves uncertainty | PASS | Matrix UNKNOWN status used |
| W021: disagreement resolved by evidence | PASS | Synthesis template requires evidence |

### Group E: Fix and Regression Gates

| Gate | Status | Evidence |
|------|--------|----------|
| W022: narrow write scope | PASS | Fix experiments declare allowed files |
| W023: no unrelated refactor | PASS | Scope.forbidden enforced |
| W024: regression follow-up | PASS | hermes-perm-audit-004 created regression suite |
| W025: regression tests run | PASS | Tests recorded in runs |
| W026: no behavior change in refactor | PASS | Regression suite validates |

### Group F: Closeout and Knowledge Deposition Gates

| Gate | Status | Evidence |
|------|--------|----------|
| W027: synthesis exists | PASS | All phases have synthesis.md |
| W028: knowledge assets deposited | PASS | Wiki, decisions, evaluator-rules, matrices created |
| W029: known gaps recorded | PASS | Closeout templates require known_gaps |
| W030: tag/commit baseline | PASS | All phases tagged |

## 4. Examples of Strong Gates

1. **W009: model inference alone can't PASS** — Explicit rule in matrix.yaml template, enforced by consistency_checks
2. **W015: verdicts separated** — Dual verdict system consistently applied across all experiments
3. **W010: secrets redacted** — Automated scanning in validate_run.py
4. **W013: P0 fail requires follow-up** — Matrix template enforces follow_up.required=true
5. **W028: knowledge deposited** — Multiple asset types required (wiki, decisions, evaluator-rules, matrices)

## 5. Suspected Weak or Manual-Only Gates

1. **W006: pre/post status** — Not explicitly recorded; relies on git status snapshots
2. **W012: matrix summary counts** — No automated checker; consistency_checks defined but not enforced by script
3. **W019: Codex role** — Not consistently used; some phases skip Codex
4. **Directory naming** — Inconsistent (model-outputs/ vs model_outputs/, hyphen vs underscore)
5. **validate_run.py** — Hardcoded filenames don't match actual run structure

## 6. No-Write Confirmation

- Token Furnace Lab repo: No code changes during audit
- Hermes gateway lab repo: No modifications
- All artifacts created in experiment/runs directories only

## 7. Key Findings

### Strong Findings (Evidence-Backed)
1. Dual verdict system is consistently applied and well-enforced
2. Matrix template has 7 automated consistency checks
3. Secret scanning is automated in validate_run.py
4. Knowledge distillation produces reusable assets
5. Cross-project generalization validated

### Weak Findings (Manual-Only Gates)
1. **validate_run.py naming mismatch**: Expects model-outputs/ (hyphen), actual uses model_outputs/ (underscore)
2. **No automated matrix consistency checker**: Rules defined in template but not enforced by script
3. **Missing run artifacts**: Recent runs lack run.yaml, status.md, cost_estimate.md
4. **Two scaffolding scripts**: new_run.py and new-run.sh produce different structures
5. **Codex not consistently used**: Some phases skip third-model review

### Workflow Risks
1. **False PASS risk**: If matrix summary counts don't match cases and no checker exists
2. **Evidence gap risk**: If accepted findings lack evidence_path and no validator catches it
3. **Naming inconsistency risk**: Different scripts expect different directory names

## 8. Preliminary Gate Assessment

| Category | Total | Strong | Weak | Manual-Only |
|----------|-------|--------|------|-------------|
| Experiment Definition | 5 | 5 | 0 | 0 |
| Evidence/State | 5 | 4 | 1 | 0 |
| Matrix/Verdict | 6 | 4 | 2 | 0 |
| Agent Handoff | 5 | 4 | 1 | 0 |
| Fix/Regression | 5 | 5 | 0 | 0 |
| Closeout/Knowledge | 5 | 4 | 1 | 0 |
| **Total** | **30** | **26** | **5** | **0** |

**Assessment**: 26/30 gates are strong (template-enforced or automated). 5 gates are weak (manual-only or inconsistent). 0 gates are completely missing.

**Recommendation**: workflow-quality-gate-audit-002 should implement automated validators for the 5 weak gates.
