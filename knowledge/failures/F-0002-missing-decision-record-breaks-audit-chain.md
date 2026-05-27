# F-0002: Missing Decision Record Breaks Audit Chain

Failure: `DECISION_RECORD.md` is referenced by quality gates but does not exist in hermes-gateway-lab/docs/harness/.

Impact: Medium. Reviewers cannot reconstruct why permission boundaries, risk classes, or live gating rules were accepted. Governance traceability gap.

Root cause: Quality gates document was written before the decision record was created. No automated check verifies referenced files exist.

Recovery: Create DECISION_RECORD.md with initial entries covering scope model, disabled live mode, human approval authority, R4/R5 non-enablement.

Source: hermes-perm-audit-001, GPT architect + Claude Code convergence
