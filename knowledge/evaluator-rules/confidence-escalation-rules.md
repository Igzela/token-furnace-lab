# Confidence & Escalation Evaluator Rules

## Confidence Score Weights

| Component | Weight | Source |
|-----------|--------|--------|
| reviewer_confidence | 0.20 | Reviewer-stated confidence → {HIGH:100, MEDIUM:60, LOW:30} |
| evidence_quality | 0.25 | % of findings with valid evidence_path |
| validator_agreement | 0.25 | 100 if all validators pass, 0 otherwise |
| cross_reviewer_convergence | 0.15 | 100 if all agree, 60 if ≤2 disagree, 20 if >2 |
| repair_history | 0.15 | 100 if 0 rounds, 70 if <max, 30 if max reached |

## Level Thresholds

| Level | Threshold |
|-------|-----------|
| HIGH | ≥ 80 |
| MEDIUM | ≥ 60 |
| LOW | < 60 |

## Decision Policy Priority

1. **Budget exhausted + blocking findings** → ESCALATE
2. **Safety-critical findings + LOW confidence** → ESCALATE
3. **Blocking findings + repair budget remaining** → REPAIR
4. **Blocking findings + repair budget exhausted** → ESCALATE
5. **Validator failures** → REPAIR
6. **LOW confidence + HIGH/CRITICAL findings** → ESCALATE
7. **No blocking, all validators pass, confidence ≥ MEDIUM** → ACCEPT
8. **Repeated LOW findings only** → ACCEPT (informational, not blocking)

## Timeout Finding Classification

| Pattern | Classification |
|---------|---------------|
| PWM-active state, no safe transition action | REPAIR |
| Explicit PASSIVE_COAST / CONTROLLED_DECEL / PWM disable | ACCEPT |
| Ambiguous or unrecognized pattern | REVIEW |

### Claim Text Requirements

- Must include source state context for is_pwm_active detection
- Negations ("without PWM disable") must not trigger safe-action detection
- Classifier defaults to REVIEW for unrecognized patterns (fail-safe)

## Calibration Cases (Orchestration-007)

9 cases tested: 3 REPAIR, 3 REVIEW, 3 ACCEPT. All pass.

| Case | Claim Pattern | Expected | Rationale |
|------|--------------|----------|-----------|
| timeout-001 | PWM running → RESTART_PENDING | REPAIR | Implicit unsafe transition |
| timeout-002 | PWM running → FAULT_LATCHED | REPAIR | Implicit unsafe transition |
| timeout-003 | PWM running → FAULT_LATCHED | REPAIR | Implicit unsafe transition |
| timeout-004 | PWM disabled (PRECHARGE) → FAULT_LATCHED | REVIEW | Needs human review |
| timeout-005 | PWM active but stopped (ALIGN) → RESTART_PENDING | REVIEW | Needs human review |
| timeout-006 | PWM running (IF_RAMP) → RESTART_PENDING | REPAIR | Should route through PASSIVE_COAST |
| ctrl-001 | → PASSIVE_COAST | ACCEPT | Explicit safe transition |
| ctrl-002 | → CONTROLLED_DECEL | ACCEPT | Explicit safe transition |
| ctrl-003 | fault_latched → pwm_disabled | ACCEPT | Explicit PWM disable |

## Pass Criteria (Orchestration-008)

- [x] All 9 calibration cases pass (9/9)
- [x] Unsafe transitions classified as REPAIR
- [x] Confidence score emitted with 5 weighted components
- [x] Escalation report generated for ESCALATE decisions
- [x] No false ACCEPT on safety-critical ambiguity
- [x] Round 1 (blocking) → REPAIR verdict
- [x] Round 2 (clean) → ACCEPT verdict
- [x] Budget-exhausted + blocking → ESCALATE verdict
