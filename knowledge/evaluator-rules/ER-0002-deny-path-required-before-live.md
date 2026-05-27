# ER-0002: Deny Path Required Before Live

Rule: Before enabling any live execution path, deny-path tests must exist for all required gates. Deny tests must prove that execution is blocked when each gate condition is missing.

Test: Count deny-path tests. Compare against documented gate checklist. If deny tests < gates, FAIL.

Severity: Critical
Source: hermes-perm-audit-001, DR-0004
