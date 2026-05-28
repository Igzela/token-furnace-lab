Now I have enough context to produce the review.

---

## Review: `knowledge/wiki/permission-boundary-model.md`

**Score: 58**
**Verdict: PASS_WITH_NOTES**
**Confidence: HIGH**

---

### Findings

- **[HIGH] Missing critical safety detail: live scope is disabled by design.** The wiki mentions 5 scopes but does not note that `live` has `allowed: []` and `status: not_enabled`. This is the single most important property of the permission model. Source: repo-reader line 35, DR-0002.

- **[HIGH] Missing critical safety detail: R4/R5 risk classes are not enabled.** The wiki mentions R0-R5 but does not note that R4 (external side effect) and R5 (private content) are explicitly disabled. Source: repo-reader line 37.

- **[HIGH] Missing cross-references to related wiki pages.** Three sibling wiki pages (`policy-runtime-drift.md`, `deny-path-testing.md`, `agent-approval-authority.md`) are derived from the same audit and provide essential context. None are linked. A reader of this page gets no signal that the most critical finding (policy-runtime drift) is documented elsewhere.

- **[MEDIUM] Evaluator is too vague to be actionable.** "Check that each scope has a corresponding risk class mapping and gate checklist" does not specify what constitutes a valid mapping, what to do if mappings are missing, or how to verify gate enforcement at runtime. Compare with `deny-path-testing.md` which gives a concrete count-based test.

- **[MEDIUM] Missing the 13-gate checklist detail.** The repo-reader confirms 13 required checks before live execution (LIVE_ENABLED, Charlie approval, TTL, idempotency key, rollback plan, etc.). The wiki page mentions "gate checklists" generically but does not reference the count or key gates.

- **[MEDIUM] Missing ChatGPT approval restriction.** The repo-reader and GPT architect both converge on: "ChatGPT CANNOT be final approver." This is a defining constraint of the approval model. Not mentioned.

- **[LOW] No reference to source artifacts.** The page cites `hermes-perm-audit-001` but does not link to the specific model outputs (`gpt-architect.md`, `claude-code-repo-reader.md`) or the decision record (`DR-0002`).

- **[LOW] Observation/Rule/Evaluator format is correct but thin.** The observation is accurate but surface-level. A reader unfamiliar with the audit gets no sense of *why* this model exists or what risks it mitigates.

---

### Accuracy Verification

| Claim | Source | Status |
|-------|--------|--------|
| 5-scope model (read, plan, approval.local, dry_run, live) | repo-reader line 35 | CORRECT |
| Risk classes R0-R5 | repo-reader line 37 | CORRECT |
| Scopes, risk classes, gates are separate concerns | GPT architect architecture assessment | CORRECT |
| Source: hermes-perm-audit-001 | run directory confirmed | CORRECT |

All factual claims are accurate. No incorrect statements found.

---

### Final Recommendation: **REPAIR**

The page is factually correct but missing safety-critical details that a future reader would need. Specifically:

1. Add that `live` scope is disabled (`allowed: []`, `not_enabled`)
2. Add that R4/R5 are not enabled
3. Add cross-references to `policy-runtime-drift.md`, `deny-path-testing.md`, `agent-approval-authority.md`, and `DR-0002`
4. Sharpen the evaluator with a concrete check (e.g., "Verify live scope has `allowed: []`; verify R4/R5 are not in any enabled risk class list")
5. Mention the 13-gate checklist and the ChatGPT approval restriction

The factual content is sound; the repair is about completeness and cross-linking, not correction.
