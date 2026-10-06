import os
import re
import difflib
from typing import Dict, Any, List

class CoderTools:
    """
    Code Agent tools for reading, creating, editing, and diffing files safely.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def read_file(self, rel_path: str) -> str:
        full_path = os.path.join(self.root_dir, rel_path)
        if not os.path.exists(full_path):
            return f"Error: File {rel_path} does not exist."
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading {rel_path}: {e}"

    def write_file(self, rel_path: str, content: str) -> str:
        full_path = os.path.join(self.root_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {rel_path}"

    def search_code(self, query: str) -> List[Dict[str, Any]]:
        matches = []
        exclude_dirs = {"node_modules", ".next", ".git", "__pycache__", "venv", ".venv"}
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                        for idx, line in enumerate(lines):
                            if query.lower() in line.lower():
                                matches.append({
                                    "file": rel_path,
                                    "line": idx + 1,
                                    "content": line.strip()
                                })
                    except Exception:
                        pass
        return matches[:20]

    def delete_file(self, rel_path: str) -> str:
        full_path = os.path.join(self.root_dir, rel_path)
        if not os.path.exists(full_path):
            return f"Error: File {rel_path} does not exist."
        try:
            os.remove(full_path)
            return f"Successfully deleted file {rel_path}"
        except Exception as e:
            return f"Error deleting file {rel_path}: {e}"

    def search_and_replace(self, rel_path: str, target: str, replacement: str) -> str:
        content = self.read_file(rel_path)
        if content.startswith("Error"):
            return content
        if target not in content:
            return f"Error: Target text not found in {rel_path}"
        new_content = content.replace(target, replacement, 1)
        self.write_file(rel_path, new_content)
        return f"Successfully replaced target in {rel_path}"

    def generate_diff(self, rel_path: str, old_content: str, new_content: str) -> str:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}"
        )
        return "".join(diff)

    def apply_diff_to_file(self, rel_path: str, new_content: str) -> str:
        full_path = os.path.join(self.root_dir, rel_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"Applied changes successfully to {rel_path}"
        except Exception as e:
            return f"Error applying changes to {rel_path}: {e}"

    def compute_diff_stats(self, diff_text: str) -> Dict[str, int]:
        """Calculates additions (+), deletions (-), and total modified lines in a unified diff."""
        additions = 0
        deletions = 0
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
        return {
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions
        }


