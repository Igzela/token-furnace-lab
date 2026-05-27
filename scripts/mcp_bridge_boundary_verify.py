#!/usr/bin/env python3
"""MCP Bridge Boundary Verifier — mock-based boundary testing.

This script verifies the MCP bridge boundary without starting a real bridge.
It mocks HermesStdioBridge and tests:
1. Deny happens before forward
2. Hidden tools don't enter stdio
3. tools/list is filtered
4. Audit doesn't record raw arguments
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import bridge module from hermes-gateway-lab
bridge_path = Path.home() / "Projects" / "hermes-gateway-lab" / "scripts"
sys.path.insert(0, str(bridge_path))

# Import with hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location(
    "h2b_chatgpt_compatible_bridge",
    bridge_path / "h2b-chatgpt-compatible-bridge.py"
)
bridge_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge_module)


class MockBridge:
    """Mock HermesStdioBridge that records calls."""

    def __init__(self):
        self.forwarded = []
        self.rejected = []
        self.audit = {
            "forbidden_rejected": [],
            "forwarded_tool_calls": [],
        }

    def call(self, msg, timeout=20):
        """Record forward calls."""
        self.forwarded.append(msg)
        return {"id": msg.get("id"), "result": {"tools": []}}

    def record_rejected(self, tool_name):
        """Record rejected tools."""
        self.rejected.append(tool_name)
        if tool_name not in self.audit["forbidden_rejected"]:
            self.audit["forbidden_rejected"].append(tool_name)

    def record_forwarded_tool_call(self, tool_name):
        """Record forwarded tool calls."""
        self.audit["forwarded_tool_calls"].append(tool_name)

    def shutdown(self):
        pass


def test_path_validation():
    """M001: Path secret required."""
    print("Testing M001: Path validation...")

    mock_bridge = MockBridge()
    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            # Create a real handler instance with mocked socket
            handler = bridge_module.Handler.__new__(bridge_module.Handler)
            handler.path = '/mcp/wrong-secret'
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            # Test wrong path
            handler.do_GET()
            handler.send_response.assert_called_with(404)

            handler.send_response.reset_mock()
            handler.path = '/mcp/test-secret'
            handler.do_GET()
            handler.send_response.assert_called_with(405)

    print("  PASS: Path validation works correctly")
    return True


def test_method_validation():
    """M002: Only POST accepted on /mcp/<path-secret>."""
    print("Testing M002: Method validation...")

    mock_bridge = MockBridge()
    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            handler = bridge_module.Handler.__new__(bridge_module.Handler)
            handler.path = '/mcp/test-secret'
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            # GET should return 405
            handler.do_GET()
            handler.send_response.assert_called_with(405)

    print("  PASS: Method validation works correctly")
    return True


def test_json_rpc_validation():
    """M003: Malformed JSON-RPC denied safely."""
    print("Testing M003: JSON-RPC validation...")

    mock_bridge = MockBridge()
    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            handler = bridge_module.Handler.__new__(bridge_module.Handler)
            handler.path = '/mcp/test-secret'
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler._send_json = MagicMock()
            handler.rfile = MagicMock()
            handler.rfile.read.return_value = b'invalid json'
            handler.headers = {'Content-Length': '12'}

            # Test invalid JSON
            handler.do_POST()
            handler._send_json.assert_called_with({"error": "invalid_json"}, status=400)

    print("  PASS: JSON-RPC validation works correctly")
    return True


def test_tools_list_filtering():
    """M004/M005: tools/list filters to allowed tools, hidden tools not exposed."""
    print("Testing M004/M005: tools/list filtering...")

    mock_bridge = MockBridge()
    mock_bridge.call = MagicMock(return_value={
        "id": 1,
        "result": {
            "tools": [
                {"name": "channels_list"},
                {"name": "permissions_list_open"},
                {"name": "messages_send"},  # Should be hidden
                {"name": "permissions_respond"},  # Should be hidden
                {"name": "conversations_list"},  # Should be hidden
            ]
        }
    })

    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            handler = bridge_module.Handler
            response = handler._handle_rpc(None, {"method": "tools/list", "id": 1})

            tools = response["result"]["tools"]
            tool_names = [t["name"] for t in tools]

            assert "channels_list" in tool_names, "channels_list should be exposed"
            assert "permissions_list_open" in tool_names, "permissions_list_open should be exposed"
            assert "messages_send" not in tool_names, "messages_send should be hidden"
            assert "permissions_respond" not in tool_names, "permissions_respond should be hidden"
            assert "conversations_list" not in tool_names, "conversations_list should be hidden"

            # Check annotations
            for tool in tools:
                assert tool["annotations"]["readOnlyHint"] == True
                assert tool["annotations"]["destructiveHint"] == False

    print("  PASS: tools/list filtering works correctly")
    return True


def test_hidden_tool_denial():
    """M006: Direct hidden tool call denied."""
    print("Testing M006: Hidden tool denial...")

    mock_bridge = MockBridge()
    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            handler = bridge_module.Handler
            response = handler._handle_rpc(None, {
                "method": "tools/call",
                "id": 1,
                "params": {"name": "messages_send"}
            })

            assert response is not None
            assert "error" in response
            assert response["error"]["code"] == -32601
            assert "rejected" in response["error"]["message"]

            # Verify no forward happened
            assert len(mock_bridge.forwarded) == 0, "Hidden tool should not be forwarded"
            assert "messages_send" in mock_bridge.rejected, "Hidden tool should be recorded as rejected"

    print("  PASS: Hidden tool denial works correctly")
    return True


def test_allowed_tool_forward():
    """M007: Allowed tool calls forwarded correctly."""
    print("Testing M007: Allowed tool forward...")

    mock_bridge = MockBridge()
    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            handler = bridge_module.Handler
            response = handler._handle_rpc(None, {
                "method": "tools/call",
                "id": 1,
                "params": {"name": "channels_list"}
            })

            # Verify forward happened
            assert len(mock_bridge.forwarded) == 1, "Allowed tool should be forwarded"
            assert "channels_list" in mock_bridge.audit["forwarded_tool_calls"]

    print("  PASS: Allowed tool forward works correctly")
    return True


def test_audit_no_raw_args():
    """M012: Audit doesn't record raw arguments."""
    print("Testing M012: Audit argument safety...")

    mock_bridge = MockBridge()
    with patch.object(bridge_module, 'bridge', mock_bridge):
        with patch.object(bridge_module, 'expected_path', '/mcp/test-secret'):
            handler = bridge_module.Handler
            handler._handle_rpc(None, {
                "method": "tools/call",
                "id": 1,
                "params": {
                    "name": "channels_list",
                    "arguments": {"secret": "should-not-be-recorded"}
                }
            })

            # Check audit doesn't contain arguments
            audit_json = json.dumps(mock_bridge.audit)
            assert "should-not-be-recorded" not in audit_json, "Audit should not contain raw arguments"

    print("  PASS: Audit doesn't record raw arguments")
    return True


def main():
    """Run all boundary verification tests."""
    print("MCP Bridge Boundary Verifier")
    print("=" * 40)

    results = []
    results.append(("M001", test_path_validation()))
    results.append(("M002", test_method_validation()))
    results.append(("M003", test_json_rpc_validation()))
    results.append(("M004/M005", test_tools_list_filtering()))
    results.append(("M006", test_hidden_tool_denial()))
    results.append(("M007", test_allowed_tool_forward()))
    results.append(("M012", test_audit_no_raw_args()))

    print("\n" + "=" * 40)
    print("Results:")
    for case_id, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {case_id}: {status}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\nAll boundary tests passed!")
        return 0
    else:
        print("\nSome boundary tests failed!")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
