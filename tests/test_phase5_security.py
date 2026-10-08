import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from agents.planner.tools import PlannerTools
from agents.planner.agent import PlannerAgent

client = TestClient(app)


def test_planner_tools_path_traversal_protection():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = PlannerTools(temp_dir)

        # 1. Path traversal outside root directory
        res_traversal = tools.inspect_file("../../../secret.txt")
        assert "Security Error" in res_traversal or "escapes" in res_traversal

        # 2. Metadata inspection traversal
        meta_traversal = tools.get_file_metadata("../../../etc/passwd")
        assert meta_traversal["exists"] is False
        assert "Security Error" in meta_traversal.get("error", "")

        # 3. Directory listing traversal
        list_traversal = tools.list_directory("../../")
        assert list_traversal == []

    finally:
        shutil.rmtree(temp_dir)


def test_planner_tools_sensitive_secrets_shielding():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = PlannerTools(temp_dir)

        # Create sensitive files
        env_file = os.path.join(temp_dir, ".env")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("DB_PASSWORD=secret123\n")

        cert_file = os.path.join(temp_dir, "private.key")
        with open(cert_file, "w", encoding="utf-8") as f:
            f.write("-----BEGIN PRIVATE KEY-----\n")

        # Create normal code file
        code_file = os.path.join(temp_dir, "index.ts")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("console.log('safe code');\n")

        # Inspecting sensitive files should be blocked
        res_env = tools.inspect_file(".env")
        assert "Security Error" in res_env or "protected" in res_env

        res_cert = tools.inspect_file("private.key")
        assert "Security Error" in res_cert or "protected" in res_cert

        # Inspecting normal code file should succeed
        res_code = tools.inspect_file("index.ts")
        assert "console.log" in res_code

        # List directory should filter out sensitive files
        dir_items = tools.list_directory("")
        assert "index.ts" in dir_items
        assert ".env" not in dir_items
        assert "private.key" not in dir_items

    finally:
        shutil.rmtree(temp_dir)


def test_planner_tools_file_size_limit():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = PlannerTools(temp_dir)

        # Create oversized file (3MB)
        large_file = os.path.join(temp_dir, "large.txt")
        with open(large_file, "w", encoding="utf-8") as f:
            f.write("x" * (3 * 1024 * 1024))

        res_large = tools.inspect_file("large.txt")
        assert "exceeds maximum allowed size" in res_large

    finally:
        shutil.rmtree(temp_dir)


def test_planner_agent_plan_generation_robustness():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = PlannerAgent(temp_dir)

        # 1. Clean plan generation
        plan = agent.generate_plan("Implement user profile dashboard")
        assert plan["task_request"] == "Implement user profile dashboard"
        assert len(plan["structured_steps"]) > 0
        assert plan["developer_approval_required"] is True

        # 2. Empty task request should fallback safely
        plan_empty = agent.generate_plan("")
        assert len(plan_empty["structured_steps"]) > 0

        # 3. Oversized task request (>5000 chars) is clamped safely
        huge_task = "Task " * 2000
        plan_huge = agent.generate_plan(huge_task)
        assert len(plan_huge["task_request"]) <= 5000

    finally:
        shutil.rmtree(temp_dir)


def test_planner_api_endpoint_validation():
    # 1. Valid plan request
    res_valid = client.post("/api/agents/planner/plan", json={"task_request": "Refactor auth middleware"})
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert "structured_steps" in data
    assert data["developer_approval_required"] is True

    # 2. Empty task request should return 400
    res_empty = client.post("/api/agents/planner/plan", json={"task_request": "   "})
    assert res_empty.status_code == 400
    assert "cannot be empty" in res_empty.json()["detail"]

    # 3. Oversized task request (>5000 chars) should return 400
    huge_request = "x" * 6000
    res_oversized = client.post("/api/agents/planner/plan", json={"task_request": huge_request})
    assert res_oversized.status_code == 400
    assert "exceeds maximum allowed length" in res_oversized.json()["detail"]

    # 4. Non-existent directory path should return 400
    res_bad_dir = client.post("/api/agents/planner/plan", json={
        "task_request": "Update styles",
        "directory_path": "/invalid/non_existent_folder_abc123"
    })
    assert res_bad_dir.status_code == 400
