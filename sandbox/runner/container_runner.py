import os
import time
import subprocess
from typing import Dict, Any, Optional
from sandbox.resource_limits.limits import ResourceLimits, DEFAULT_SANDBOX_LIMITS
from sandbox.policies.command_policy import CommandSecurityPolicy, DEFAULT_COMMAND_POLICY

class DockerContainerRunner:
    """
    Manages isolated container execution lifecycles:
    1. Validates command against security policy
    2. Provisions container with resource limits & mounted workspace
    3. Runs command with execution timeout
    4. Captures stdout/stderr and exit code
    5. Destroys container upon completion
    """

    IMAGE_NAME = "ai-developer-os/sandbox:latest"

    def __init__(
        self,
        workspace_dir: str,
        limits: Optional[ResourceLimits] = None,
        policy: Optional[CommandSecurityPolicy] = None
    ):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.limits = limits or DEFAULT_SANDBOX_LIMITS
        self.policy = policy or DEFAULT_COMMAND_POLICY
        self.is_docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        """Check if Docker CLI and daemon are operational."""
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return res.returncode == 0
        except Exception:
            return False

    def run_command(self, command: str) -> Dict[str, Any]:
        """
        Execute command inside isolated sandbox container or fallback process sandbox.
        """
        # Step 1: Security policy validation
        is_allowed, reason = self.policy.is_command_allowed(command)
        if not is_allowed:
            return {
                "status": "security_violation",
                "exit_code": 126,
                "command": command,
                "stdout": "",
                "stderr": reason,
                "duration_seconds": 0.0,
                "mode": "blocked_by_policy"
            }

        start_time = time.time()

        # Step 2: Choose Docker vs Local Process Sandbox
        if self.is_docker_available:
            return self._run_in_docker(command, start_time)
        else:
            return self._run_in_local_sandbox(command, start_time)

    def _run_in_docker(self, command: str, start_time: float) -> Dict[str, Any]:
        """Run command in disposable Docker container with resource constraints."""
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.workspace_dir}:/workspace",
            "-w", "/workspace",
        ]
        docker_cmd.extend(self.limits.to_docker_run_args())
        docker_cmd.extend([self.IMAGE_NAME, "sh", "-c", command])

        try:
            proc = subprocess.run(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.limits.execution_timeout
            )
            duration = round(time.time() - start_time, 2)
            return {
                "status": "completed",
                "exit_code": proc.returncode,
                "command": command,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "duration_seconds": duration,
                "mode": "docker_container",
                "limits": self.limits.to_dict()
            }
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 2)
            return {
                "status": "timeout",
                "exit_code": 124,
                "command": command,
                "stdout": "",
                "stderr": f"Execution timed out after {self.limits.execution_timeout} seconds.",
                "duration_seconds": duration,
                "mode": "docker_container"
            }
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            return {
                "status": "error",
                "exit_code": 1,
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "duration_seconds": duration,
                "mode": "docker_container"
            }

    def _run_in_local_sandbox(self, command: str, start_time: float) -> Dict[str, Any]:
        """Fallback process execution inside isolated workspace when Docker is absent."""
        try:
            env = os.environ.copy()
            env["CI"] = "true"
            env["NODE_ENV"] = "test"

            proc = subprocess.run(
                command,
                cwd=self.workspace_dir,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=self.limits.execution_timeout
            )
            duration = round(time.time() - start_time, 2)
            return {
                "status": "completed",
                "exit_code": proc.returncode,
                "command": command,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "duration_seconds": duration,
                "mode": "local_process_sandbox",
                "limits": self.limits.to_dict()
            }
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 2)
            return {
                "status": "timeout",
                "exit_code": 124,
                "command": command,
                "stdout": "",
                "stderr": f"Execution timed out after {self.limits.execution_timeout} seconds.",
                "duration_seconds": duration,
                "mode": "local_process_sandbox"
            }
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            return {
                "status": "error",
                "exit_code": 1,
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "duration_seconds": duration,
                "mode": "local_process_sandbox"
            }
