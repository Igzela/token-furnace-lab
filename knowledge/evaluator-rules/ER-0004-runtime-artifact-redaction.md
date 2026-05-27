# ER-0004: Runtime Artifact Redaction

Rule: Runtime artifacts (audit logs, reliability reports, queue files) must not contain unsanitized secrets. Secret patterns must be scrubbed before persistence.

Test: Inject simulated secret into reason field, verify audit log does not contain it in plaintext.

Severity: Medium
Source: hermes-perm-audit-001, F-0003
