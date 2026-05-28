# Evaluator Rule: Validator Fail Overrides Review Score

**Rule**: Deterministic validator errors (CRITICAL/HIGH) override reviewer score in gate evaluation.

**Priority**: Validators are checked before score. Even a perfect score cannot override a structural failure.

**Rationale**: Validators check structural properties that are binary (pass/fail):
- State machine: all states defined, all transitions valid, UNIVERSAL rules present
- Review artifact: score in range, valid verdict, findings section exists
- Scope: no forbidden paths, no secrets

A reviewer might give 90/100 to a model with missing UNIVERSAL hard-fault rules. The validator catches it as CRITICAL.

**Gate priority order**:
1. Artifact exists?
2. Validator errors (CRITICAL/HIGH)?
3. Evidence errors?
4. Blocking findings?
5. Score below threshold?
6. Verdict not accepted?

**Test coverage**: F008 (bad transition), F010 (validator FAIL but review PASS)
