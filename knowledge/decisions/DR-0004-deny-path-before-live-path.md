# DR-0004: Deny Path Before Live Path

Decision: Any future live execution path must first have deny-path tests proving that execution is blocked when required conditions are missing.

Reason: A permission architecture should prove both allow and deny behavior. Testing only the happy path leaves the deny surface unverified.

Status: Accepted
Date: 2026-05-27
Source: hermes-perm-audit-001, GPT architect recommendation
