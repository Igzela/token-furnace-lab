# ER-0001: Live Gate Conformance

Rule: Any code path that enables live execution must import and use the canonical gate function. Independent gate implementations are prohibited.

Test: Compare gate checks in worker path vs canonical path. If worker path omits any gate that canonical path enforces, FAIL.

Conformance matrix: knowledge/matrices/gate-conformance-matrix.yaml (C001-C005)

Current status (hermes-perm-audit-002):
- C001: FAIL - worker does not use canonical gate
- C002: FAIL - worker missing 5+ gates
- C003: FAIL - 6/25 cases produce different deny/allow
- C004: untested - bypass entry unknown
- C005: partial - deny raises error but missing gates allow through

Severity: Critical
Source: hermes-perm-audit-001, hermes-perm-audit-002, F-0001
