# Orchestration Series — L6 Closeout

**Date**: TODO
**Maturity**: TODO_L6_ADVERSARIAL_VALIDATED
**Verdict**: TODO

## Timeline

| Run | Focus | Verdict | Commit |
|-----|-------|---------|--------|
| 001 | Basic pipeline | PASS (82/100) | — |
| 002 | Mock execution | PASS (100/100) | — |
| 003 | Schema enforcement + failure injection | PASS (10/10) | eec471a |
| 004 | Real multi-model cross-audit | PASS_WITH_NOTES (77/100) | 11bd806 |
| 005 | Review fusion + multi-reviewer gate | PASS | 95f11b6 |
| 006 | Fused repair execution benchmark | ACCEPT (92/90) | 8074c82 |
| 007 | Multi-worktree parallel dispatch | PASS | 4a2b85e |
| 008 | Confidence & escalation calibration | PASS | 92cb116 |
| 009 | Outcome memory + policy tuning loop | PASS | 180e938 |
| 010 | Safe policy application engine | PASS | 9312000 |
| 011 | Adaptive task routing | PASS | 2071a08 |
| 012 | Self-evaluation benchmark | PASS | 65ac8ad |
| 013 | Real execution + adaptive full pipeline | PASS (mock + real benchmark) | TODO |
| 014 | Multi-agent adversarial debate | TODO | TODO |
| 015 | Expanded benchmark suite (repair, validation, cross-audit at scale) | TODO | TODO |

## What L6 Adds on Top of L5

L5 validated the orchestrator's adaptive routing, policy engine, and self-evaluation using simulated execution. L6 closes the three remaining gaps that prevent the orchestrator from being considered adversarial-validated:

### 1. Real Execution at Scale (>=3 cases, real LLM calls)

Run 013 demonstrated end-to-end routing through real LLM execution (Claude) with gate validation and outcome learning. L6 requires this at scale:

- At least 3 distinct task types exercised through the real execution path (routing, execution, gate, repair loop, memory write).
- Latency and cost measured per case (not just correctness).
- Failure modes observed under real conditions (timeout, malformed output, partial response).
- Comparison: adaptive routing baseline vs. real execution outcome to validate that the self-evaluation benchmark (012) is a reliable proxy.

### 2. Multi-Agent Adversarial Debate

L5 had cross-audit (004) where GPT reviewed Claude's output, but no structured adversarial protocol. L6 introduces:

- **Devil's advocate agent**: Given a proposed decision (verdict, policy change, finding acceptance), actively constructs the strongest counter-argument.
- **Defense agent**: Responds to devil's advocate, provides evidence and reasoning for the original decision.
- **Presiding agent**: Evaluates both sides, issues final ruling with confidence score.
- Debate is logged as structured traces (position, evidence, counter-evidence, ruling).
- Pattern applies to high-stakes decisions: accepting a finding, changing a policy, overriding a gate verdict.

### 3. Expanded Benchmark Coverage

L5 benchmark (012) had 8 cases. L6 requires a broader set covering all pipeline dimensions:

- **Repair tasks**: Cases where the gate rejects output and the orchestrator must drive a repair loop to acceptance.
- **Validation tasks**: Cases with intentional schema violations, missing fields, or contradictory evidence.
- **Cross-audit tasks**: Multi-model review with real LLM calls, measuring delta detection (finding gaps between models).
- **Escalation tasks**: Cases where confidence is ambiguous and the orchestrator must escalate to human.
- **Latency-sensitive tasks**: Cases with tight timeouts to test the timeout classifier under real conditions.

## Capability Matrix

