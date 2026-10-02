import re
from typing import Dict, Any, Optional
from sandbox.runner.container_runner import DockerContainerRunner
from sandbox.resource_limits.limits import ResourceLimits
from sandbox.policies.command_policy import CommandSecurityPolicy

class SandboxExecutor:
    """
    High-level API for running commands and tests in the sandbox.
    Parses test pass/fail results, tracks execution metrics, and reports container status.
    """

    def __init__(
        self,
        workspace_dir: str,
        limits: Optional[ResourceLimits] = None,
        policy: Optional[CommandSecurityPolicy] = None
    ):
        self.workspace_dir = workspace_dir
        self.runner = DockerContainerRunner(workspace_dir, limits=limits, policy=policy)

    def execute(self, command: str) -> Dict[str, Any]:
        """Execute arbitrary allowed command and parse output metadata."""
        raw_result = self.runner.run_command(command)
        
        # Parse test metrics if command is a test runner
        test_metrics = self._parse_test_metrics(raw_result.get("stdout", "") + "\n" + raw_result.get("stderr", ""))
        
        return {
            **raw_result,
            "passed": raw_result.get("exit_code") == 0,
            "test_metrics": test_metrics,
            "docker_available": self.runner.is_docker_available
        }

    def _parse_test_metrics(self, output: str) -> Dict[str, Any]:
        """Extract passed/failed test counts from output logs."""
        passed_count = 0
        failed_count = 0

        # Jest pattern: Tests: X failed, Y passed, Z total
        jest_match = re.search(r"Tests:\s+(?:(\d+)\s+failed,?\s*)?(?:(\d+)\s+passed,?\s*)?(\d+)\s+total", output)
        if jest_match:
            failed_count = int(jest_match.group(1) or 0)
            passed_count = int(jest_match.group(2) or 0)
            return {"passed": passed_count, "failed": failed_count, "runner": "jest"}

        # Pytest pattern: X passed, Y failed
        pytest_match = re.search(r"(=+)\s*(?:(\d+)\s+passed)?(?:,?\s*(\d+)\s+failed)?.*(=+)", output)
        if pytest_match:
            passed_count = int(pytest_match.group(2) or 0)
            failed_count = int(pytest_match.group(3) or 0)
            return {"passed": passed_count, "failed": failed_count, "runner": "pytest"}

        # Generic fallback based on exit code or basic keywords
        if "PASS" in output or "success" in output.lower():
            passed_count = 1
        if "FAIL" in output or "error" in output.lower():
            failed_count = 1

        return {"passed": passed_count, "failed": failed_count, "runner": "generic"}

    def get_status(self) -> Dict[str, Any]:
        return {
            "docker_daemon_active": self.runner.is_docker_available,
            "active_mode": "docker_container" if self.runner.is_docker_available else "local_process_sandbox",
            "limits": self.runner.limits.to_dict(),
            "policy": self.runner.policy.get_policy_summary()
        }
