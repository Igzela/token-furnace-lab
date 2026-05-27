# Task: mcp-bridge-boundary-audit-002 — Runtime Stdio and Session Boundary Verification

## Objective

Verify runtime behavior of the MCP bridge stdio subprocess boundary, session isolation, payload handling, and real hermes mcp serve metadata leakage. Extends 001 (static + mock) with fixture-level runtime verification.

## Target

- **Repo**: Igzela/hermes-gateway-lab
- **File**: scripts/h2b-chatgpt-compatible-bridge.py
- **Local path**: ~/Projects/hermes-gateway-lab

## Depends On

- mcp-bridge-boundary-audit-001 (static + mock boundary verification)

## Test Groups

### TG01: stdio metadata leakage (P0)
Verify tools/list response from mock hermes doesn't leak hidden tool metadata through bridge filtering.

### TG02: stdio subprocess lifecycle (P0)
Verify spawn failure, timeout, crash, stderr handling.

### TG03: session/request isolation (P1)
Verify concurrent requests don't share state.

### TG04: oversized payload handling (P1)
Verify bridge handles oversized JSON-RPC payloads safely.

### TG05: allowed tool argument safety (P1)
Verify channels_list / permissions_list_open arguments don't escalate capability.

## Claude Code Tasks

1. Create fixture test script (mock hermes subprocess)
2. Implement TG01-TG05 test cases
3. Run tests and collect evidence
4. Output evidence for each test group

## Safety Constraints

- No live execution
- No external exposure (Cloudflare tunnel)
- No real secrets
- Localhost-only testing with mock subprocess
- No modification to target repo