| # | Capability | Validated In | Evidence | L6 Status |
|---|-----------|-------------|----------|-----------|
| 1 | Pipeline execution (queue -> subagent -> gate) | 001-002 | E2E test 82/100 | Retained |
| 2 | Schema enforcement + failure injection | 003 | 10/10 cases | Retained |
| 3 | Real cross-audit (Claude + GPT) | 004 | GPT found 2 HIGH blocking | Extended to adversarial |
| 4 | Review fusion | 005 | findings union, blocking override | Retained |
| 5 | Closed-loop repair | 006 | 2 rounds to ACCEPT | Tested at scale |
| 6 | Parallel dispatch | 007 | 3/3 subproblems, ~30s wall | Retained |
| 7 | Confidence calibration | 008 | 9/9 calibration, 5-component | Retained |
| 8 | Decision policy | 008 | ACCEPT/REPAIR/ESCALATE/REJECT | Retained |
| 9 | Timeout classifier | 008 | Negation handling, fail-safe | Tested under real latency |
| 10 | Outcome memory | 009 | 10 runs, 13 lessons | Extended with real outcomes |
| 11 | Policy registry | 009-010 | 10 active + 4 blocked | Retained |
| 12 | Self-modification gate | 010 | Auto-tighten allowed | Retained |
| 13 | Regression testing | 010 | 4/4 tests pass | Extended with L6 regressions |
| 14 | Adaptive routing | 011 | 3-layer router, 8 task types | Validated at scale |
| 15 | Strategy selection | 011 | 7 strategies, 8 task types | Retained |
| 16 | Self-evaluation benchmark | 012 | +13.2 score, -83% missed | Proxy validated vs real |
| 17 | Real execution path | 013 | routing -> LLM -> gate -> learning | Extended to 3+ cases |
| 18 | **Adversarial debate protocol** | **014** | **TODO** | **New in L6** |
| 19 | **Devil's advocate + defense + presider** | **014** | **TODO** | **New in L6** |
| 20 | **Expanded benchmark (repair/validation/cross-audit/escalation/latency)** | **015** | **TODO** | **New in L6** |
| 21 | **Cost/latency measurement per real case** | **013** | **TODO** | **New in L6** |

## Validation Criteria

For L6 to pass, ALL of the following must be true:

### Real Execution (from 013 + 015)
- [ ] At least 3 task types executed through real LLM calls (not mock)
- [ ] Latency recorded for each case (P50, P95)
- [ ] Cost (tokens) recorded for each case
- [ ] At least 1 real failure mode observed and recovered (timeout, malformed output, or partial response)
- [ ] Self-evaluation benchmark score correlates with real execution outcome (delta < 15 points)

### Adversarial Debate (from 014)
- [ ] Devil's advocate successfully challenges at least 1 correct decision (tests counter-argument construction)
- [ ] Defense successfully defends at least 1 correct decision against invalid challenge
- [ ] Presiding agent overrules devil's advocate when challenge is weak (false positive rejection)
- [ ] Presiding agent sides with devil's advocate when challenge is valid (true positive detection)
- [ ] All debate exchanges logged as structured traces with position, evidence, ruling

### Expanded Benchmark (from 015)
- [ ] Repair loop tested with at least 2 rejection-then-repair-then-accept cases
- [ ] Validation tested with at least 1 schema-violation case and 1 missing-evidence case
- [ ] Cross-audit delta measured with at least 2 model pairs (Claude+GPT, Claude+Haiku or similar)
- [ ] Escalation tested with at least 1 ambiguous-confidence case
- [ ] Timeout classifier tested with at least 1 real-latency case

### Aggregate
- [ ] No false accepts (same as L5, maintained)
- [ ] No false rejections on clear PASS cases (new: ensure adversarial debate does not over-veto)
- [ ] Total benchmark cases >= 15 (8 from 012 + 7 new)

## Remaining Gaps (What L7 Would Cover)

1. **Production deployment** — No persistent service, no CLI UI, no auth, no logging infrastructure. L7 could explore lightweight service mode with health checks and structured logging.
2. **Auto-merge policy** — Policy engine suggests but does not auto-merge approved low-risk changes. L7 could add a safe auto-merge path with regression guard.
3. **Multi-agent memory sharing** — Agents do not share context across tasks beyond the orchestrator's outcome_memory. L7 could explore shared working memory or vector-store-backed context.
4. **Self-healing pipeline** — If a pipeline component fails (gate crashes, LLM times out repeatedly), the orchestrator does not reconfigure itself. L7 could add circuit-breaker and fallback routing.
5. **Cross-series knowledge transfer** — Orchestration findings are not systematically applied to the FOC derivation series. L7 could explore orchestrator-managed cross-domain task management.
6. **Continuous benchmark regression** — No mechanism to re-run benchmarks on schedule and detect score degradation over time. L7 could add a CI-like benchmark runner.
7. **Human-in-the-loop escalation UI** — Escalation goes to a human but there is no structured interface for receiving and responding to escalations.

## When to Resume

Resume orchestration expansion when:
- A production-like deployment need emerges (persistent service, multi-user orchestration)
- The FOC project reaches Phase D integration (orchestrator manages integration test suite)
- Cross-series orchestration is needed (FOC + permission audit + orchestration managed by one orchestrator)
- Real-world PR review workload is available as a benchmark source

## Recommended Future Directions (Priority Order)

1. **Production deployment** — Persistent service with structured logging, health checks, and a minimal CLI
2. **Auto-merge with regression guard** — Safe automatic policy application for low-risk changes with rollback
3. **Self-healing pipeline** — Circuit-breaker pattern, fallback routing, automatic recovery from component failures
4. **Continuous benchmark** — Scheduled regression runs with score tracking and degradation alerts
