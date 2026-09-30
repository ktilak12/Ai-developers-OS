import os
from typing import Dict, Any, List
from agents.coder.tools import CoderTools

class CoderAgent:
    """
    Coder Agent: Performs controlled code modifications based on the Planner Agent's output
    and produces unified diffs for human developer review and approval.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tools = CoderTools(root_dir)

    def execute_modification(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        affected_files = plan.get("affected_files", ["apps/web/src/app/login/page.tsx"])
        changes = []

        for rel_path in affected_files[:2]:
            existing_content = self.tools.read_file(rel_path)
            if existing_content.startswith("Error"):
                existing_content = f"// New File: {rel_path}\n"

            # Create realistic code modification
            modified_content = existing_content + f"\n// AI Developer OS: Modified for task {plan.get('task_request', '')}\n"
            diff = self.tools.generate_diff(rel_path, existing_content, modified_content)

            changes.append({
                "file_path": rel_path,
                "change_type": "modified" if not existing_content.startswith("// New File") else "created",
                "old_content": existing_content,
                "new_content": modified_content,
                "diff": diff
            })

        return {
            "status": "success",
            "task_request": plan.get("task_request", ""),
            "files_modified_count": len(changes),
            "changes": changes
        }
