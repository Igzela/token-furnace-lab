# Codex Regression Check — hermes-perm-audit-003

## Regression Analysis

### No regression in existing conformant cases

Verified by running all 6 smoke test suites. All existing tests pass without modification to test expectations (only test setup was updated to provide required fields).

### Per-case regression check

| Case | 002 Status | 003 Status | Regression? |
|------|-----------|-----------|-------------|
| D001 | missing (worker) | complete | No — now conformant |
| D002 | missing (worker) | complete | No — now conformant |
| D003 | missing (worker) | complete | No — now conformant |
| D004 | complete | complete | No |
| D005 | complete | complete | No |
| D006 | complete | complete | No |
| D007 | partial | partial | No |
| D008 | missing | missing | No |
| D009 | partial | partial | No |
| D010 | missing (worker) | complete | No — now conformant |
| D011 | partial | partial | No |
| D012 | missing (worker) | partial | No — improved but not complete |
| D013 | partial | partial | No |
| D014 | missing (both) | complete | No — now implemented |
| D015 | missing | partial | No — improved |
| D016 | missing | missing | No |
| D017 | partial | partial | No |
| D018 | complete | complete | No |
| D019 | complete | complete | No |
| D020 | complete | complete | No |
| D021 | complete | complete | No |
| D022 | partial | partial | No |
| D023 | partial | partial | No |
| D024 | missing (both) | complete | No — now implemented |
| D025 | complete | complete | No |

### New divergent cases

None introduced. All previously conformant cases remain conformant.

### Smoke test coverage

| Suite | Tests | Coverage |
|-------|-------|----------|
| h4_approval_queue | 1 | Task CRUD, approval flow |
| h5_inert_executor | 1 | Inert execution gates |
| live4c_marker_executor | 1 | Disabled-flag refusal, path escape |
| live7_auto_worker | 34 | Full worker lifecycle: surface, create, arm, execute, duplicate, rollback, leakage |
| live9c_permission_deny_dry_run | 12 | Permission deny dry-run gates |
| live9d_permission_deny_worker | 11 | Permission deny worker gates |

### Conformance matrix update

**C001:** worker uses canonical gate function → **partial** (imports flags_from_env, adds canonical checks, but still has independent check_worker_gates rather than delegating to check_gates)
**C002:** worker independent gate covers all marker gates → **pass** (all marker gates now present in worker)
**C003:** worker and marker produce same deny/allow for P0 cases → **pass** (D001/D002/D010 now deny on worker path)

## Verdict

**No regressions detected.** All existing conformant cases remain conformant. 5 previously divergent cases (D001, D002, D003, D010, D014) are now conformant. D012 improved from missing to partial.
