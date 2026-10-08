import os
from typing import Dict, Any, List

class PlannerTools:
    """
    Inspection tools used by Planner Agent to inspect repository state
    before creating implementation plans.
    Includes security guards against directory traversal, sensitive secrets leaks,
    and file size DoS attacks.
    """

    MAX_INSPECT_BYTES = 2 * 1024 * 1024  # 2MB cap
    SENSITIVE_PATTERNS = {
        ".env", ".env.local", ".env.production", ".env.development",
        "id_rsa", "id_ed25519", "credentials.json", "service_account.json",
        "secret.key", "private.key", ".pem", ".pfx", ".pkcs12"
    }

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))

    def _resolve_safe_path(self, rel_path: str) -> str:
        """Resolves path and enforces directory jail and sensitive file shielding."""
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

    def inspect_file(self, rel_path: str) -> str:
        try:
            safe_path = self._resolve_safe_path(rel_path)
            if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
                return f"File {rel_path} not found."

            if os.path.getsize(safe_path) > self.MAX_INSPECT_BYTES:
                return f"Error: File {rel_path} exceeds maximum allowed size ({self.MAX_INSPECT_BYTES} bytes)."

            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(self.MAX_INSPECT_BYTES)
        except PermissionError as pe:
            return f"Security Error: {pe}"
        except Exception as e:
            return f"Error reading file {rel_path}: {e}"

    def get_file_metadata(self, rel_path: str) -> Dict[str, Any]:
        try:
            safe_path = self._resolve_safe_path(rel_path)
            if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
                return {"exists": False}

            stat = os.stat(safe_path)
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines(self.MAX_INSPECT_BYTES)
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "line_count": len(lines),
                "extension": os.path.splitext(rel_path)[1]
            }
        except PermissionError as pe:
            return {"exists": False, "error": f"Security Error: {pe}"}
        except Exception as e:
            return {"exists": False, "error": str(e)}

    def list_directory(self, rel_path: str = "") -> List[str]:
        try:
            safe_path = self._resolve_safe_path(rel_path) if rel_path else self.root_dir
            if not os.path.exists(safe_path) or not os.path.isdir(safe_path):
                return []

            items = os.listdir(safe_path)
            # Filter sensitive files and exclude directories
            safe_items = []
            for item in items:
                lower = item.lower()
                if not any(pat in lower for pat in self.SENSITIVE_PATTERNS):
                    safe_items.append(item)
            return safe_items
        except PermissionError:
            return []
        except Exception:
            return []


