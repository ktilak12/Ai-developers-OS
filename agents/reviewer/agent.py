import os
from typing import Dict, Any, List, Optional
from agents.reviewer.tools import ReviewerTools


class ReviewAgent:
    """
    Review Agent: Acts like a second pair of eyes reviewing code changes,
    architecture consistency, test coverage, and maintainability before human approval.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tools = ReviewerTools(root_dir)

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
            "summary": (
                "Implementation satisfies requirements and passes automated checks."
                if is_approved else
                "Review flagged items that should be addressed before final human sign-off."
            )
        }

    @staticmethod
    def validate_conventional_title(title: str) -> bool:
        """Validates if a Pull Request title conforms to Conventional Commits standards."""
        import re
        pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_-]+\))?:\s.+$"
        return bool(re.match(pattern, title.strip()))
