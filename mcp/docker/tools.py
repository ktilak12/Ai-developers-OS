import os
from typing import Dict, Any
from mcp.protocol import BaseMCPTool, MCPToolSchema, MCPToolParameter, MCPToolResponse
from sandbox.runner.executor import SandboxExecutor

class RunContainerCommandTool(BaseMCPTool):
    name = "run_container_command"
    description = "Execute a command inside the isolated Docker sandbox with resource limits"
    server = "docker"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.executor = SandboxExecutor(self.root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("command", "string", "Command to execute (e.g. 'npm test')", required=True)
            ]
        )

    def execute(self, command: str = "") -> MCPToolResponse:
        if not command or not isinstance(command, str) or not command.strip():
            return MCPToolResponse(success=False, error="Command cannot be empty.", server=self.server, tool_name=self.name)
        if len(command) > 500:
            return MCPToolResponse(success=False, error="Command exceeds maximum length of 500 characters.", server=self.server, tool_name=self.name)
        if "\0" in command:
            return MCPToolResponse(success=False, error="Null bytes are prohibited in command.", server=self.server, tool_name=self.name)

        res = self.executor.execute(command)
        return MCPToolResponse(
            success=res.get("exit_code") == 0,
            data=res,
            error=res.get("stderr") if res.get("exit_code") != 0 else None,
            server=self.server,
            tool_name=self.name
        )

class GetContainerStatusTool(BaseMCPTool):
    name = "get_container_status"
    description = "Inspect Docker sandbox daemon status, resource limits, and security configuration"
    server = "docker"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.executor = SandboxExecutor(self.root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[]
        )

    def execute(self) -> MCPToolResponse:
        status = self.executor.get_status()
        return MCPToolResponse(
            success=True,
            data=status,
            server=self.server,
            tool_name=self.name
        )
