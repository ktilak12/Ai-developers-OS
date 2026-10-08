import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from agents.coder.tools import CoderTools
from agents.coder.agent import CoderAgent

client = TestClient(app)


def test_coder_tools_path_traversal_and_root_jail():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = CoderTools(temp_dir)

        # 1. Traversal in read_file
        res_read = tools.read_file("../../../secret_file.txt")
        assert "Security Error" in res_read or "escapes" in res_read

        # 2. Traversal in write_file
        res_write = tools.write_file("../../evil.py", "malicious_code = True")
        assert "Security Error" in res_write or "escapes" in res_write

        # 3. Traversal in delete_file
        res_delete = tools.delete_file("../../../boot.ini")
        assert "Security Error" in res_delete or "escapes" in res_delete

        # 4. Traversal in apply_diff_to_file
        res_diff = tools.apply_diff_to_file("../escaped.py", "code")
        assert "Security Error" in res_diff or "escapes" in res_diff

    finally:
        shutil.rmtree(temp_dir)


def test_coder_tools_sensitive_secrets_protection():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = CoderTools(temp_dir)

        # 1. Blocking write to .env or private key
        res_env = tools.write_file(".env", "SECRET=123")
        assert "Security Error" in res_env or "protected" in res_env

        res_key = tools.write_file("id_rsa", "PRIVATE KEY")
        assert "Security Error" in res_key or "protected" in res_key

        # 2. Blocking delete of sensitive file
        res_del_env = tools.delete_file(".env.local")
        assert "Security Error" in res_del_env or "protected" in res_del_env

        # 3. Safe file write and read
        res_safe = tools.write_file("src/utils.py", "def helper(): pass")
        assert "Successfully wrote" in res_safe
        content = tools.read_file("src/utils.py")
        assert "def helper(): pass" in content

    finally:
        shutil.rmtree(temp_dir)


def test_coder_tools_file_size_limits():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = CoderTools(temp_dir)

        # Over-limit write (>5MB)
        huge_payload = "a" * (6 * 1024 * 1024)
        res_write = tools.write_file("huge.txt", huge_payload)
        assert "exceeds maximum write size" in res_write

    finally:
        shutil.rmtree(temp_dir)


def test_coder_agent_plan_execution_and_change_application():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = CoderAgent(temp_dir)

        # 1. Malicious plan with path traversal in affected files should be sanitized
        malicious_plan = {
            "task_request": "Add authentication",
            "affected_files": ["../../etc/passwd", ".env", "apps/api/main.py"]
        }
        mod_res = agent.execute_modification(malicious_plan)
        assert mod_res["status"] == "success"
        # Only safe files should be targeted
        for change in mod_res["changes"]:
            assert ".." not in change["file_path"]
            assert ".env" not in change["file_path"]

        # 2. Apply changes with traversal attempt should be rejected
        unsafe_changes = [
            {"file_path": "../../../injected.py", "new_content": "hacked()"},
            {"file_path": ".env", "new_content": "LEAK=1"}
        ]
        apply_res = agent.apply_changes(unsafe_changes)
        assert apply_res["status"] == "success"
        for result in apply_res["applied_files"]:
            assert "Security Error" in result["status"]

    finally:
        shutil.rmtree(temp_dir)


def test_coder_api_endpoints_validation():
    # 1. /api/agents/coder/modify with empty plan
    res_mod_empty = client.post("/api/agents/coder/modify", json={"plan": {}})
    assert res_mod_empty.status_code == 400

    # 2. /api/agents/coder/modify with invalid directory
    res_mod_bad_dir = client.post("/api/agents/coder/modify", json={
        "plan": {"task_request": "Do something"},
        "directory_path": "/invalid/path/that/does/not/exist"
    })
    assert res_mod_bad_dir.status_code == 400

    # 3. /api/agents/coder/apply with empty changes
    res_apply_empty = client.post("/api/agents/coder/apply", json={"changes": []})
    assert res_apply_empty.status_code == 400

    # 4. /api/agents/coder/apply with over-limit changes (>20)
    over_limit_changes = [{"file_path": f"f_{i}.py", "new_content": "pass"} for i in range(25)]
    res_apply_over = client.post("/api/agents/coder/apply", json={"changes": over_limit_changes})
    assert res_apply_over.status_code == 400
