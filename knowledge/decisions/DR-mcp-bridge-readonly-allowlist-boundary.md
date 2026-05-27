# DR-mcp-bridge-readonly-allowlist-boundary

## Decision

The MCP bridge enforces a read-only allowlist boundary: only `channels_list` and `permissions_list_open` are exposed via HTTP JSON-RPC. All write-capable and authorization tools are hidden from `tools/list` and denied at `tools/call` before reaching stdio.

## Context

The bridge proxies HTTP requests to a stdio-based `hermes mcp serve` subprocess. Without filtering, all hermes tools would be exposed to HTTP clients, including write-capable tools like `messages_send` and `permissions_respond`.

## Rationale

1. **Minimal attack surface**: Only 2 read-only tools exposed
2. **Defense in depth**: Hidden tools denied at multiple layers (tools/list filtering + tools/call gate)
3. **Deny before forward**: Rejection happens before stdio subprocess, preventing any side effects
4. **Audit minimization**: Only tool names recorded, no raw arguments

## Alternatives Considered

1. **Full tool exposure with argument validation**: Rejected — too complex, hermes tools have varied argument semantics
2. **MCP-level auth (OAuth/API keys)**: Rejected — overkill for localhost-only bridge
3. **Per-tool allowlist per client**: Rejected — single bridge instance, no client identity

## Consequences

- HTTP clients can only read channel/permission data
- Write operations require direct hermes access (not via bridge)
- Future tool additions must be explicitly added to ALLOWED_TOOLS
- Audit log is safe to persist (no secrets)

## Verification

- Mock boundary verifier confirms: deny before forward, hidden tools never enter stdio, tools/list filtered, audit doesn't record raw arguments

## Status

ACCEPTED — verified in mcp-bridge-boundary-audit-001

## Related

- Matrix: `mcp-bridge-tool-boundary-matrix.yaml`
- Wiki: `mcp-bridge-tool-boundary-model.md`
- Evaluator: `ER-mcp-hidden-tools-deny-before-forward.md`
