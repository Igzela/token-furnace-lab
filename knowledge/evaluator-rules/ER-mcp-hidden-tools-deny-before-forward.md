# ER-mcp-hidden-tools-deny-before-forward

## Rule

Hidden MCP tools must be denied at the bridge layer BEFORE any stdio forward to the hermes subprocess.

## Rationale

If a hidden tool call reaches stdio, the hermes subprocess may execute it regardless of the bridge's allowlist. The deny must happen at the HTTP handler level, not rely on hermes-side filtering.

## Verification

For any `tools/call` request where `params.name` is in `HIDDEN_TOOLS`:
1. The bridge returns a JSON-RPC error (`-32601`)
2. `HermesStdioBridge.call()` is NOT invoked
3. The audit records the denied tool name
4. No raw arguments are persisted in audit

## Test Pattern

```python
# Mock bridge that records calls
mock_bridge = MockBridge()
response = handler._handle_rpc(None, {
    "method": "tools/call",
    "id": 1,
    "params": {"name": "messages_send"}
})

# Assert: error response
assert "error" in response
assert response["error"]["code"] == -32601

# Assert: no forward
assert len(mock_bridge.forwarded) == 0

# Assert: audit recorded
assert "messages_send" in mock_bridge.rejected
```

## Anti-patterns

- Forwarding to hermes and relying on hermes to deny (hermes may not have the same allowlist)
- Recording raw arguments in audit alongside denied tool name
- Returning success response for hidden tool calls

## Scope

Applies to all tools in `HIDDEN_TOOLS`:
- messages_send
- permissions_respond
- conversations_list
- conversation_get
- messages_read
- attachments_fetch
- events_poll
- events_wait

## Status

VERIFIED — mock boundary verifier in mcp-bridge-boundary-audit-001

## Related

- Matrix: M006, M013
- Decision: `DR-mcp-bridge-readonly-allowlist-boundary.md`
- Wiki: `mcp-bridge-tool-boundary-model.md`
