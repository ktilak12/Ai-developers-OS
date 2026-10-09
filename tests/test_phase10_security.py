import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from mcp.registry import MCPRegistry, get_mcp_registry

client = TestClient(app)


def test_mcp_tools_endpoint_rejects_invalid_directory():
    # /api/mcp/tools with non-existent directory must return 400
    res = client.get("/api/mcp/tools?directory_path=/invalid/non_existent_dir_xyz")
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_mcp_servers_endpoint_rejects_invalid_directory():
    # /api/mcp/servers with non-existent directory must return 400
    res = client.get("/api/mcp/servers?directory_path=/invalid/non_existent_dir_xyz")
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_mcp_call_endpoint_rejects_invalid_directory():
    # /api/mcp/call with non-existent directory must return 400
    res = client.post("/api/mcp/call", json={
        "tool_name": "list_files",
        "arguments": {},
        "directory_path": "/invalid/non_existent_dir_xyz"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_mcp_tools_endpoint_rejects_file_as_directory():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_file.close()
    try:
        res = client.get(f"/api/mcp/tools?directory_path={temp_file.name}")
        assert res.status_code == 400
        assert "not a directory" in res.json()["detail"]
    finally:
        os.unlink(temp_file.name)


def test_mcp_registry_registers_all_expected_servers():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        servers = {s["server"] for s in registry.list_servers()}
        assert "filesystem" in servers
        assert "github" in servers
        assert "docker" in servers
        assert "terminal" in servers
        assert "browser" in servers
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_registry_list_tools_returns_json_schemas():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        tools = registry.list_tools()
        assert len(tools) > 0
        for tool_schema in tools:
            assert "name" in tool_schema
            assert "description" in tool_schema
            assert "inputSchema" in tool_schema
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_registry_call_tool_unknown_returns_error():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        res = registry.call_tool("non_existent_tool_xyz", {})
        assert res.success is False
        assert "not found" in res.error.lower()
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_registry_filesystem_list_files():
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a test file in the temp dir
        open(os.path.join(temp_dir, "hello.py"), "w").close()
        registry = MCPRegistry(temp_dir)
        res = registry.call_tool("list_files", {"directory": ""})
        assert res.success is True
        assert "hello.py" in res.data["items"]
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_registry_filesystem_read_write_roundtrip():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        # Write a file
        write_res = registry.call_tool("write_file", {
            "file_path": "output/test.py",
            "content": "x = 42\n"
        })
        assert write_res.success is True
        assert write_res.data["bytes_written"] == 7

        # Read it back
        read_res = registry.call_tool("read_file", {"file_path": "output/test.py"})
        assert read_res.success is True
        assert read_res.data["content"] == "x = 42\n"
    finally:
        shutil.rmtree(temp_dir)


def test_get_mcp_registry_singleton_respects_root_dir_change():
    # Singleton must return a new registry when root_dir changes
    import mcp.registry as reg_module
    # Reset singleton
    reg_module.GLOBAL_MCP_REGISTRY = None

    dir1 = tempfile.mkdtemp()
    dir2 = tempfile.mkdtemp()
    try:
        r1 = get_mcp_registry(dir1)
        r2 = get_mcp_registry(dir2)
        assert r1.root_dir != r2.root_dir
        assert r1.root_dir == os.path.abspath(dir1)
        assert r2.root_dir == os.path.abspath(dir2)
    finally:
        shutil.rmtree(dir1)
        shutil.rmtree(dir2)
        reg_module.GLOBAL_MCP_REGISTRY = None


def test_get_mcp_registry_singleton_reuses_same_root():
    # Same root_dir must reuse same registry object
    import mcp.registry as reg_module
    reg_module.GLOBAL_MCP_REGISTRY = None

    temp_dir = tempfile.mkdtemp()
    try:
        r1 = get_mcp_registry(temp_dir)
        r2 = get_mcp_registry(temp_dir)
        assert r1 is r2
    finally:
        shutil.rmtree(temp_dir)
        reg_module.GLOBAL_MCP_REGISTRY = None


def test_mcp_api_list_tools_returns_correct_structure():
    res = client.get("/api/mcp/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "tools_count" in data
    assert isinstance(data["tools"], list)
    assert data["tools_count"] > 0


def test_mcp_api_list_servers_returns_correct_structure():
    res = client.get("/api/mcp/servers")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert isinstance(data["servers"], list)
    server_names = {s["server"] for s in data["servers"]}
    assert "filesystem" in server_names
    assert "github" in server_names


def test_mcp_filesystem_path_traversal_jail():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        # Attempt to read outside workspace
        read_res = registry.call_tool("read_file", {"file_path": "../../../etc/passwd"})
        assert read_res.success is False
        assert "escapes workspace" in read_res.error.lower()

        # Attempt to write outside workspace
        write_res = registry.call_tool("write_file", {"file_path": "../../../bad.txt", "content": "owned"})
        assert write_res.success is False
        assert "escapes workspace" in write_res.error.lower()
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_filesystem_shields_sensitive_files():
    temp_dir = tempfile.mkdtemp()
    try:
        with open(os.path.join(temp_dir, ".env"), "w") as f:
            f.write("SECRET=123")
        registry = MCPRegistry(temp_dir)
        read_res = registry.call_tool("read_file", {"file_path": ".env"})
        assert read_res.success is False
        assert "protected" in read_res.error.lower()
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_github_rejects_injection_in_owner():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        res = registry.call_tool("get_repository", {"owner": "evil/../injection", "repo": "main"})
        assert res.success is False
        assert "invalid" in res.error.lower()
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_browser_rejects_dangerous_protocols():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MCPRegistry(temp_dir)
        res = registry.call_tool("open_page", {"url": "file:///etc/passwd"})
        assert res.success is False
        assert "only http and https are allowed" in res.error.lower()
    finally:
        shutil.rmtree(temp_dir)


def test_mcp_api_call_endpoint_rejects_empty_or_oversized_tool_name():
    res = client.post("/api/mcp/call", json={
        "tool_name": "   ",
        "arguments": {}
    })
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]

    res2 = client.post("/api/mcp/call", json={
        "tool_name": "x" * 65,
        "arguments": {}
    })
    assert res2.status_code == 400
    assert "exceeds maximum length" in res2.json()["detail"]

