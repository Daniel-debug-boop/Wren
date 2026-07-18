"""MCP (Model Context Protocol) integration for Wren SDK.

Wraps MCP servers as Wren tools with auto-discovery.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from wren.tool.base import Tool, ToolDef, ToolCategory, ToolSafety, Action, Observation

logger = logging.getLogger("wren.mcp")


class MCPToolDef(WrenModel):
    """MCP tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str


class MCPTool(Tool):
    """Wraps an MCP tool as a Wren tool."""

    def __init__(self, definition: MCPToolDef, executor: "MCPClient"):
        self._definition = definition
        self._executor = executor

    def get_definition(self) -> ToolDef:
        """Convert MCP tool to Wren ToolDef."""
        return ToolDef(
            name=f"mcp_{self._definition.name}",
            description=self._definition.description,
            parameters=self._definition.input_schema,
            category=ToolCategory.MCP,
            safety=ToolSafety.MODERATE,
            best_for=[self._definition.description.lower()],
            tags=["mcp", self._definition.server_name],
        )

    async def execute(self, action: Action) -> Observation:
        """Execute the MCP tool."""
        try:
            result = await self._executor.call_tool(
                self._definition.name,
                action.arguments,
            )
            return Observation(
                success=True,
                result=json.dumps(result) if isinstance(result, dict) else str(result),
            )
        except Exception as e:
            return Observation(
                success=False,
                result="",
                error=str(e),
            )


class MCPClient:
    """Client for connecting to MCP servers.

    Auto-discovers tools from connected MCP servers
    and wraps them as Wren tools.
    """

    def __init__(self, server_url: str | None = None):
        self.server_url = server_url
        self._tools: list[MCPToolDef] = []
        self._connected = False

    @property
    def tools(self) -> list[MCPToolDef]:
        """Get discovered tools."""
        return list(self._tools)

    async def connect(self) -> None:
        """Connect to the MCP server and discover tools."""
        if not self.server_url:
            logger.warning("No MCP server URL configured")
            return

        try:
            # Import MCP client (optional dependency)
            from mcp import ClientSession
            from mcp.client.sse import sse_client

            # Connect to server
            self._session = ClientSession(*sse_client(self.server_url))
            await self._session.initialize()

            # Discover tools
            tools_result = await self._session.list_tools()
            self._tools = [
                MCPToolDef(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.inputSchema,
                    server_name=self.server_url,
                )
                for tool in tools_result.tools
            ]

            self._connected = True
            logger.info(f"Connected to MCP server, discovered {len(self._tools)} tools")

        except ImportError:
            logger.warning("MCP package not installed. Install with: pip install mcp")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if hasattr(self, "_session"):
            await self._session.close()
        self._connected = False
        self._tools.clear()

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool."""
        if not self._connected:
            raise RuntimeError("MCP client not connected")

        result = await self._session.call_tool(tool_name, arguments)
        return result

    def get_wren_tools(self) -> list[MCPTool]:
        """Get MCP tools wrapped as Wren tools."""
        return [MCPTool(tool, self) for tool in self._tools]
