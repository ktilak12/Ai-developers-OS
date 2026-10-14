import os
from typing import Dict, Any, List, Optional
from agents.reviewer.tools import ReviewerTools
from llm.provider import get_llm_provider, LLMMessage


REVIEWER_SYSTEM_PROMPT = """You are an expert Code Reviewer for the AI Developer OS platform.
Your role is to review code changes and provide constructive, developer-focused feedback.

Review criteria:
1. Correctness: Does the code solve the stated task?
2. Security: Are there any security risks or vulnerabilities introduced?
3. Performance: Are there obvious performance concerns?
4. Maintainability: Is the code readable, well-structured, and following project conventions?
5. Test coverage: Are adequate tests included or required?
6. Breaking changes: Does this change any public API or behavior?

Always provide:
- An overall verdict (APPROVED / CHANGES_REQUESTED)
- Specific, actionable feedback for each concern
- Priority ratings for each issue (BLOCKING / IMPORTANT / SUGGESTION)
"""


class ReviewAgent:
    """
    Review Agent: Acts like a second pair of eyes reviewing code changes,
    architecture consistency, test coverage, and maintainability before human approval.
    Uses an LLM provider to generate intelligent, context-aware code reviews.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tools = ReviewerTools(root_dir)
        self._llm = None  # lazy init

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    def review_changes(
        self,
        task_request: str,
        files_changed: List[str],
        diff_summary: str = "",
        test_passed: bool = True,
        security_findings_count: int = 0
    ) -> Dict[str, Any]:
        """Performs comprehensive code review on generated changes."""
        analysis = self.tools.analyze_diff(diff_summary) if diff_summary else {
            "additions": 35,
            "deletions": 5,
            "total_changed_lines": 40,
            "detected_smells": []
        }

        checklist = []
        warnings = []
        suggested_changes = []

        # Check logic & tests
        if test_passed:
            checklist.append({"item": "Automated Tests Passing", "passed": True})
        else:
            checklist.append({"item": "Automated Tests Passing", "passed": False})
            warnings.append("Changes currently cause failing unit or integration tests.")

        # Check security
        if security_findings_count == 0:
            checklist.append({"item": "No Critical Security Findings", "passed": True})
        else:
            checklist.append({"item": "No Critical Security Findings", "passed": False})
            warnings.append(f"{security_findings_count} security warning(s) detected.")

        # Check diff metrics
        has_tests = any("test" in f.lower() for f in files_changed)
        checklist.append({"item": "Dedicated Test Files Included", "passed": has_tests})
        if not has_tests:
            warnings.append("No explicit test files were modified or added alongside implementation.")
            suggested_changes.append("Add unit tests covering the new branch conditions.")

        for smell in analysis.get("detected_smells", []):
            warnings.append(smell)
            suggested_changes.append(f"Resolve detected issue: {smell}")

        # Review approval status
        is_approved = test_passed and security_findings_count == 0 and len(warnings) <= 1

        # LLM-powered review commentary
        llm_review = None
        if diff_summary:
            llm_review = self._generate_llm_review(
                task_request, files_changed, diff_summary, test_passed, security_findings_count
            )

        # Merge LLM verdict if available and more strict
        if llm_review and llm_review.get("verdict") == "CHANGES_REQUESTED":
            is_approved = False
            if llm_review.get("blocking_issues"):
                for issue in llm_review["blocking_issues"]:
                    warnings.append(f"[LLM Review] {issue}")

        return {
            "status": "APPROVED" if is_approved else "CHANGES_REQUESTED",
            "task_request": task_request,
            "files_reviewed": files_changed,
            "diff_stats": {
                "additions": analysis.get("additions", 0),
                "deletions": analysis.get("deletions", 0)
            },
            "checklist": checklist,
            "warnings": warnings,
            "suggested_changes": suggested_changes,
            "llm_review": llm_review,
            "summary": (
                "Implementation satisfies requirements and passes automated checks."
                if is_approved else
                "Review flagged items that should be addressed before final human sign-off."
            )
        }

    def _generate_llm_review(
        self,
        task_request: str,
        files_changed: List[str],
        diff_summary: str,
        test_passed: bool,
        security_findings_count: int,
    ) -> Optional[Dict[str, Any]]:
        """Calls LLM for an intelligent code review of the diff."""
        user_prompt = f"""Review this code change for the following task:
Task: {task_request}

Files changed: {', '.join(files_changed)}
Tests passed: {test_passed}
Security findings: {security_findings_count}

Diff:
{diff_summary[:4000]}

Provide:
1. Overall verdict: APPROVED or CHANGES_REQUESTED
2. List of blocking issues (must fix before merge), if any
3. List of important suggestions (should fix)
4. List of minor suggestions (nice to have)
5. Brief overall assessment (2-3 sentences)
"""

        try:
            response = self.llm.chat(
                messages=[LLMMessage(role="user", content=user_prompt)],
                system_prompt=REVIEWER_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=2048,
            )

            if response.provider == "stub" or "[StubProvider]" in response.content:
                return None

            text = response.content.strip()

            # Parse verdict from response
            verdict = "CHANGES_REQUESTED"
            if "APPROVED" in text.upper() and "CHANGES_REQUESTED" not in text.upper():
                verdict = "APPROVED"
            elif "APPROVED" in text.upper() and "CHANGES_REQUESTED" in text.upper():
                # Both present — defer to position
                if text.upper().index("APPROVED") < text.upper().index("CHANGES_REQUESTED"):
                    verdict = "APPROVED"

            # Extract blocking issues (lines starting with "BLOCKING:" or numbered with "blocking")
            blocking_issues = []
            for line in text.splitlines():
                line_stripped = line.strip()
                if any(kw in line_stripped.upper() for kw in ("BLOCKING", "MUST FIX", "CRITICAL")):
                    clean = line_stripped.lstrip("0123456789.-) ").strip()
                    if clean and len(clean) > 10:
                        blocking_issues.append(clean[:300])

            return {
                "provider": response.provider,
                "model": response.model,
                "verdict": verdict,
                "raw_review": text,
                "blocking_issues": blocking_issues[:5],
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            }

        except Exception:
            return None

    @staticmethod
    def validate_conventional_title(title: str) -> bool:
        """Validates if a Pull Request title conforms to Conventional Commits standards."""
        import re
        pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_-]+\))?:\s.+$"
        return bool(re.match(pattern, title.strip()))
