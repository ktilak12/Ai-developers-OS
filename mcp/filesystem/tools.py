import os
from typing import Dict, Any, List
from mcp.protocol import BaseMCPTool, MCPToolSchema, MCPToolParameter, MCPToolResponse

class ListFilesTool(BaseMCPTool):
    name = "list_files"
    description = "List files and subdirectories in a relative directory path"
    server = "filesystem"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("directory", "string", "Relative directory path (empty for root)", required=False, default="")
            ]
        )

    def execute(self, directory: str = "") -> MCPToolResponse:
        target = os.path.join(self.root_dir, directory) if directory else self.root_dir
        if not os.path.exists(target):
            return MCPToolResponse(success=False, error=f"Directory '{directory}' does not exist.", server=self.server, tool_name=self.name)
        try:
            items = os.listdir(target)
            return MCPToolResponse(success=True, data={"directory": directory, "items": items[:50]}, server=self.server, tool_name=self.name)
        except Exception as e:
            return MCPToolResponse(success=False, error=str(e), server=self.server, tool_name=self.name)

class ReadFileTool(BaseMCPTool):
    name = "read_file"
    description = "Read full text content of a file"
    server = "filesystem"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("file_path", "string", "Relative path to target file", required=True)
            ]
        )

    def execute(self, file_path: str = "") -> MCPToolResponse:
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            return MCPToolResponse(success=False, error=f"File '{file_path}' not found.", server=self.server, tool_name=self.name)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return MCPToolResponse(success=True, data={"file_path": file_path, "content": content}, server=self.server, tool_name=self.name)
        except Exception as e:
            return MCPToolResponse(success=False, error=str(e), server=self.server, tool_name=self.name)

class WriteFileTool(BaseMCPTool):
    name = "write_file"
    description = "Create or overwrite a file with given text content"
    server = "filesystem"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("file_path", "string", "Relative path of file to write", required=True),
                MCPToolParameter("content", "string", "File text content", required=True)
            ]
        )

    def execute(self, file_path: str = "", content: str = "") -> MCPToolResponse:
        full_path = os.path.join(self.root_dir, file_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return MCPToolResponse(success=True, data={"file_path": file_path, "bytes_written": len(content)}, server=self.server, tool_name=self.name)
        except Exception as e:
            return MCPToolResponse(success=False, error=str(e), server=self.server, tool_name=self.name)

class SearchFilesTool(BaseMCPTool):
    name = "search_files"
    description = "Search codebase for occurrences of a substring"
    server = "filesystem"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("query", "string", "Text substring to search for", required=True)
            ]
        )

    def execute(self, query: str = "") -> MCPToolResponse:
        matches = []
        exclude = {".git", "node_modules", ".next", "__pycache__", "venv"}
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js", ".json", ".md")):
                    f_path = os.path.join(root, file)
                    rel = os.path.relpath(f_path, self.root_dir).replace("\\", "/")
                    try:
                        with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                            for idx, line in enumerate(f.readlines(), 1):
                                if query.lower() in line.lower():
                                    matches.append({"file": rel, "line": idx, "content": line.strip()})
                    except Exception:
                        pass
        return MCPToolResponse(success=True, data={"query": query, "matches": matches[:25]}, server=self.server, tool_name=self.name)
