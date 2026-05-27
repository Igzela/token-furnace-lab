# ER-0001: Live Gate Conformance

Rule: Any code path that enables live execution must import and use the canonical gate function. Independent gate implementations are prohibited.

Test: Compare gate checks in worker path vs canonical path. If worker path omits any gate that canonical path enforces, FAIL.

Severity: Critical
Source: hermes-perm-audit-001, F-0001
