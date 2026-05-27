# Cost Estimate: hermes-perm-audit-004

## Token Usage

| Model | Role | Estimated Tokens | Actual Tokens |
|-------|------|------------------|---------------|
| Claude Code | Implementer | ~15,000 | ~18,000 |
| GPT | Architect | ~3,000 | ~3,500 |
| Codex | Verifier | ~2,000 | ~2,200 |
| **Total** | | **~20,000** | **~23,700** |

## Time Breakdown

| Phase | Duration |
|-------|----------|
| Test architecture design (GPT) | ~2 min |
| Test implementation (Claude Code) | ~15 min |
| Bug fixes (D018, redaction) | ~10 min |
| Coverage verification (Codex) | ~2 min |
| Model outputs & synthesis | ~5 min |
| **Total** | **~34 min** |

## Bug Discovery

| Bug | Discovery Time | Fix Time |
|-----|----------------|----------|
| D018: approve_task resets external_side_effect | ~5 min | ~3 min |
| Redaction: audit() doesn't sanitize | ~3 min | ~2 min |

## Efficiency Notes

- 2 bugs found during test implementation (not after)
- Both bugs were test design flaws, not code bugs
- Fix for D018 required adding `set_task_field()` helper
- Fix for redaction required matching caller pattern (`sanitize_text` before `audit`)

## ROI

- 24 regression tests for ~23,700 tokens (~987 tokens per test)
- Catches future gate divergence automatically
- Single command execution: `python3 scripts/gate_conformance_regression.py`
- <1 second execution time
