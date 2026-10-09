import os
from typing import Dict, Any, List, Optional
from mcp.protocol import BaseMCPTool, MCPToolResponse
from mcp.filesystem.tools import ListFilesTool, ReadFileTool, WriteFileTool, SearchFilesTool
from mcp.github.tools import GetRepositoryTool, CreatePullRequestTool
from mcp.docker.tools import RunContainerCommandTool, GetContainerStatusTool
from mcp.terminal.tools import ExecuteShellTool, GetEnvironmentTool
from mcp.browser.tools import OpenPageTool, ClickElementTool, TypeTextTool, CaptureScreenshotTool


class MCPRegistry:
    """
    Central registry and dispatcher for all Model Context Protocol tools.
    Allows agents to discover and invoke tools without hardcoded API coupling.
    """

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.tools: Dict[str, BaseMCPTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        # Filesystem MCP Server
        self.register(ListFilesTool(self.root_dir))
        self.register(ReadFileTool(self.root_dir))
        self.register(WriteFileTool(self.root_dir))
        self.register(SearchFilesTool(self.root_dir))

        # GitHub MCP Server
        self.register(GetRepositoryTool())
        self.register(CreatePullRequestTool())

        # Docker MCP Server
        self.register(RunContainerCommandTool(self.root_dir))
        self.register(GetContainerStatusTool(self.root_dir))

        # Terminal MCP Server
        self.register(ExecuteShellTool(self.root_dir))
        self.register(GetEnvironmentTool(self.root_dir))

        # Browser MCP Server
        self.register(OpenPageTool(self.root_dir))
        self.register(ClickElementTool(self.root_dir))
        self.register(TypeTextTool(self.root_dir))
        self.register(CaptureScreenshotTool(self.root_dir))


    def register(self, tool: BaseMCPTool):
        self.tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[BaseMCPTool]:
        return self.tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns JSON Schema definitions for all registered MCP tools."""
        return [tool.get_schema().to_json_schema() for tool in self.tools.values()]

    def list_servers(self) -> List[Dict[str, Any]]:
        """Returns registered servers with tool counts."""
        servers: Dict[str, int] = {}
        for tool in self.tools.values():
            servers[tool.server] = servers.get(tool.server, 0) + 1
        return [{"server": s, "tools_count": c} for s, c in servers.items()]

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> MCPToolResponse:
        if not tool_name or not isinstance(tool_name, str) or "\0" in tool_name:
            return MCPToolResponse(
                success=False,
                error="MCP Error: Invalid or empty tool name specified.",
                tool_name=str(tool_name)
            )
        if len(tool_name) > 64:
            return MCPToolResponse(
                success=False,
                error="MCP Error: Tool name exceeds maximum allowed length of 64 characters.",
                tool_name=tool_name[:64]
            )
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return MCPToolResponse(
                success=False,
                error="MCP Error: Tool arguments must be a dictionary.",
                tool_name=tool_name
            )

        tool = self.get_tool(tool_name)
        if not tool:
            return MCPToolResponse(
                success=False,
                error=f"MCP Error: Tool '{tool_name}' not found in registry.",
                tool_name=tool_name
            )
        try:
            return tool.execute(**arguments)
        except Exception as e:
            return MCPToolResponse(
                success=False,
                error=f"MCP Tool Execution Error: {str(e)}",
                server=tool.server,
                tool_name=tool.name
            )

GLOBAL_MCP_REGISTRY: Optional[MCPRegistry] = None

def get_mcp_registry(root_dir: str = ".") -> MCPRegistry:
    global GLOBAL_MCP_REGISTRY
    abs_dir = os.path.abspath(root_dir)
    if GLOBAL_MCP_REGISTRY is None or GLOBAL_MCP_REGISTRY.root_dir != abs_dir:
        GLOBAL_MCP_REGISTRY = MCPRegistry(abs_dir)
    return GLOBAL_MCP_REGISTRY
