"""Standard Model Context Protocol (MCP) JSON-RPC 2.0 Stdio Wire Server.

Allows any official MCP client (Claude Desktop, Cursor, Continue.dev, Atlan Agent Gateway)
to connect via standard I/O (stdio) transport to query ContextForge governed catalog metadata.
"""

import json
import sys
from typing import Any

from cforge.mcp.server import MCPServer


class MCPStdioServer:
    """JSON-RPC 2.0 Protocol Handler for Model Context Protocol."""

    def __init__(self, mcp_server: MCPServer | None = None):
        self.server = mcp_server or MCPServer()

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single JSON-RPC 2.0 request or notification."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        # Notifications (no response expected)
        if req_id is None:
            return None

        # Protocol Handshake
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "contextforge-mcp", "version": "0.1.0"},
                },
            }

        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # Tool Discovery
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.server.get_tool_definitions()},
            }

        # Tool Execution
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                if tool_name == "search_assets":
                    res = self.server.search_assets(
                        query=arguments.get("query", ""),
                        asset_type=arguments.get("asset_type"),
                        limit=arguments.get("limit", 10),
                    )
                elif tool_name == "get_asset_context":
                    res = self.server.get_asset_context(
                        asset_id=arguments.get("asset_id", ""),
                        caller_role=arguments.get("caller_role", "ANALYST"),
                    )
                elif tool_name == "get_lineage":
                    res = self.server.get_lineage(
                        asset_id=arguments.get("asset_id", ""),
                        direction=arguments.get("direction", "BOTH"),
                        max_depth=arguments.get("max_depth", 5),
                    )
                elif tool_name == "get_policies":
                    res = self.server.get_policies(policy_id=arguments.get("policy_id"))
                elif tool_name == "get_quality":
                    res = self.server.get_quality(table_name=arguments.get("table_name", ""))
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method/Tool '{tool_name}' not found"},
                    }

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error executing tool: {e!s}"}],
                        "isError": True,
                    },
                }

        # Fallback for unknown methods
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not implemented"},
        }

    def run_stdio(self):
        """Standard I/O event loop reading JSON-RPC lines from stdin."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError:
                sys.stdout.write(
                    json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
                    + "\n"
                )
                sys.stdout.flush()


def main():
    server = MCPStdioServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
