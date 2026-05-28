## Wiki Review: `knowledge/wiki/permission-boundary-model.md`

**Score: 68**
**Verdict: PASS_WITH_NOTES**
**Confidence: HIGH**

### Findings

- **[MEDIUM] Scope names abbreviated, not exact.** Wiki says `read, plan, approval.local, dry_run, live`. Source (`claude-code-repo-reader.md:35`) defines them as `hermes.read`, `hermes.plan`, `hermes.approval.local`, `hermes.execute.dry_run`, `hermes.execute.live`. The namespace prefix matters for code-level mapping.

- **[MEDIUM] Critical audit finding omitted.** The primary accepted finding from the audit (DR-0001) was that the **worker gate function diverges from the canonical 13-gate checklist** — the most significant architectural risk discovered. The wiki's rule candidate ("scopes, risk classes, and gate checklists as separate concerns") is generic and does not capture this key insight.

- **[LOW] Source attribution incomplete.** Wiki cites "GPT architect + Claude Code repo-reader convergence." The comparison also involved a Codex risk reviewer that surfaced 4 unique findings (re-approval replay, hardcoded gate values, missing TTL, permission deny duplicate). These were accepted as decision records DR-0004 through DR-0006.

- **[LOW] Evaluator criteria miss the dominant risk.** Evaluator says "verify that the most restrictive scope (live) has the most gates." The actual dominant risk was not about gate count but about **gate enforcement divergence** — the worker implements a different gate function than the canonical one. The evaluator should include a conformance check: does the executor enforce all documented gates?

### Final Recommendation

**REPAIR** — The wiki page is factually correct at a surface level but misses the primary finding of the source audit (worker gate drift), uses abbreviated scope names, and has an evaluator that tests the wrong thing. Two targeted edits would fix it: (1) add the worker gate drift finding to the observation/rule, and (2) update the evaluator to check gate enforcement conformance, not just gate count.
