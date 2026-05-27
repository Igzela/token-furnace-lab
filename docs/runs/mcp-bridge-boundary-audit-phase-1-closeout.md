# MCP Bridge Boundary Audit — Phase 1 Closeout

## Metadata

- Phase: mcp-bridge-boundary-audit-phase-1
- Experiments: 001, 002
- Status: COMPLETE
- Created: 2026-05-28

## Triple Verdict

- phase_verdict: COMPLETE
- target_control_verdict: PASS
- platform_validation_verdict: PASS

## Timeline

| Date | Experiment | Activity | Commit |
|------|------------|----------|--------|
| 2026-05-28 | 001 | Static analysis + mock boundary verification | a480b5b |
| 2026-05-28 | 002 | Runtime fixture boundary verification | 52301ba |

## 001: Static + Mock Boundary Verification

### Findings
- HTTP input boundary effective (path secret, method, JSON-RPC validation)
- Tool allowlist filtering works (only channels_list, permissions_list_open exposed)
- Hidden tools denied before stdio forward
- Audit doesn't record raw arguments
- Read-only annotations applied to exposed tools

### Matrix (001 Final)
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

## 002: Runtime Fixture Boundary Verification

### Test Results (8/8 PASS)
| ID | Test | Status |
|----|------|--------|
| TG01 | stdio metadata leakage | PASS |
| TG02a | subprocess spawn failure | PASS |
| TG02b | subprocess timeout | PASS |
| TG02c | stderr no secret leak | PASS |
| TG03 | concurrent request isolation | PASS |
| TG04 | oversized payload | PASS |
| TG05 | argument escalation | PASS |
| TG05b | argument injection | PASS |

### Matrix (001+002 Final)
| ID | Name | 001 | 002 | Final |
|----|------|-----|-----|-------|
| M001 | Path secret required | PASS | — | PASS |
| M002 | Only POST accepted | PASS | — | PASS |
| M003 | Malformed JSON-RPC denied | PASS | — | PASS |
| M004 | tools/list filters | PASS | — | PASS |
| M005 | Hidden tools not exposed | PASS | — | PASS |
| M006 | Hidden tool call denied | PASS | — | PASS |
| M007 | Allowed tools forwarded | PASS | — | PASS |
| M008 | stdio lifecycle | PARTIAL | PASS | PASS |
| M009 | stdio response filtering | PASS_WITH_NOTES | PASS | PASS |
| M010 | Denied request audited | PASS | — | PASS |
| M011 | Forwarded request audited | PASS | — | PASS |
| M012 | Raw args not persisted | PASS | — | PASS |
| M013 | Hidden deny before forward | PASS | — | PASS |
| M014 | Argument boundary | PASS_WITH_NOTES | PASS | PASS |
| M015 | Session isolation | UNKNOWN | PASS | PASS |
| M016 | Oversized payload | PARTIAL | PASS | PASS |

**Final: 16/16 PASS**

## Security Boundary Confirmation

1. **Path secret**: Required for all MCP requests; wrong path → 404
2. **Method filter**: Only POST accepted on /mcp/<secret>; GET → 405
3. **JSON-RPC validation**: Malformed JSON → 400
4. **Tool allowlist**: Only channels_list and permissions_list_open exposed
5. **Hidden tool gate**: Hidden tools denied before stdio forward
6. **Audit minimization**: No raw arguments, no path secret in audit
7. **Localhost binding**: 127.0.0.1 only
8. **Subprocess lifecycle**: Spawn failure, timeout, stderr all handled safely
9. **Session isolation**: Concurrent requests don't cross-contaminate
10. **Payload safety**: Oversized payloads handled without crash

## Known Limitations

1. **Not a public internet security audit**: 002 is fixture/runtime boundary verification, not long-term public exposure assessment
2. **No Cloudflare tunnel testing**: External network exposure scenarios not tested
3. **No multi-user auth model**: No real authentication/authorization testing
4. **No local process tampering**: Malicious same-user process modifying bridge files/runtime not tested
5. **No real hermes mcp serve**: All tests use mock subprocess; real hermes behavior not directly verified

These do NOT block Phase 1 PASS because Phase 1 goal is MCP bridge tool-boundary and runtime boundary, not public internet product security audit.

## Methodology Observations

1. **Static → Mock → Runtime lifecycle works**: 001 (static + mock) → 002 (runtime fixtures) is effective progression
2. **Mock boundary verifier is reusable**: `scripts/mcp_bridge_boundary_verify.py` can be run in CI
3. **Runtime fixture verifier is reusable**: `scripts/mcp_bridge_runtime_verify.py` can be run in CI
4. **GPT as architect + Claude Code as implementer**: GPT designed matrix, Claude Code wrote tests
5. **16-case matrix provides clear evidence trail**: Each case has status, evidence, conformance level

## Knowledge Assets Created

- `knowledge/wiki/mcp-bridge-tool-boundary-model.md`
- `knowledge/matrices/mcp-bridge-tool-boundary-matrix.yaml`
- `knowledge/decisions/DR-mcp-bridge-readonly-allowlist-boundary.md`
- `knowledge/evaluator-rules/ER-mcp-hidden-tools-deny-before-forward.md`

## Tag

```
git tag mcp-bridge-boundary-audit-phase-1
```

## Next Phase

Phase 2 (if needed): Public internet exposure security audit
- Cloudflare tunnel testing
- External network attack surface
- Real authentication model
- Long-term exposure assessment
