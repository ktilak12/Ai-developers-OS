import os
from typing import Dict, Any, List
from intelligence.parser.code_parser import CodeParser

class CodeIndexer:
    """
    Scans a directory/repository and indexes all symbols, classes, functions, routes,
    components, and dependencies.
    """

    EXCLUDE_DIRS = {"node_modules", ".next", ".git", "__pycache__", "venv", ".venv", "dist", "build"}

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
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

        for root, dirs, files in os.walk(self.root_dir):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")

                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        symbols = CodeParser.parse_file(rel_path, content)
                        self.index["files_scanned"] += 1
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
