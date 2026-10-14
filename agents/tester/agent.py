import os
from typing import Dict, Any, List, Optional
from agents.tester.tools import TestingTools
from agents.tester.prompts import TESTER_SYSTEM_PROMPT, TESTER_RETRY_PROMPT
from agents.coder.agent import CoderAgent
from llm.provider import get_llm_provider, LLMMessage


class TestingAgent:
    """
    Testing Agent: Validates changes by executing automated tests inside Docker Sandbox.
    If tests fail, uses an LLM to produce intelligent failure analysis and coordinates
    autonomous retry loops with CoderAgent (up to MAX_ITERATIONS = 3).
    """

    __test__ = False
    MAX_ITERATIONS: int = 3  # Strict limit to prevent infinite agent loops

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.tools = TestingTools(self.root_dir)
        self.coder = CoderAgent(self.root_dir)
        self._llm = None  # lazy init

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    def validate_code(self, test_command: str = "npm test") -> Dict[str, Any]:
        """
        Executes tests inside Docker sandbox and performs LLM-powered failure analysis
        if any failures occur.
        """
        if not test_command or not isinstance(test_command, str):
            test_command = "npm test"
        test_command = test_command.strip()[:500]
        if "\0" in test_command:
            test_command = test_command.replace("\0", "")

        raw_result = self.tools.execute_test(test_command)
        exit_code = raw_result.get("exit_code", 1)
        stdout = raw_result.get("stdout", "")
        stderr = raw_result.get("stderr", "")
        duration = raw_result.get("duration_seconds", 0.0)

        failures = self.tools.extract_failure_details(stdout, stderr)
        passed = exit_code == 0

        analysis = None
        if not passed:
            analysis = self.analyze_failure(test_command, exit_code, stdout, stderr, failures)

        return {
            "status": "passed" if passed else "failed",
            "command": test_command,
            "exit_code": exit_code,
            "duration_seconds": duration,
            "passed": passed,
            "failures": failures,
            "analysis": analysis,
            "test_metrics": raw_result.get("test_metrics", {"passed": 0, "failed": len(failures) or 1}),
            "stdout": stdout,
            "stderr": stderr
        }

    def analyze_failure(
        self,
        command: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        failures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Uses LLM to explain test failure and formulate clear, actionable fix instructions.
        Falls back to heuristic analysis if LLM is unavailable.
        """
        target_file = failures[0].get("file") if failures else "apps/web/src/app/login/page.tsx"
        failure_names = [f.get("name", "") for f in failures[:5]]

        # Build combined output for LLM
        combined_output = f"STDOUT:\n{stdout[:2000]}\n\nSTDERR:\n{stderr[:2000]}"

        user_prompt = f"""Analyze these test failures and provide a root cause and fix instructions.

Test command: {command}
Exit code: {exit_code}
Failing tests: {failure_names}
Target file: {target_file}

Test output:
{combined_output}

Respond with:
1. Root cause (1-2 sentences)
2. Specific fix instructions (numbered steps)
3. Files to check
"""

        llm_root_cause = None
        llm_fix_instructions = None

        try:
            response = self.llm.chat(
                messages=[LLMMessage(role="user", content=user_prompt)],
                system_prompt=TESTER_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=1024,
            )
            if response.provider != "stub" and "[StubProvider]" not in response.content:
                llm_root_cause = response.content.strip()[:1000]
        except Exception:
            pass

        # Heuristic fallback analysis
        heuristic_root_cause = "Test assertion mismatch or unhandled exception during test suite execution."
        if "TS" in stderr or "TS" in stdout:
            heuristic_root_cause = "TypeScript compilation error: Missing property or type mismatch."
        elif "Cannot find module" in stderr or "Cannot find module" in stdout:
            heuristic_root_cause = "Missing dependency or unresolved module import."

        fix_instructions = llm_fix_instructions or (
            f"1. Open {target_file}.\n"
            f"2. Resolve the failing assertion or compile mismatch identified in the test trace.\n"
            f"3. Ensure correct exports and syntax consistency."
        )

        return {
            "root_cause": llm_root_cause or heuristic_root_cause,
            "heuristic_root_cause": heuristic_root_cause,
            "target_file": target_file,
            "failing_tests_count": len(failures) or 1,
            "fix_instructions": fix_instructions,
            "suggested_actions": [
                f"Verify export signatures in {target_file}",
                "Check mock data in test files",
                "Re-run test in Docker Sandbox"
            ],
            "llm_analysis_used": llm_root_cause is not None,
        }

    def run_autonomous_loop(self, task_request: str, test_command: str = "npm test") -> Dict[str, Any]:
        """
        Executes autonomous Coder -> Sandbox -> Tests -> Testing Agent -> Fix loop
        bounded by MAX_ITERATIONS = 3.
        """
        if not task_request or not isinstance(task_request, str) or not task_request.strip():
            task_request = "Run and verify test suite"
        task_request = task_request.strip()[:2000]
        if "\0" in task_request:
            task_request = task_request.replace("\0", "")

        iterations = []
        is_resolved = False

        for current_iter in range(1, self.MAX_ITERATIONS + 1):
            # Step 1: Run tests in Sandbox
            test_res = self.validate_code(test_command)
            iteration_record = {
                "iteration": current_iter,
                "exit_code": test_res.get("exit_code"),
                "passed": test_res.get("passed", False),
                "duration_seconds": test_res.get("duration_seconds", 0.0),
                "failures_count": len(test_res.get("failures", []))
            }

            if test_res.get("passed"):
                is_resolved = True
                iteration_record["action"] = "Tests verified successfully in sandbox."
                iterations.append(iteration_record)
                break

            # Step 2: LLM-powered failure analysis
            analysis = test_res.get("analysis", {})
            iteration_record["failure_reason"] = analysis.get("root_cause")
            iteration_record["target_file"] = analysis.get("target_file")
            iteration_record["llm_analysis_used"] = analysis.get("llm_analysis_used", False)

            # Step 3: Trigger Coder Agent to generate fix using LLM
            coder_fix = self.coder.execute_modification({
                "task_request": f"Fix test failure: {analysis.get('root_cause')}",
                "affected_files": [analysis.get("target_file", "apps/web/src/app/login/page.tsx")],
                "implementation_steps": [analysis.get("fix_instructions", "")]
            })

            iteration_record["coder_action"] = (
                f"Coder Agent generated fix diff for {len(coder_fix.get('changes', []))} file(s). "
                f"LLM provider: {coder_fix.get('llm_provider', 'unknown')}."
            )
            iterations.append(iteration_record)

            if current_iter == self.MAX_ITERATIONS:
                break

        return {
            "status": "success" if is_resolved else "max_iterations_reached",
            "resolved": is_resolved,
            "task_request": task_request,
            "total_iterations": len(iterations),
            "max_iterations_limit": self.MAX_ITERATIONS,
            "iteration_history": iterations,
            "final_status": "PASSED" if is_resolved else "REQUIRES_HUMAN_INSPECTION"
        }

    @staticmethod
    def format_test_metrics_summary(passed_count: int, failed_count: int, duration_sec: float) -> str:
        """Formats a human-readable single-line test execution summary."""
        total = passed_count + failed_count
        pass_pct = round((passed_count / total * 100), 1) if total > 0 else 100.0
        return f"{passed_count}/{total} tests passed ({pass_pct}%) in {duration_sec:.2f}s"
