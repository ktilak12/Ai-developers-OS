import re
import ast
from typing import Dict, List, Any

class CodeParser:
    """
    Parses Python and TypeScript/JavaScript files to extract symbols:
    Functions, Classes, Imports, Exports, Routes, Components, and Models.
    Includes security protections: file size guards, extracted symbol caps,
    identifier length bounds, and resilience against malformed ASTs / ReDoS.
    """

    MAX_CODE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB cap
    MAX_SYMBOLS_PER_FILE = 500  # Cap extracted symbols to prevent memory DoS

    @classmethod
    def parse_python(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols: Dict[str, List[Any]] = {
            "functions": [],
            "classes": [],
            "imports": [],
            "routes": [],
            "models": []
        }
        
        if not code or not isinstance(code, str):
            return symbols

        if len(code.encode("utf-8", errors="ignore")) > cls.MAX_CODE_SIZE_BYTES:
            return symbols

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                total_symbols = (
                    len(symbols["functions"]) +
                    len(symbols["classes"]) +
                    len(symbols["routes"]) +
                    len(symbols["models"])
                )
                if total_symbols >= cls.MAX_SYMBOLS_PER_FILE:
                    break

                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_route = False
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                                is_route = True
                                route_path = decorator.args[0].value if decorator.args and isinstance(decorator.args[0], ast.Constant) else ""
                                symbols["routes"].append({
                                    "name": str(node.name)[:200],
                                    "method": decorator.func.attr.upper(),
                                    "path": str(route_path)[:200],
                                    "line": getattr(node, "lineno", 1),
                                    "file": file_path
                                })
                    if not is_route:
                        args_list = [str(arg.arg)[:100] for arg in getattr(node.args, "args", [])[:50]]
                        symbols["functions"].append({
                            "name": str(node.name)[:200],
                            "line": getattr(node, "lineno", 1),
                            "file": file_path,
                            "args": args_list
                        })
                elif isinstance(node, ast.ClassDef):
                    is_model = any(
                        isinstance(base, ast.Name) and base.id in ["BaseModel", "Model", "Base"]
                        for base in node.bases
                    )
                    if is_model:
                        symbols["models"].append({
                            "name": str(node.name)[:200],
                            "line": getattr(node, "lineno", 1),
                            "file": file_path
                        })
                    else:
                        symbols["classes"].append({
                            "name": str(node.name)[:200],
                            "line": getattr(node, "lineno", 1),
                            "file": file_path
                        })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if len(symbols["imports"]) < cls.MAX_SYMBOLS_PER_FILE:
                            symbols["imports"].append(str(alias.name)[:200])
                elif isinstance(node, ast.ImportFrom):
                    if len(symbols["imports"]) < cls.MAX_SYMBOLS_PER_FILE:
                        mod = node.module or ""
                        first_name = node.names[0].name if node.names else ""
                        import_str = f"{mod}.{first_name}" if mod else first_name
                        symbols["imports"].append(str(import_str)[:200])
        except (SyntaxError, MemoryError, RecursionError, ValueError, Exception):
            # Fallback regex parsing if AST fails
            funcs = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*\(', code)[:cls.MAX_SYMBOLS_PER_FILE]
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*\(', code)[:cls.MAX_SYMBOLS_PER_FILE]
            symbols["functions"] = [{"name": f, "file": file_path, "line": 1} for f in funcs]
            symbols["classes"] = [{"name": c, "file": file_path, "line": 1} for c in classes]

        return symbols

    @classmethod
    def parse_typescript(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols: Dict[str, List[Any]] = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": [],
            "components": [],
            "routes": []
        }

        if not code or not isinstance(code, str):
            return symbols

        if len(code.encode("utf-8", errors="ignore")) > cls.MAX_CODE_SIZE_BYTES:
            return symbols

        try:
            # Imports
            import_matches = re.findall(r'import\s+.*?from\s+[\'"]([^\'"\r\n]{1,300})[\'"]', code)
            symbols["imports"] = list(set(import_matches))[:cls.MAX_SYMBOLS_PER_FILE]

            # Exports
            export_matches = re.findall(r'export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})', code)
            symbols["exports"] = list(set(export_matches))[:cls.MAX_SYMBOLS_PER_FILE]

            # React Components (JSX/TSX returning functions)
            component_matches = re.findall(r'(?:export\s+default\s+|export\s+)?function\s+([A-Z][a-zA-Z0-9_]{0,199})\s*\(', code)
            symbols["components"] = list(set(component_matches))[:cls.MAX_SYMBOLS_PER_FILE]

            # Regular Functions
            func_matches = re.findall(r'(?:async\s+)?function\s+([a-z_][a-zA-Z0-9_]{0,199})\s*\(', code)
            const_funcs = re.findall(r'const\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*=\s*(?:async\s+)?\(', code)
            symbols["functions"] = [{"name": f, "file": file_path} for f in list(set(func_matches + const_funcs))[:cls.MAX_SYMBOLS_PER_FILE]]

            # Classes & Interfaces
            class_matches = re.findall(r'(?:class|interface|type)\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})', code)
            symbols["classes"] = [{"name": c, "file": file_path} for c in list(set(class_matches))[:cls.MAX_SYMBOLS_PER_FILE]]

            # App Router Pages/Routes
            if "page.tsx" in file_path or "page.jsx" in file_path or "route.ts" in file_path:
                route_name = file_path.replace("\\", "/").split("src/app/")[-1] if "src/app/" in file_path else file_path
                clean_path = f"/{route_name.replace('/page.tsx', '').replace('/page.jsx', '')}"
                symbols["routes"].append({
                    "path": clean_path[:200],
                    "file": file_path
                })
        except Exception:
            pass

        return symbols

    @classmethod
    def parse_file(cls, file_path: str, content: str) -> Dict[str, Any]:
        if not file_path or not content:
            return {"functions": [], "classes": [], "imports": [], "exports": [], "components": [], "routes": [], "models": []}
        if file_path.endswith(".py"):
            return cls.parse_python(content, file_path)
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return cls.parse_typescript(content, file_path)
        return {"functions": [], "classes": [], "imports": [], "exports": [], "components": [], "routes": [], "models": []}

