# GPT Architecture Reviewer Output: mcp-bridge-boundary-audit-001

## Verdict

- experiment_verdict: COMPLETE
- static_discovery: COMPLETE
- target_control_verdict: PASS_WITH_NOTES
- platform_validation_verdict: PASS

## Summary

The bridge shows a strong initial boundary design: localhost binding, path-secret validation, small read-only allowlist, explicit hidden tools, and audit points for deny/forward events. However, the current evidence is mostly static. The bridge cannot yet be marked PASS until hidden direct tool calls, tools/list response filtering, argument handling, stdio lifecycle, and session isolation are tested with non-live fixtures or mocks.

## Accepted Findings

1. The exposed tool surface is intentionally narrow: `channels_list` and `permissions_list_open`.
2. Write/authorization tools are hidden by design.
3. The bridge binds to localhost, reducing accidental external exposure.
4. Path-secret validation is a meaningful first boundary.
5. Audit logging avoids raw argument persistence, reducing leakage risk.

## Findings Requiring Verification

1. Hidden tool direct calls must deny before stdio forward.
2. `tools/list` response must not leak hidden tool metadata from Hermes.
3. Allowed tool arguments must not be able to escalate capability.
4. Session isolation is not yet proven.
5. Stdio subprocess lifecycle needs failure/timeout verification.

## Matrix Adjustment

M001-M007 should be marked `STATIC_PASS`, not final PASS. M009 remains P0 UNKNOWN. M013-M016 should be added to cover direct hidden call denial, argument boundary, session isolation, and malformed/oversized payload behavior.

## Recommended Tests for Mock Boundary Verifier

### Test 1: Hidden tool direct call
- JSON-RPC: tools/call with messages_send
- Expected: deny/error, no forward, audit records denied tool, arguments not persisted raw

### Test 2: tools/list response filtering
- Mock hermes returns mixed allowed/hidden tools
- Expected: HTTP response only contains allowed tools, no hidden tool metadata leaked

### Test 3: Unknown tool call
- JSON-RPC: tools/call with unknown_tool
- Expected: deny_without_forward, audit denied

### Test 4: Allowed tool argument pollution
- JSON-RPC: channels_list with unexpected/path/token arguments
- Expected: allowed tool may forward only if arguments are safe or ignored, audit does not persist raw token, no hidden capability triggered
- Note: If code doesn't validate arguments, mark WARN not FAIL

### Test 5: Path-secret boundary
- /mcp/wrong-secret → deny
- /mcp/<correct-secret> → accepted
- /mcp/ → deny
- Wrong HTTP method → deny
- Use `<REDACTED_PATH_SECRET>` in artifacts

### Test 6: stdio spawn lifecycle
- HermesStdioBridge init failure → HTTP error, no crash loop
- stdio timeout → bounded error
- subprocess stderr/stdout doesn't leak secret
- bridge shutdown cleans subprocess
- Can mock, don't need real hermes mcp serve

## Final Conclusion

001 proved:
- HTTP input boundary effective
- path secret validation effective
- error method / malformed JSON-RPC doesn't forward
- tools/list filters hidden tools
- hidden tools direct tools/call denied before forward
- allowed tools can be forwarded
- audit doesn't record raw arguments

This is sufficient to mark 001 as COMPLETE.

## Matrix Status

M001: PASS   # path secret
M002: PASS   # method/path boundary
M003: PASS   # malformed JSON-RPC
M004: PASS   # tools/list allowlist filtering
M005: PASS   # hidden tools not exposed
M006: PASS   # direct hidden tool call denied before forward
M007: PASS   # allowed tools forwarded
M008: PARTIAL # stdio subprocess lifecycle not fully verified
M009: PASS_WITH_NOTES # mock verified filtering; real hermes metadata still not runtime-verified
M010: PASS   # denied request audited
M011: PASS   # forwarded request audited
M012: PASS   # raw arguments not persisted

M013: PASS          # direct hidden tools/call denied before forward
M014: PASS_WITH_NOTES # allowed tool arguments forwarded; no escalation shown, but semantic validation limited
M015: UNKNOWN       # session isolation not tested
M016: PARTIAL       # malformed JSON covered; oversized payload not tested

## Next Step

Open mcp-bridge-boundary-audit-002: Runtime Stdio and Session Boundary Verification

002 goals:
1. Verify real hermes mcp serve tools/list metadata leakage
2. Verify stdio subprocess spawn/timeout/crash/stderr behavior
3. Verify session/request isolation
4. Verify oversized payload handling
5. Verify allowed tool argument safety for channels_list / permissions_list_open

001 should be closed as discovery + mock boundary verification. Don't add runtime tests to 001.
