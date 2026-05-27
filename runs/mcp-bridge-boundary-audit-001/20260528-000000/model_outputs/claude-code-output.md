# Claude Code Output: mcp-bridge-boundary-audit-001

## 1. Endpoint Inventory

| Endpoint | Method | Path | Purpose |
|----------|--------|------|---------|
| Health check | GET | /healthz | Returns {"ok": true, "transport": "streaming_http"} |
| MCP endpoint | POST | /mcp/<path-secret> | JSON-RPC MCP requests |
| MCP endpoint | GET | /mcp/<path-secret> | Returns 405 (POST only) |
| Other | * | * | Returns 404 |

**Binding**: 127.0.0.1:18902 (localhost only)

## 2. Allowed/Hidden Tool Inventory

### Allowed Tools (exposed via tools/list)

| Tool | Annotations |
|------|-------------|
| channels_list | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=false |
| permissions_list_open | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=false |

### Hidden Tools (suppressed from tools/list)

| Tool | Status |
|------|--------|
| messages_send | Hidden |
| permissions_respond | Hidden |
| conversations_list | Hidden |
| conversation_get | Hidden |
| messages_read | Hidden |
| attachments_fetch | Hidden |
| events_poll | Hidden |
| events_wait | Hidden |

## 3. Request Flow

```text
HTTP POST /mcp/<path-secret>
  ↓
Handler.do_POST()
  ↓
Check path == expected_path (H2B_PATH_SECRET)
  ↓ (if valid)
Parse JSON body
  ↓
Handler._handle_rpc(msg)
  ↓
Check method:
  - initialize/notifications/initialized → bridge.call(msg)
  - tools/list → bridge.call(msg) → filter to allowed tools → add read-only annotations
  - tools/call → check tool_name in ALLOWED_TOOLS → bridge.call(msg) or reject
  - other → reject with -32601
  ↓
HermesStdioBridge.call(msg)
  ↓
Write JSON to hermes stdin
  ↓
Read JSON from hermes stdout
  ↓
Return response
```

## 4. Deny/Forward Audit Points

### Deny Points

| Point | Condition | Response |
|-------|-----------|----------|
| Path validation | path != expected_path | 404 |
| Method validation | GET on /mcp/<secret> | 405 |
| Invalid JSON | json.loads fails | 400 {"error": "invalid_json"} |
| Unknown method | method not in {initialize, tools/list, tools/call} | -32601 "method rejected by H2-B bridge" |
| Tool not allowed | tool_name not in ALLOWED_TOOLS | -32601 "tool rejected by H2-B read-only allowlist" |

### Forward Points

| Point | Condition | Action |
|-------|-----------|--------|
| initialize | method == "initialize" | Forward to hermes |
| notifications/initialized | method == "notifications/initialized" | Forward to hermes |
| tools/list | method == "tools/list" | Forward to hermes, then filter |
| tools/call (allowed) | tool_name in ALLOWED_TOOLS | Forward to hermes |

### Audit Recording

| Event | Recorded |
|-------|----------|
| Rejected tool call | Yes (forbidden_rejected list) |
| Forwarded tool call | Yes (forwarded_tool_calls list) |
| Path secret in audit | No (not recorded) |

## 5. Unknowns

| Unknown | Risk | Notes |
|---------|------|-------|
| Does hermes mcp serve expose more tools than ALLOWED_TOOLS? | Medium | Bridge filters tools/list, but does hermes expose them internally? |
| Can tool arguments bypass read-only restriction? | Medium | Annotations are hints, not enforcement |
| Is stdio subprocess isolated? | Low | Runs as same user, no sandboxing |
| Does audit log leak sensitive data? | Low | Only records tool names, not arguments |
| Can path secret be brute-forced? | Low | Secret is environment variable, not validated for strength |
| Is there session isolation between requests? | Medium | Single bridge instance, shared state |

## 6. Target Repo Modification Check

```bash
cd ~/Projects/hermes-gateway-lab
git status --short
```

**Result**: No modifications to target repo during this audit.

## 7. Evidence Summary

| Case | ID | Status | Evidence |
|------|-----|--------|----------|
| Path secret required | M001 | PASS | Line 261-265: H2B_PATH_SECRET required, expected_path = f"/mcp/{secret}" |
| Only POST accepted | M002 | PASS | Line 170-180: do_GET returns 405 on /mcp/<secret> |
| Malformed JSON-RPC denied | M003 | PASS | Line 188-194: json.loads exception returns 400 |
| tools/list filters | M004 | PASS | Line 211-228: filters to ALLOWED_TOOLS |
| Hidden tools not exposed | M005 | PASS | Line 217: tool.get("name") not in ALLOWED_TOOLS |
| Direct hidden tool call denied | M006 | PASS | Line 233-239: returns -32601 |
| Read-only annotations | M007 | PASS | Line 221-225: annotations set to read-only |
| stdio lifecycle controlled | M008 | PARTIAL | Line 150-160: terminate/kill on shutdown, but no spawn validation |
| stdio response filtering | M009 | UNKNOWN | Need to verify if hermes leaks hidden tool metadata |
| Denied request audited | M010 | PASS | Line 140-144: record_rejected() |
| Forwarded request audited | M011 | PASS | Line 146-148: record_forwarded_tool_call() |
| Secret payload redacted | M012 | PASS | Audit only records tool names, not payloads |
