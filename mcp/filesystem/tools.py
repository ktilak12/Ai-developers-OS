import os
from typing import Dict, Any, List, Optional
from mcp.protocol import BaseMCPTool, MCPToolSchema, MCPToolParameter, MCPToolResponse

SENSITIVE_PATTERNS = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", "credentials.json", "service_account.json",
    "secret.key", "private.key", ".pem", ".pfx", ".pkcs12"
}

MAX_READ_BYTES = 1_000_000
MAX_WRITE_BYTES = 2_000_000


def resolve_safe_mcp_path(root_dir: str, rel_path: str, allow_missing: bool = False) -> str:
    """Enforces workspace jail and shields sensitive secrets."""
    if not isinstance(rel_path, str) or "\0" in rel_path:
        raise PermissionError("Invalid path specified.")

    real_root = os.path.realpath(os.path.abspath(root_dir))
    full_path = os.path.realpath(os.path.abspath(os.path.join(real_root, rel_path.lstrip("/\\") if rel_path else "")))

    try:
        if os.path.commonpath([real_root, full_path]) != real_root:
            raise PermissionError(f"Access denied: path '{rel_path}' escapes workspace directory.")
    except ValueError:
        raise PermissionError(f"Access denied: path '{rel_path}' is on a different drive or invalid.")

    base_name = os.path.basename(full_path).lower()
    if any(pat in base_name for pat in SENSITIVE_PATTERNS):
        raise PermissionError(f"Access denied: sensitive secret file '{base_name}' is protected.")

    return full_path


class ListFilesTool(BaseMCPTool):
    name = "list_files"
    description = "List files and subdirectories in a relative directory path"
    server = "filesystem"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

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
        try:
            target = resolve_safe_mcp_path(self.root_dir, directory)
        except PermissionError as pe:
            return MCPToolResponse(success=False, error=str(pe), server=self.server, tool_name=self.name)

        if not os.path.exists(target):
            return MCPToolResponse(success=False, error=f"Directory '{directory}' does not exist.", server=self.server, tool_name=self.name)
        if not os.path.isdir(target):
            return MCPToolResponse(success=False, error=f"Path '{directory}' is not a directory.", server=self.server, tool_name=self.name)
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
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

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
        try:
            full_path = resolve_safe_mcp_path(self.root_dir, file_path)
        except PermissionError as pe:
            return MCPToolResponse(success=False, error=str(pe), server=self.server, tool_name=self.name)

        if not os.path.exists(full_path):
            return MCPToolResponse(success=False, error=f"File '{file_path}' not found.", server=self.server, tool_name=self.name)
        if not os.path.isfile(full_path):
            return MCPToolResponse(success=False, error=f"Path '{file_path}' is not a file.", server=self.server, tool_name=self.name)
        try:
            if os.path.getsize(full_path) > MAX_READ_BYTES:
                return MCPToolResponse(success=False, error=f"File exceeds maximum allowed size ({MAX_READ_BYTES} bytes).", server=self.server, tool_name=self.name)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(MAX_READ_BYTES)
            return MCPToolResponse(success=True, data={"file_path": file_path, "content": content}, server=self.server, tool_name=self.name)
        except Exception as e:
            return MCPToolResponse(success=False, error=str(e), server=self.server, tool_name=self.name)


class WriteFileTool(BaseMCPTool):
    name = "write_file"
    description = "Create or overwrite a file with given text content"
    server = "filesystem"

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

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
        if not isinstance(content, str):
            return MCPToolResponse(success=False, error="Content must be a string.", server=self.server, tool_name=self.name)
        if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
            return MCPToolResponse(success=False, error=f"Content exceeds maximum write size ({MAX_WRITE_BYTES} bytes).", server=self.server, tool_name=self.name)

        try:
            full_path = resolve_safe_mcp_path(self.root_dir, file_path, allow_missing=True)
        except PermissionError as pe:
            return MCPToolResponse(success=False, error=str(pe), server=self.server, tool_name=self.name)

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
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

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
        if not query or not isinstance(query, str) or "\0" in query:
            return MCPToolResponse(success=False, error="Invalid search query.", server=self.server, tool_name=self.name)
        if len(query) > 200:
            query = query[:200]

        matches = []
        exclude = {".git", "node_modules", ".next", "__pycache__", "venv"}
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if any(pat in file.lower() for pat in SENSITIVE_PATTERNS):
                    continue
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
