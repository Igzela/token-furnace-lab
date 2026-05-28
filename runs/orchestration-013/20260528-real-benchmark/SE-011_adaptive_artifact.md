## Delta Report: orchestrator-quality-gate-policy.md vs worker-gate-conformance.md

### Document Scope Summary

| Aspect | orchestrator-quality-gate-policy.md | worker-gate-conformance.md |
|--------|--------------------------------------|----------------------------|
| **Purpose** | Defines WHAT checks the gate performs, priority order, and severity levels | Defines HOW multiple code paths must implement the same checks consistently |
| **Level** | Policy/specification | Implementation pattern |
| **Test cases** | F001–F010 (failure injection) | C001–C005 (conformance) |
| **Validators referenced** | 5 named validators with scripts | None named |

---

### Findings

**[MEDIUM] Gap: Evidence validation has no conformance counterpart**

The orchestrator policy defines `validate_evidence()` (line 44) as a HIGH-severity check ensuring blocking findings have backing `evidence_path` files. The worker conformance document does not mention evidence validation at all. If the worker daemon or marker executor processes blocking findings, there is no documented rule requiring them to run evidence checks — creating a potential enforcement gap.

- *orchestrator-quality-gate-policy.md:44* — `validate_evidence() in tf_orchestrator.py | HIGH (blocking finding without evidence)`
- *worker-gate-conformance.md* — no mention of evidence or evidence_path

**[MEDIUM] Gap: Validator types and scripts not cross-referenced**

The orchestrator policy names 5 specific validators with scripts (lines 38–44). The worker conformance pattern discusses "gate functions" and "checks" generically but never maps its C001–C005 test cases back to these validators. A reader cannot determine whether the conformance tests cover all 5 validators or a subset.

- *orchestrator-quality-gate-policy.md:38–44* — table of 5 validators
- *worker-gate-conformance.md:13* — `C001-C005 test cases` with no mapping

**[LOW] Terminology divergence: "REJECT" vs "gate denies"**

The orchestrator policy uses precise action labels: REJECT, REPAIR, ESCALATE, ACCEPT (lines 8–14). The worker conformance uses "gate denies if empty" (line 21) without mapping to the REJECT/REPAIR distinction. In the orchestrator policy, a missing artifact triggers REJECT (line 8), but a missing required field like `rollback_plan` would likely trigger REPAIR (via validator). The conformance doc's "gate denies" is ambiguous about which action applies.

- *orchestrator-quality-gate-policy.md:8* — `Artifact exists? → REJECT`
- *worker-gate-conformance.md:21* — `gate denies if empty` (which action?)

**[LOW] Gap: Gate priority order not referenced in conformance**

The strict 7-level priority order (lines 5–15) is the core invariant of the orchestrator policy. The worker conformance pattern does not acknowledge or reference this ordering. If the worker daemon implements its own gate, it must respect the same priority — but this requirement is implicit, not stated.

- *orchestrator-quality-gate-policy.md:5–15* — priority rules
- *worker-gate-conformance.md* — no mention of priority order

**[LOW] Overlap: Both address "required fields must be enforced"**

Both documents agree that missing required data must be caught, but at different levels. The orchestrator policy covers it via `validate_artifact_schema.py` (line 43, CRITICAL). The worker conformance covers it via `rollback_plan` default-to-empty-then-deny pattern (line 21). These are consistent but not explicitly linked.

- *orchestrator-quality-gate-policy.md:43* — `validate_artifact_schema.py | CRITICAL (missing required fields)`
- *worker-gate-conformance.md:21* — `Required fields (like rollback_plan) should default to empty string in schema, gate denies if empty`

**[LOW] Gap: `sanitize_text` / secret redaction not in orchestrator policy**

The worker conformance identifies `sanitize_text` as "the right place for defense-in-depth secret redaction" (line 19). The orchestrator policy has no mention of secret redaction or text sanitization. If this is a gate-level concern, it belongs in the policy; if it's purely a worker concern, the conformance doc should state that boundary explicitly.

- *worker-gate-conformance.md:19* — `sanitize_text is the right place for defense-in-depth secret redaction`
- *orchestrator-quality-gate-policy.md* — no mention

---

### Score: 78
### Verdict: PASS_WITH_NOTES
### Confidence: MEDIUM

The two documents are not contradictory — they operate at policy vs implementation-pattern levels and are broadly consistent. The gaps identified are real but expected given the different scopes. The main risk is that the worker conformance pattern does not explicitly reference the orchestrator policy's validators, priority order, or evidence checks, leaving room for implementation drift.

### Final Recommendation: ACCEPT

No blocking contradictions found. The 5 findings are all gaps or terminology differences, not conflicts. Recommend adding a cross-reference section to `worker-gate-conformance.md` that maps C001–C005 to the orchestrator's 5 validators and acknowledges the gate priority order — but this is a documentation improvement, not a correctness issue.
