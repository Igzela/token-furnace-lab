---
title: Worker Gate Conformance Pattern
experiment: hermes-perm-audit-003
date: 2026-05-27
---

# Worker Gate Conformance Pattern

Observation: Worker daemon and marker executor had independent gate functions with different coverage. Worker was missing 6 critical checks.

Rule candidate: When two code paths must enforce the same safety policy, either (a) delegate to a shared function, or (b) inject the same checks into both. Option (b) is preferred when the paths have different operational requirements (e.g., arm gate validation).

Evaluator: Run both paths with identical inputs. If any path allows what the other denies, conformance fails. Automate via C001-C005 test cases.

## Key Learnings

1. `flags_from_env()` is the single source of truth for LIVE_ENABLED state
2. Thread flags as a parameter rather than reading env inside gate functions (testable)
3. `sanitize_text` is the right place for defense-in-depth secret redaction
4. Required fields (like rollback_plan) should default to empty string in schema, gate denies if empty
