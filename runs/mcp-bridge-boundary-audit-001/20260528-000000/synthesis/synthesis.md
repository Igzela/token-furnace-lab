# Synthesis: mcp-bridge-boundary-audit-001

## Metadata

- Experiment: mcp-bridge-boundary-audit-001
- Type: audit
- Status: COMPLETE
- Created: 2026-05-28

## Verdict

- experiment_verdict: COMPLETE
- target_control_verdict: PASS_WITH_NOTES
- platform_validation_verdict: PASS

## Executive Summary

mcp-bridge-boundary-audit-001 completed successfully. Static inspection and mock boundary verification confirm that the bridge enforces path-secret validation, method/JSON-RPC validation, tool allowlist filtering, hidden-tool denial before stdio forwarding, and argument-minimizing audit behavior. The target control is PASS_WITH_NOTES because real hermes mcp serve runtime behavior, stdio lifecycle failure modes, session isolation, and oversized payload handling remain unverified.

## Evidence Inputs

| Source | File | Status |
|--------|------|--------|
| Claude Code static analysis | model_outputs/claude-code-output.md | COMPLETE |
| GPT architecture review | model_outputs/gpt-reviewer-output.md | COMPLETE |
| Mock boundary verifier | scripts/mcp_bridge_boundary_verify.py | 7/7 PASS |

## Model Output Comparison

### Claude Code
- Mapped all endpoints, tools, request flow
- Identified 12 boundary cases
- Created mock boundary verifier with 7 tests
- All tests passing

### GPT
- Reviewed boundary architecture
- Added M013-M016 cases
- Confirmed verdict: COMPLETE / PASS_WITH_NOTES
- Recommended 002 for runtime verification

## Accepted Findings

1. HTTP input boundary effective (path secret, method, JSON-RPC validation)
2. Tool allowlist filtering works (only channels_list, permissions_list_open exposed)
3. Hidden tools denied before stdio forward
4. Audit doesn't record raw arguments
5. Read-only annotations applied to exposed tools

## Findings Requiring Verification

1. M008: Stdio subprocess lifecycle (PARTIAL — static only)
2. M009: Real hermes metadata leakage (PASS_WITH_NOTES — mock only)
3. M014: Allowed tool argument semantic validation (PASS_WITH_NOTES)
4. M015: Session isolation (UNKNOWN)
5. M016: Oversized payload handling (PARTIAL)

## Matrix Results

| ID | Name | Status |
|----|------|--------|
| M001 | Path secret required | PASS |
| M002 | Only POST accepted | PASS |
| M003 | Malformed JSON-RPC denied | PASS |
| M004 | tools/list filters | PASS |
| M005 | Hidden tools not exposed | PASS |
| M006 | Hidden tool call denied | PASS |
| M007 | Allowed tools forwarded | PASS |
| M008 | stdio lifecycle | PARTIAL |
| M009 | stdio response filtering | PASS_WITH_NOTES |
| M010 | Denied request audited | PASS |
| M011 | Forwarded request audited | PASS |
| M012 | Raw args not persisted | PASS |
| M013 | Hidden deny before forward | PASS |
| M014 | Argument boundary | PASS_WITH_NOTES |
| M015 | Session isolation | UNKNOWN |
| M016 | Oversized payload | PARTIAL |

## Path Conformance

- Target repo (hermes-gateway-lab): No modifications
- Token Furnace Lab: Knowledge assets created
- Safety constraints: All respected (no live execution, no real secrets, localhost only)

## Cost Estimate

- Claude Code: ~50k tokens (static analysis + mock verifier)
- GPT: ~20k tokens (architecture review)
- Total: ~70k tokens

## Decision Record

The bridge's read-only allowlist boundary is ACCEPTED. The design is sound: minimal tool surface, deny-before-forward, audit without argument leakage. Runtime verification deferred to 002.

## Next Experiment

mcp-bridge-boundary-audit-002: Runtime Stdio and Session Boundary Verification

Goals:
1. Verify real hermes mcp serve tools/list metadata leakage
2. Verify stdio subprocess spawn/timeout/crash/stderr behavior
3. Verify session/request isolation
4. Verify oversized payload handling
5. Verify allowed tool argument safety
