import os
from typing import Dict, Any, List
from intelligence.parser.code_parser import CodeParser

class CodeIndexer:
    """
    Scans a directory/repository and indexes all symbols, classes, functions, routes,
    components, and dependencies with built-in security protections against directory traversal,
    symlink escapes, sensitive secret leaks, and memory exhaustion.
    """

    EXCLUDE_DIRS = {
        "node_modules", ".next", ".git", "__pycache__", "venv", ".venv",
        "dist", "build", ".memory", ".observability", ".evaluation"
    }

    # Security: Sensitive files and secrets to exclude from indexing
    SENSITIVE_PATTERNS = {
        ".env", ".env.local", ".env.production", ".env.development",
        "id_rsa", "id_ed25519", "credentials.json", "service_account.json",
        "secret.key", "private.key", ".pem", ".pfx", ".pkcs12"
    }

    # Security: Max file size (2 MB) to prevent ReDoS / Memory exhaustion DoS
    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
    MAX_FILES_LIMIT = 2500

    def __init__(self, root_dir: str):
        # Security: Canonicalize root path to prevent traversal
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))
        self.index = {
            "files_scanned": 0,
            "functions": [],
            "classes": [],
            "components": [],
            "routes": [],
            "models": [],
            "imports": [],
            "file_symbols_map": {}
        }

    def _is_safe_file(self, full_path: str, filename: str) -> bool:
        """Verifies that the target file is inside the root directory and is safe to index."""
        # Check sensitive filenames and extensions
        lower_name = filename.lower()
        if any(pat in lower_name for pat in self.SENSITIVE_PATTERNS):
            return False

        # Check symlink or path traversal escape from root jail
        try:
            real_path = os.path.realpath(full_path)
            if os.path.commonpath([self.root_dir, real_path]) != self.root_dir:
                return False
        except Exception:
            return False

        # Check file size limit
        try:
            if os.path.getsize(full_path) > self.MAX_FILE_SIZE_BYTES:
                return False
        except Exception:
            return False

        return True

    def scan_and_index(self) -> Dict[str, Any]:
        self.index = {
            "files_scanned": 0,
            "functions": [],
            "classes": [],
            "components": [],
            "routes": [],
            "models": [],
            "imports": [],
            "file_symbols_map": {}
        }

        files_counted = 0

        for root, dirs, files in os.walk(self.root_dir, followlinks=False):
            # Security: Exclude unwanted / private runtime directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for file in files:
                if files_counted >= self.MAX_FILES_LIMIT:
                    break

                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                    full_path = os.path.join(root, file)
                    
                    if not self._is_safe_file(full_path, file):
                        continue

                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")

                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read(self.MAX_FILE_SIZE_BYTES)

                        symbols = CodeParser.parse_file(rel_path, content)
                        self.index["files_scanned"] += 1
                        files_counted += 1
                        self.index["file_symbols_map"][rel_path] = symbols

                        # Aggregate global symbol tables
                        for func in symbols.get("functions", []):
                            self.index["functions"].append(func if isinstance(func, dict) else {"name": func, "file": rel_path})
                        
                        for cls in symbols.get("classes", []):
                            self.index["classes"].append(cls if isinstance(cls, dict) else {"name": cls, "file": rel_path})
                        
                        for comp in symbols.get("components", []):
                            self.index["components"].append({"name": comp, "file": rel_path})

                        for r in symbols.get("routes", []):
                            self.index["routes"].append(r if isinstance(r, dict) else {"path": str(r), "file": rel_path})

                        for m in symbols.get("models", []):
                            self.index["models"].append(m if isinstance(m, dict) else {"name": str(m), "file": rel_path})

                        self.index["imports"].extend(symbols.get("imports", []))

                    except Exception as e:
                        print(f"Error indexing file {rel_path}: {e}")

        # Unique imports
        self.index["imports"] = list(set(self.index["imports"]))
        return self.index
