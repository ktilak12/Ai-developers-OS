import os
from typing import Dict, Any, List


class ReviewerTools:
    """Tools for evaluating code changes, architecture rules, and static quality."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def analyze_diff(self, diff_text: str) -> Dict[str, Any]:
        """Analyzes a unified git diff for common code smells or deficiencies."""
        lines = diff_text.splitlines()
        additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))

        smells = []
        if additions > 500:
            smells.append("High change volume in single task (> 500 lines modified). Consider splitting.")
        if "console.log" in diff_text or "print(" in diff_text:
            smells.append("Debug print/console statement detected in proposed code change.")
        if "TODO" in diff_text or "FIXME" in diff_text:
            smells.append("Unresolved TODO/FIXME markers present in diff.")
        if "except Exception:" in diff_text or "catch (e) {}" in diff_text:
            smells.append("Broad or empty exception handling block detected.")

        return {
            "additions": additions,
            "deletions": deletions,
            "total_changed_lines": additions + deletions,
            "detected_smells": smells
        }
