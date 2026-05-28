# Synthesis: Orchestration-008 Confidence & Escalation Calibration

**Overall verdict**: PASS
**Calibration cases**: 9/9 passed
**Pipeline tests**: 3/3 passed

## Confidence Score Design

5 weighted components:
- reviewer_confidence (0.20): Maps HIGH/MEDIUM/LOW to 100/60/30
- evidence_quality (0.25): % of findings with valid evidence_path
- validator_agreement (0.25): Binary — all pass = 100, any fail = 0
- cross_reviewer_convergence (0.15): 100/60/20 based on verdict agreement
- repair_history (0.15): 100/70/30 based on repair rounds used

Level thresholds: HIGH ≥ 80, MEDIUM ≥ 60, LOW < 60

## Decision Policy

Priority-ordered rules:
1. Budget exhausted + blocking → ESCALATE
2. Safety-critical + LOW confidence → ESCALATE
3. Blocking + repair budget remaining → REPAIR
4. Blocking + budget exhausted → ESCALATE
5. Validator failures → REPAIR
6. LOW confidence + HIGH/CRITICAL findings → ESCALATE
7. No blocking + validators pass + confidence ≥ MEDIUM → ACCEPT
8. Repeated LOW findings only → ACCEPT (informational)

## Timeout Finding Classifier

Heuristic-based classification of timeout transitions:
- PWM-active source + no safe transition action → REPAIR
- Explicit PASSIVE_COAST / CONTROLLED_DECEL / PWM disable → ACCEPT
- Ambiguous or unrecognized → REVIEW (fail-safe default)

Key fixes applied:
1. Negation handling: "without PWM disable" no longer triggers safe-action detection
2. Default fallback: Changed from ACCEPT to REVIEW for unrecognized patterns
3. Repeated LOW findings: No longer triggers REPAIR when no blocking findings exist

## Calibration Results

| Case | Type | Expected | Actual | Pass |
|------|------|----------|--------|------|
| timeout-001 | PWM running → RESTART_PENDING | REPAIR | REPAIR | ✓ |
| timeout-002 | PWM running → FAULT_LATCHED | REPAIR | REPAIR | ✓ |
| timeout-003 | PWM running → FAULT_LATCHED | REPAIR | REPAIR | ✓ |
| timeout-004 | PWM disabled → FAULT_LATCHED | REVIEW | REVIEW | ✓ |
| timeout-005 | PWM active/stopped → RESTART_PENDING | REVIEW | REVIEW | ✓ |
| timeout-006 | PWM running → RESTART_PENDING | REPAIR | REPAIR | ✓ |
| ctrl-001 | → PASSIVE_COAST | ACCEPT | ACCEPT | ✓ |
| ctrl-002 | → CONTROLLED_DECEL | ACCEPT | ACCEPT | ✓ |
| ctrl-003 | fault → pwm_disabled | ACCEPT | ACCEPT | ✓ |

## Pipeline Verification

| Test | Input | Expected | Actual | Pass |
|------|-------|----------|--------|------|
| Round 1 (blocking) | 006 round 1 reviews | REPAIR | REPAIR | ✓ |
| Round 2 (clean) | 006 round 2 reviews | ACCEPT | ACCEPT | ✓ |
| Budget exhausted | 006 round 1 + exhausted | ESCALATE | ESCALATE | ✓ |

## Escalation Report

Generated when gate outputs ESCALATE. Contains:
- Unresolved findings with severity and blocking status
- Evidence paths for human review
- Attempted repair count
- Decision options: (a) accept with risk, (b) manual repair, (c) reject
- Safe default: REJECT
