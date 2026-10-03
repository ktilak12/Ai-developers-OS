import os
import subprocess
from typing import Dict, Any
from mcp.protocol import BaseMCPTool, MCPToolSchema, MCPToolParameter, MCPToolResponse
from sandbox.policies.command_policy import CommandSecurityPolicy, DEFAULT_COMMAND_POLICY

class ExecuteShellTool(BaseMCPTool):
    name = "execute_shell"
    description = "Execute an audited, allowed command with security policies applied"
    server = "terminal"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.policy = DEFAULT_COMMAND_POLICY

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("command", "string", "Shell command to run (e.g. 'git status')", required=True)
            ]
        )

    def execute(self, command: str = "") -> MCPToolResponse:
        allowed, reason = self.policy.is_command_allowed(command)
        if not allowed:
            return MCPToolResponse(success=False, error=reason, server=self.server, tool_name=self.name)

        try:
            res = subprocess.run(
                command,
                cwd=self.root_dir,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            return MCPToolResponse(
                success=res.returncode == 0,
                data={
                    "command": command,
                    "exit_code": res.returncode,
                    "stdout": res.stdout,
                    "stderr": res.stderr
                },
                server=self.server,
                tool_name=self.name
            )
        except Exception as e:
            return MCPToolResponse(success=False, error=str(e), server=self.server, tool_name=self.name)

class GetEnvironmentTool(BaseMCPTool):
    name = "get_environment"
    description = "Read safe environment variables and workspace path"
    server = "terminal"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[]
        )

    def execute(self) -> MCPToolResponse:
        safe_keys = ["NODE_ENV", "CI", "PATH", "SHELL", "USER", "OS"]
        env_vars = {k: os.environ.get(k, "unset") for k in safe_keys}
        return MCPToolResponse(
            success=True,
            data={
                "workspace_root": self.root_dir,
                "environment": env_vars
            },
            server=self.server,
            tool_name=self.name
        )
