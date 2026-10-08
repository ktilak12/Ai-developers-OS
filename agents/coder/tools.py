import os
import re
import difflib
from typing import Dict, Any, List

class CoderTools:
    """
    Code Agent tools for reading, creating, editing, and diffing files safely.
    Includes security guards against path traversal, arbitrary file overwrite/deletion,
    sensitive secrets leaks, and file size exhaustion.
    """

    MAX_READ_BYTES = 2 * 1024 * 1024   # 2MB
    MAX_WRITE_BYTES = 5 * 1024 * 1024  # 5MB
    SENSITIVE_PATTERNS = {
        ".env", ".env.local", ".env.production", ".env.development",
        "id_rsa", "id_ed25519", "credentials.json", "service_account.json",
        "secret.key", "private.key", ".pem", ".pfx", ".pkcs12"
    }

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

    def _resolve_safe_path(self, rel_path: str) -> str:
        """Resolves target path and enforces directory jail and secret file shielding."""
        if not rel_path or not isinstance(rel_path, str) or "\0" in rel_path:
            raise PermissionError("Invalid path specified.")

        full_path = os.path.realpath(os.path.abspath(os.path.join(self.root_dir, rel_path)))
        try:
            if os.path.commonpath([self.root_dir, full_path]) != self.root_dir:
                raise PermissionError(f"Access denied: path '{rel_path}' escapes workspace directory.")
        except ValueError:
            raise PermissionError(f"Access denied: path '{rel_path}' is on a different drive or invalid.")

        base_name = os.path.basename(full_path).lower()
        if any(pat in base_name for pat in self.SENSITIVE_PATTERNS):
            raise PermissionError(f"Access denied: sensitive secret file '{base_name}' is protected.")

        return full_path

    def read_file(self, rel_path: str) -> str:
        try:
            safe_path = self._resolve_safe_path(rel_path)
            if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
                return f"Error: File {rel_path} does not exist."

            if os.path.getsize(safe_path) > self.MAX_READ_BYTES:
                return f"Error: File {rel_path} exceeds maximum allowed size ({self.MAX_READ_BYTES} bytes)."

            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(self.MAX_READ_BYTES)
        except PermissionError as pe:
            return f"Security Error: {pe}"
        except Exception as e:
            return f"Error reading {rel_path}: {e}"

    def write_file(self, rel_path: str, content: str) -> str:
        try:
            safe_path = self._resolve_safe_path(rel_path)
            if len(content.encode("utf-8", errors="ignore")) > self.MAX_WRITE_BYTES:
                return f"Error: Content exceeds maximum write size ({self.MAX_WRITE_BYTES} bytes)."

            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {rel_path}"
        except PermissionError as pe:
            return f"Security Error: {pe}"
        except Exception as e:
            return f"Error writing to {rel_path}: {e}"

    def search_code(self, query: str) -> List[Dict[str, Any]]:
        matches = []
        exclude_dirs = {
            "node_modules", ".next", ".git", "__pycache__", "venv", ".venv",
            "dist", "build", ".memory", ".observability", ".evaluation"
        }
        for root, dirs, files in os.walk(self.root_dir, followlinks=False):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                lower_file = file.lower()
                if any(pat in lower_file for pat in self.SENSITIVE_PATTERNS):
                    continue

                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")
                    try:
                        if os.path.getsize(full_path) > self.MAX_READ_BYTES:
                            continue
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines(self.MAX_READ_BYTES)
                        for idx, line in enumerate(lines):
                            if query.lower() in line.lower():
                                matches.append({
                                    "file": rel_path,
                                    "line": idx + 1,
                                    "content": line.strip()
                                })
                                if len(matches) >= 20:
                                    return matches
                    except Exception:
                        pass
        return matches

    def delete_file(self, rel_path: str) -> str:
        try:
            safe_path = self._resolve_safe_path(rel_path)
            if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
                return f"Error: File {rel_path} does not exist."

            # Ensure we never delete the root directory
            if safe_path == self.root_dir:
                return "Security Error: Cannot delete root workspace directory."

            os.remove(safe_path)
            return f"Successfully deleted file {rel_path}"
        except PermissionError as pe:
            return f"Security Error: {pe}"
        except Exception as e:
            return f"Error deleting file {rel_path}: {e}"

    def search_and_replace(self, rel_path: str, target: str, replacement: str) -> str:
        try:
            content = self.read_file(rel_path)
            if content.startswith("Error") or content.startswith("Security Error"):
                return content
            if target not in content:
                return f"Error: Target text not found in {rel_path}"
            new_content = content.replace(target, replacement, 1)
            return self.write_file(rel_path, new_content)
        except Exception as e:
            return f"Error during search and replace in {rel_path}: {e}"

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
        try:
            safe_path = self._resolve_safe_path(rel_path)
            if len(new_content.encode("utf-8", errors="ignore")) > self.MAX_WRITE_BYTES:
                return f"Error: New content exceeds maximum size ({self.MAX_WRITE_BYTES} bytes)."

            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"Applied changes successfully to {rel_path}"
        except PermissionError as pe:
            return f"Security Error: {pe}"
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



