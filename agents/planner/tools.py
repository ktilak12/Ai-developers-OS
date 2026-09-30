import os
from typing import Dict, Any, List

class PlannerTools:
    """
    Inspection tools used by Planner Agent to inspect repository state
    before creating implementation plans.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def inspect_file(self, rel_path: str) -> str:
        full_path = os.path.join(self.root_dir, rel_path)
        if not os.path.exists(full_path):
            return f"File {rel_path} not found."
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {rel_path}: {e}"

    def list_directory(self, rel_path: str = "") -> List[str]:
        full_path = os.path.join(self.root_dir, rel_path) if rel_path else self.root_dir
        if not os.path.exists(full_path):
            return []
        try:
            return os.listdir(full_path)
        except Exception:
            return []
