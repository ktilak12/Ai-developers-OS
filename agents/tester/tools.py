import os
import re
from typing import Dict, Any, List, Optional
from sandbox.runner.executor import SandboxExecutor

class TestingTools:
    """
    Tools utilized by the Testing Agent to run test suites in the Docker Sandbox,
    extract stack traces, and isolate failure points for the Coder Agent.
    """

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.sandbox = SandboxExecutor(self.root_dir)

    def execute_test(self, command: str = "npm test") -> Dict[str, Any]:
        """Runs the specified test command inside the isolated sandbox."""
        return self.sandbox.execute(command)

    def run_type_check(self) -> Dict[str, Any]:
        """Runs TypeScript compiler check (npm run build)."""
        return self.sandbox.execute("npm run build")

    def run_linter(self) -> Dict[str, Any]:
        """Runs linter check (npm run lint)."""
        return self.sandbox.execute("npm run lint")

    def extract_failure_details(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """
        Parses test output logs to locate failing test suites, error messages,
        and offending file paths/lines.
        """
        combined = f"{stdout}\n{stderr}"
        failures = []

        # Jest failure regex: FAIL path/to/file.test.ts
        jest_fails = re.findall(r"FAIL\s+([\w\-\./\\]+\.(?:test|spec)\.[jt]sx?)", combined)
        for f in set(jest_fails):
            failures.append({
                "type": "jest",
                "file": f.replace("\\", "/"),
                "summary": "Test suite assertion failure in Jest/Vitest."
            })

        # Pytest failure regex: FAILED path/to/test_file.py::test_func
        pytest_fails = re.findall(r"FAILED\s+([\w\-\./\\]+\.py)::(\w+)", combined)
        for file_path, test_name in pytest_fails:
            failures.append({
                "type": "pytest",
                "file": file_path.replace("\\", "/"),
                "test_name": test_name,
                "summary": f"Pytest function {test_name} failed."
            })

        # TypeScript compile error regex: path/to/file.tsx(line,col): error TS...
        ts_errors = re.findall(r"([\w\-\./\\]+\.[jt]sx?)\((\d+),\d+\):\s+error\s+(TS\d+:\s+[^\n]+)", combined)
        for file_path, line, msg in ts_errors:
            failures.append({
                "type": "typescript",
                "file": file_path.replace("\\", "/"),
                "line": int(line),
                "summary": msg.strip()
            })

        # Generic syntax or unhandled exception fallback
        if not failures and ("Error:" in combined or "Exception:" in combined):
            error_lines = [l.strip() for l in combined.splitlines() if "Error:" in l or "Exception:" in l]
            failures.append({
                "type": "runtime_error",
                "file": "unknown",
                "summary": error_lines[0] if error_lines else "General test execution failure detected."
            })

        return failures
