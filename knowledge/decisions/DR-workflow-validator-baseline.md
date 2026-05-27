# DR-workflow-validator-baseline

## Decision

Implement three automated validators (validate_run.py, validate_matrix_consistency.py, validate_synthesis_evidence.py) to enforce workflow quality gates mechanically, replacing manual-only checks.

## Context

workflow-quality-gate-audit-001 identified 5 weak gates:
1. W006: pre/post status not explicitly recorded
2. W012: matrix summary counts not automatically checked
3. Evidence gap: accepted findings without evidence_path unchecked
4. Naming inconsistency: model-outputs/ vs model_outputs/
5. validate_run.py drift: hardcoded filenames

## Rationale

Manual-only gates create false PASS risk. Automated validators:
- Catch matrix summary count mismatches before verdict
- Enforce evidence_path for accepted findings
- Support canonical layout with legacy compatibility
- Check model role contract (declared roles must have outputs)

## Alternatives Considered

1. **Manual discipline only**: Rejected — false PASS risk too high
2. **Strict enforcement (no legacy)**: Rejected — breaks historical runs
3. **CI/CD pipeline**: Deferred — not needed for local-only platform

## Consequences

- Matrix PASS verdicts now require automated validation
- Synthesis evidence is enforced, not just documented
- Legacy layout supported but warnings generated
- Codex role is contract-based, not globally mandatory

## Status

ACCEPTED — implemented in workflow-quality-gate-audit-002 (f3b8346)
