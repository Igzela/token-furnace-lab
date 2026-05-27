# Synthesis: mcp-bridge-boundary-audit-002

## Metadata

- Experiment: mcp-bridge-boundary-audit-002
- Type: audit (runtime verification)
- Status: COMPLETE
- Created: 2026-05-28
- Depends on: mcp-bridge-boundary-audit-001

## Verdict

- experiment_verdict: COMPLETE
- target_control_verdict: PASS

## Executive Summary

mcp-bridge-boundary-audit-002 completed successfully. Runtime fixture verification confirms that the MCP bridge handles subprocess lifecycle failures, session isolation, oversized payloads, and argument-based attacks safely. All 8 test cases passed. The target control is upgraded to PASS because all previously unknown/partial cases (M008, M009, M014, M015, M016) are now verified.

## Evidence Inputs

| Source | File | Status |
|--------|------|--------|
| Claude Code runtime tests | model_outputs/claude-code-output.md | 8/8 PASS |
| GPT architecture review | model_outputs/gpt-reviewer-output.md | CONFIRMED |
| Runtime fixture verifier | scripts/mcp_bridge_runtime_verify.py | 8 tests |

## Test Results

| ID | Test | Status | Evidence |
|----|------|--------|----------|
| TG01 | stdio metadata leakage | PASS | Hidden tool names, descriptions, annotations not in response |
| TG02a | subprocess spawn failure | PASS | Error response, no crash loop |
| TG02b | subprocess timeout | PASS | Bounded None response |
| TG02c | stderr no secret leak | PASS | Path secret not in error responses |
| TG03 | concurrent isolation | PASS | 10 concurrent requests, no cross-contamination |
| TG04 | oversized payload | PASS | 1MB payload handled, audit clean |
| TG05 | argument escalation | PASS | No capability escalation via arguments |
| TG05b | argument injection | PASS | Hidden tool name in arguments doesn't bypass allowlist |

## Matrix Update

| ID | 001 Status | 002 Status | Final |
|----|------------|------------|-------|
| M008 | PARTIAL | PASS | PASS |
| M009 | PASS_WITH_NOTES | PASS | PASS |
| M014 | PASS_WITH_NOTES | PASS | PASS |
| M015 | UNKNOWN | PASS | PASS |
| M016 | PARTIAL | PASS | PASS |

**Final: 16/16 PASS**

## Path Conformance

- Target repo (hermes-gateway-lab): No modifications
- Token Furnace Lab: Knowledge assets and closeout created
- Safety constraints: All respected (no live execution, no real secrets, localhost only, no tunnel)

## Cost Estimate

- Claude Code: ~30k tokens (runtime fixture verifier + tests)
- GPT: ~10k tokens (verdict confirmation)
- Total: ~40k tokens

## Decision Record

The MCP bridge runtime boundary is ACCEPTED. All fixture tests pass. The bridge handles subprocess failures, session isolation, oversized payloads, and argument attacks safely. Combined with 001 (static + mock), the bridge is verified for Phase 1 use.

## Known Limitations

1. Fixture-based, not real hermes mcp serve
2. No public internet exposure testing
3. No multi-user auth model
4. No local process tampering protection

These are deferred to Phase 2 if needed.
