from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable

@dataclass
class MCPToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None

@dataclass
class MCPToolSchema:
    name: str
    description: str
    server: str
    parameters: List[MCPToolParameter] = field(default_factory=list)

    def to_json_schema(self) -> Dict[str, Any]:
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {
                "type": p.type,
                "description": p.description
            }
            if p.required:
                required.append(p.name)

        return {
            "name": self.name,
            "description": self.description,
            "server": self.server,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

@dataclass
class MCPToolResponse:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    server: str = "generic"
    tool_name: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "server": self.server,
            "tool_name": self.tool_name
        }

class BaseMCPTool:
    """Base class for all standardized Model Context Protocol tools."""
    name: str = "base_tool"
    description: str = "Base MCP Tool"
    server: str = "generic"

    def get_schema(self) -> MCPToolSchema:
        raise NotImplementedError

    def execute(self, **kwargs) -> MCPToolResponse:
        raise NotImplementedError
