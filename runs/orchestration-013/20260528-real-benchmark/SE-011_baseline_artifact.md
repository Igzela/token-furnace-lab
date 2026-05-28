## Delta Report: `orchestrator-quality-gate-policy.md` vs `worker-gate-conformance.md`

**Score: 78/100**
**Verdict: PASS_WITH_NOTES**
**Confidence: HIGH**

---

### Summary

These two documents operate at different abstraction levels and cover different domains. `orchestrator-quality-gate-policy.md` is a formal gate policy for the orchestrator's review pipeline. `worker-gate-conformance.md` is a knowledge note about a conformance bug discovered in the worker daemon's gate logic. There are no direct contradictions, but there are structural gaps and one terminology disconnect.

---

### Findings

- **[MEDIUM] No shared definition of "blocking finding"**
  - `orchestrator-quality-gate-policy.md:11` uses "Blocking findings?" as a gate priority level but never defines what constitutes a blocking finding beyond the test matrix examples (F004, F005).
  - `worker-gate-conformance.md:9` mentions "6 critical checks" the worker was missing but does not enumerate them or map them to the orchestrator's blocking finding taxonomy.
  - **Gap**: A worker-side gate could reject on a finding that the orchestrator doesn't classify as blocking, or vice versa. No shared severity vocabulary links the two.

- **[MEDIUM] Validator coverage asymmetry**
  - `orchestrator-quality-gate-policy.md:38-44` lists 5 explicit validators (state machine, review artifact, scope diff, artifact schema, evidence).
  - `worker-gate-conformance.md:9` references "6 critical checks" in the worker that were missing — none of these map to the orchestrator's 5 validators. The worker checks appear to be operational/safety checks (live-enable flags, secret redaction, rollback plan validation), not review-pipeline validators.
  - **Gap**: The orchestrator policy does not mention worker-side safety gates at all. A finding could pass the orchestrator's quality gate but fail the worker's safety gate, or the worker could be missing checks the orchestrator assumes exist.

- **[LOW] Terminology: "gate" means different things**
  - `orchestrator-quality-gate-policy.md` uses "gate" to mean: a deterministic pass/fail check on review artifacts before accepting a run.
  - `worker-gate-conformance.md` uses "gate" to mean: an operational safety check before the worker daemon executes an action (e.g., arm gate validation, live-enable flag).
  - **Note**: Not a contradiction, but a reader unfamiliar with the codebase could conflate the two. A glossary or explicit scope statement at the top of each document would help.

- **[LOW] `sanitize_text` / secret redaction not in orchestrator policy**
  - `worker-gate-conformance.md:19` identifies `sanitize_text` as "the right place for defense-in-depth secret redaction."
  - `orchestrator-quality-gate-policy.md` does not mention secret redaction as a gate check or validator.
  - **Gap**: If a review artifact contains secrets, the orchestrator gate would accept it (all 5 validators pass). The worker gate would catch it. This is an implicit two-layer defense, but it's undocumented in the orchestrator policy.

- **[LOW] `flags_from_env()` single-source-of-truth not referenced by orchestrator**
  - `worker-gate-conformance.md:17` establishes `flags_from_env()` as the single source of truth for `LIVE_ENABLED` state.
  - The orchestrator policy has no equivalent "single source of truth" principle for its gate inputs (score, verdict, evidence paths).
  - **Note**: Minor — the orchestrator reads structured artifacts, not env flags, so the pattern doesn't directly apply. But the principle (one canonical input source) could strengthen the orchestrator's design documentation.

---

### What's Consistent

- Both documents agree that deterministic checks should override non-deterministic ones (orchestrator: "Validators are deterministic and cheap" at line 54; worker: "thread flags as a parameter rather than reading env inside gate functions" at line 18 — both favor testable, deterministic inputs).
- Both documents are internally consistent within their own scope.
- No rule in one document contradicts a rule in the other.

---

### Final Recommendation

**ACCEPT** — The documents cover different domains (orchestrator review pipeline vs. worker operational safety) with no contradictions. The gaps identified are documentation gaps, not logic gaps: the orchestrator policy would benefit from a note acknowledging the worker's independent safety gate layer and defining the shared severity vocabulary for "blocking finding." These are improvements, not blockers.
