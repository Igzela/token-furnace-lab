You are reviewing a cross-audit review artifact produced by Claude Code.

Claude reviewed the Phase E-001 runtime fault recovery model for a sensorless FOC water pump drive (22uF DC-link, TMS320F28035).

Claude's review is at: runs/orchestration/20260528-105029/artifacts/claude_review.md

Your job: review Claude's review for completeness, correctness, and missed issues.

Produce a structured review with:
- Score (0-100) for Claude's review quality
- Verdict (PASS, PASS_WITH_NOTES, or FAIL)
- Confidence (HIGH, MEDIUM, LOW)
- Findings (each with: id, severity, blocking, evidence_path, claim, correction)
- Final Recommendation (ACCEPT, REPAIR, ESCALATE, REJECT)

Focus on:
1. Did Claude miss any critical fault paths?
2. Are Claude's findings correctly prioritized?
3. Are timing constants physically reasonable?
4. Are there safety gaps Claude overlooked?
5. Is the blocking finding (F01: IF_RAMP missing) valid?

Include evidence paths for all claims.

Output your review as a markdown file with a JSON code block containing the structured data.
