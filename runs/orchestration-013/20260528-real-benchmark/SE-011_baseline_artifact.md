## Delta Report: orchestrator-quality-gate-policy.md vs worker-gate-conformance.md

**Score: 62/100**
**Verdict: PASS_WITH_NOTES**
**Confidence: HIGH**

---

### Analysis

These two documents operate at **different abstraction levels** — one is a gate policy definition, the other is a lessons-learned wiki note. They aren't designed to be directly compared, but they should reference each other and maintain consistent terminology. They currently do neither.

---

### Findings

- **[MEDIUM] No cross-references between documents.** `orchestrator-quality-gate-policy.md` lists `[[ER-schema-invalid-cannot-pass]]` and `[[ER-validator-fail-overrides-review-score]]` as related rules (lines 62-63), but does not reference `worker-gate-conformance`. Conversely, `worker-gate-conformance.md` mentions "6 critical checks" missing from worker (line 9) but never references the orchestrator's gate priority rules that define what "critical" means in the gate context.

- **[MEDIUM] Terminology mismatch on severity levels.** The orchestrator policy defines specific severity levels per validator type: `CRITICAL` and `HIGH` (lines 39-44). The worker doc says "6 critical checks" (line 9) without specifying whether these map to the orchestrator's `CRITICAL` severity (which triggers REPAIR/ESALATE at priority 2) or are "critical" in a colloquial sense. This ambiguity could lead to misclassification if someone ports the worker findings into the orchestrator gate.

- **[LOW] No shared test matrix.** The orchestrator policy defines a 10-case failure-injection matrix (F001-F010, lines 19-33). The worker doc references C001-C005 test cases (line 13) but these are not listed, and there's no indication whether they overlap with or are subsets of the orchestrator's matrix. A reader cannot determine if the worker conformance tests cover the same failure modes.

- **[LOW] Scope boundary undocumented.** The orchestrator policy says validators are "deterministic and cheap" (line 54) and defines 5 validator types (lines 38-44). The worker doc identifies `flags_from_env()` as "single source of truth for LIVE_ENABLED state" (line 17) — this is a runtime configuration gate, not a validator in the orchestrator's sense. The boundary between "orchestrator validator" and "worker gate check" is not formally defined anywhere.

- **[LOW] Missing integration point.** The worker doc's pattern (line 11) — "delegate to a shared function, or inject the same checks into both" — is a good practice, but neither document explains how worker gate failures flow into the orchestrator's priority chain. If a worker gate check fails, does it trigger the orchestrator's priority-2 (validator CRITICAL/HIGH) or is it handled elsewhere?

---

### Final Recommendation

**PASS_WITH_NOTES** — The documents don't directly contradict each other, but the lack of cross-references and shared terminology creates a gap that could cause confusion during integration. Recommend adding a `[[worker-gate-conformance]]` link to the orchestrator policy's "Related Rules" section, and clarifying whether the worker's "6 critical checks" map to the orchestrator's `CRITICAL` severity level.
