import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from agents.tester.agent import TestingAgent
from agents.tester.tools import TestingTools

client = TestClient(app)


def test_tester_validate_endpoint_rejects_invalid_directory():
    # /api/agents/tester/validate with a non-existent directory must return 400
    res = client.post("/api/agents/tester/validate", json={
        "command": "npm test",
        "directory_path": "/invalid/non_existent_dir_xyz"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_tester_loop_endpoint_rejects_invalid_directory():
    # /api/agents/tester/loop with a non-existent directory must return 400
    res = client.post("/api/agents/tester/loop", json={
        "task_request": "Fix tests",
        "command": "npm test",
        "directory_path": "/invalid/non_existent_dir_xyz"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_tester_validate_endpoint_rejects_file_as_directory():
    # Pointing to a file instead of a directory must return 400
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_file.close()
    try:
        res = client.post("/api/agents/tester/validate", json={
            "command": "npm test",
            "directory_path": temp_file.name
        })
        assert res.status_code == 400
        assert "not a directory" in res.json()["detail"]
    finally:
        os.unlink(temp_file.name)


def test_tester_format_test_metrics_summary():
    # Static helper must produce correctly formatted summary string
    summary = TestingAgent.format_test_metrics_summary(
        passed_count=18, failed_count=2, duration_sec=4.321
    )
    assert "18/20" in summary
    assert "90.0%" in summary
    assert "4.32s" in summary


def test_tester_format_test_metrics_no_tests():
    # Zero total tests must not divide by zero; pass rate must default to 100%
    summary = TestingAgent.format_test_metrics_summary(
        passed_count=0, failed_count=0, duration_sec=0.0
    )
    assert "100.0%" in summary


def test_tester_tools_extract_jest_failures():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = TestingTools(temp_dir)
        stdout = "FAIL apps/web/src/__tests__/Login.test.tsx\n. Login renders correctly"
        failures = tools.extract_failure_details(stdout, "")
        assert len(failures) >= 1
        assert failures[0]["type"] == "jest"
        assert "Login.test.tsx" in failures[0]["file"]
    finally:
        shutil.rmtree(temp_dir)


def test_tester_tools_extract_pytest_failures():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = TestingTools(temp_dir)
        stderr = "FAILED tests/test_api.py::test_login_returns_200"
        failures = tools.extract_failure_details("", stderr)
        assert len(failures) >= 1
        assert failures[0]["type"] == "pytest"
        assert failures[0]["test_name"] == "test_login_returns_200"
    finally:
        shutil.rmtree(temp_dir)


def test_tester_tools_extract_typescript_errors():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = TestingTools(temp_dir)
        stderr = "apps/web/src/app/login/page.tsx(42,10): error TS2345: Type mismatch."
        failures = tools.extract_failure_details("", stderr)
        assert len(failures) >= 1
        assert failures[0]["type"] == "typescript"
        assert failures[0]["line"] == 42
    finally:
        shutil.rmtree(temp_dir)


def test_tester_tools_extract_runtime_error_fallback():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = TestingTools(temp_dir)
        stderr = "Error: Cannot connect to database"
        failures = tools.extract_failure_details("", stderr)
        assert len(failures) >= 1
        assert failures[0]["type"] == "runtime_error"
    finally:
        shutil.rmtree(temp_dir)


def test_testing_agent_autonomous_loop_respects_max_iterations():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = TestingAgent(temp_dir)
        assert agent.MAX_ITERATIONS == 3

        result = agent.run_autonomous_loop("Fix login tests", "npm test")
        # Loop must never exceed MAX_ITERATIONS iterations
        assert result["total_iterations"] <= agent.MAX_ITERATIONS
        assert result["max_iterations_limit"] == 3
        assert "final_status" in result
        assert result["status"] in ("success", "max_iterations_reached")
    finally:
        shutil.rmtree(temp_dir)


def test_tester_validate_endpoint_rejects_oversized_command():
    res = client.post("/api/agents/tester/validate", json={
        "command": "npm test " + "x" * 501
    })
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]


def test_tester_validate_endpoint_rejects_null_byte_command():
    res = client.post("/api/agents/tester/validate", json={
        "command": "npm test\0malicious"
    })
    assert res.status_code == 400
    assert "Null bytes are prohibited" in res.json()["detail"]


def test_tester_loop_endpoint_rejects_empty_task_request():
    res = client.post("/api/agents/tester/loop", json={
        "task_request": "   ",
        "command": "npm test"
    })
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


def test_tester_loop_endpoint_rejects_oversized_task_request():
    res = client.post("/api/agents/tester/loop", json={
        "task_request": "fix " * 600,
        "command": "npm test"
    })
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]

