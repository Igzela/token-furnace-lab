---

## Review: `knowledge/wiki/multi-agent-orchestration-architecture.md`

**Score: 40**
**Verdict: FAIL**
**Confidence: HIGH**

### Findings

- **[CRITICAL] Line count outdated**: Wiki claims `tf_orchestrator.py` is 833 lines. Actual: 1175 lines (+41%). The orchestrator has grown significantly with fuse and parallel subcommands.

- **[CRITICAL] 11 major subsystems completely undocumented**: The wiki makes no mention of: `adaptive_pipeline.py`, `adaptive_router.py`, `adversarial_review.py`, `confidence_calibrator.py`, `orchestrator_learn.py`, `policy_engine.py`, `review_fusion.py`, `task_profiler.py`, `quality_gate_runner.py`, `tf_agent_executor.py`, `worktree_manager.py`, `routing_outcome_update.py`. These represent orchestration-005 through 015 — the majority of the system's current capability.

- **[HIGH] Missing subcommands**: Wiki documents 4 subcommands (run, gate, validate, closeout). Actual has 6: **`fuse`** (review fusion from orchestration-005) and **`parallel`** (worktree parallel dispatch from orchestration-007) are missing.

- **[HIGH] "Single-threaded" limitation is false**: Limitation #2 says "subproblems execute sequentially (parallel dispatch would require async)". This was resolved in orchestration-007 — `run_parallel_dispatch()` exists at line 1056 and the `parallel` subcommand is registered. The limitation should be removed.

- **[HIGH] Validator table incomplete**: Lists 3 of 7 validators. Missing: `validate_run.py`, `validate_matrix_consistency.py`, `validate_synthesis_evidence.py`, `validate_artifact_schema.py` (exists in `orchestrator-quality-gate-policy.md` but not here).

- **[MEDIUM] Architecture diagram incomplete**: Shows basic pipeline only. Missing: adaptive routing layer (task_profiler → memory_matcher → routing_decision), adversarial three-way fusion (original + devil's advocate + defense), policy engine feedback loop, outcome memory.

- **[MEDIUM] Task YAML format missing fields**: No mention of `adversarial`, `adaptive`, `confidence`, or `routing` configuration keys that the newer scripts consume.

- **[LOW] E2E test results reference old run**: Only shows `runs/orchestration/20260528-101549/`. Orchestration-013 real benchmark and 015 expanded benchmark results are absent.

- **[LOW] Scope validator limitation still listed**: "Scope validator not integrated into main loop" — needs verification against current `run_orchestrate()`.

### Accuracy of Existing Content

The content that *is* present is largely accurate:
- Gate priority rules: correct (matches `orchestrator-quality-gate-policy.md`)
- Adapter pattern rationale: correct
- Validator/reviewer separation: correct
- Budget ledger and idempotent resume: correct
- Task YAML format (for basic use): correct

### Final Recommendation

**REPAIR** — The existing content is accurate but the page is frozen circa orchestration-004. It needs:

1. Update line count to 1175
2. Add `fuse` and `parallel` subcommands to the documented list
3. Remove "Single-threaded" from limitations (replaced by noting parallel dispatch exists)
4. Expand architecture diagram to show adaptive routing + adversarial review + policy engine
5. Document the 11+ new scripts in a Components section (or at minimum, add an "Extended Components" section)
6. Add 4 missing validators to the table
7. Add orchestration-013/015 benchmark results to E2E section

The `orchestrator-quality-gate-policy.md` page is more current but also needs updating to reference the adversarial review module's three-way fusion gate.
