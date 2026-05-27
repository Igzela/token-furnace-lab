# MCP Bridge Tool Boundary Model

## Overview

The MCP bridge (`h2b-chatgpt-compatible-bridge.py`) proxies HTTP JSON-RPC requests to a stdio-based `hermes mcp serve` subprocess. The boundary model enforces: path-secret validation, method filtering, tool allowlist, hidden tool suppression, and argument-minimizing audit.

## Architecture

```
HTTP Client
    ↓ POST /mcp/<path-secret>
Handler (BaseHTTPRequestHandler)
    ↓ path validation
    ↓ JSON-RPC parse
    ↓ method routing
HermesStdioBridge
    ↓ stdio pipe
hermes mcp serve (subprocess)
```

## Boundary Layers

### Layer 1: HTTP Endpoint
- Binding: `127.0.0.1:18902` (localhost only)
- Path: `/mcp/<path-secret>` (secret from `H2B_PATH_SECRET` env)
- Methods: POST only (GET returns 405)

### Layer 2: JSON-RPC Validation
- Malformed JSON → 400 `invalid_json`
- Unknown method → `-32601` "method rejected"

### Layer 3: Tool Allowlist
- `ALLOWED_TOOLS = {channels_list, permissions_list_open}`
- `HIDDEN_TOOLS = {messages_send, permissions_respond, conversations_list, conversation_get, messages_read, attachments_fetch, events_poll, events_wait}`

### Layer 4: tools/list Filtering
- Forward to hermes, filter response to ALLOWED_TOOLS only
- Add read-only annotations: `readOnlyHint=true, destructiveHint=false`

### Layer 5: tools/call Gate
- If tool_name not in ALLOWED_TOOLS → deny with `-32601`
- Deny happens BEFORE stdio forward

### Layer 6: Audit
- Records: forbidden_rejected (tool names), forwarded_tool_calls (tool names)
- Does NOT record: raw arguments, path secret

## Key Properties

1. **Deny-before-forward**: Hidden tool calls are rejected before reaching stdio
2. **Hidden tools never enter stdio**: Not forwarded to hermes subprocess
3. **tools/list filtered**: Only allowed tools visible to HTTP clients
4. **Audit minimization**: No raw arguments persisted

## Known Gaps (as of 001)

- Session isolation not verified (single bridge instance, shared state)
- Stdio subprocess failure modes not fully tested
- Oversized payload handling not tested
- Real hermes mcp serve metadata leakage not runtime-verified
- Allowed tool argument semantic validation limited

## Related

- Matrix: `mcp-bridge-tool-boundary-matrix.yaml`
- Decision: `DR-mcp-bridge-readonly-allowlist-boundary.md`
- Evaluator Rule: `ER-mcp-hidden-tools-deny-before-forward.md`
- Experiment: `mcp-bridge-boundary-audit-001`
