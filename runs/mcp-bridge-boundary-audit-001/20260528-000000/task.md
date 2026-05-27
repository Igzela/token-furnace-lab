# Task: mcp-bridge-boundary-audit-001 — MCP Bridge Tool Boundary Discovery Audit

## Objective

Map and audit the MCP bridge tool boundary, including HTTP JSON-RPC input, path-secret validation, tool allowlist filtering, hidden tool suppression, stdio subprocess boundary, and audit logging.

## Target

- **Repo**: Igzela/hermes-gateway-lab
- **File**: scripts/h2b-chatgpt-compatible-bridge.py
- **Local path**: ~/Projects/hermes-gateway-lab

## Claude Code First Round Tasks

1. Read h2b-chatgpt-compatible-bridge.py
2. Output endpoint inventory
3. Output allowed/hidden tool inventory
4. Output request flow: HTTP → Handler → HermesStdioBridge → hermes mcp serve
5. Output deny/forward audit points
6. Output unknowns
7. Confirm target repo no modification

## Safety Constraints

- No live execution
- No external exposure (Cloudflare tunnel)
- No real secrets
- Localhost-only testing with fake secrets if needed
- No modification to target repo
