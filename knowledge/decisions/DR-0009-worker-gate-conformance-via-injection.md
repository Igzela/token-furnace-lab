---
id: DR-0009
title: Worker gate conformance via check injection
experiment: hermes-perm-audit-003
date: 2026-05-27
---

# DR-0009: Worker gate conformance via check injection

## Decision

Add canonical gate checks directly to `check_worker_gates` rather than delegating to `check_gates` from `local_marker_executor`.

## Context

hermes-perm-audit-002 found 6/25 deny cases diverge between worker_daemon and marker_executor paths. The worker was missing LIVE_ENABLED, idempotency key, scope, and rollback plan checks.

## Rationale

The worker has additional gate requirements (arm gate validation, request state checks) that don't exist in the marker executor. Delegating to `check_gates` would require refactoring the marker executor to accept external gate results. The injection approach preserves the worker's autonomy while achieving behavioral equivalence.

## Trade-off

Code duplication between the two gate functions. Mitigated by the shared `flags_from_env` import and identical validation logic.

## Outcome

- C002-C005 conformance tests pass
- 0/25 deny cases diverge
- All smoke tests pass (57 assertions)
