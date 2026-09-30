import re
import ast
from typing import Dict, List, Any

class CodeParser:
    """
    Parses Python and TypeScript/JavaScript files to extract symbols:
    Functions, Classes, Imports, Exports, Routes, Components, and Models.
    """

    @staticmethod
    def parse_python(code: str, file_path: str) -> Dict[str, Any]:
        symbols = {
            "functions": [],
            "classes": [],
            "imports": [],
            "routes": [],
            "models": []
        }
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Check if function has a decorator indicating a route (e.g., @app.get)
                    is_route = False
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                                is_route = True
                                route_path = decorator.args[0].value if decorator.args and isinstance(decorator.args[0], ast.Constant) else ""
                                symbols["routes"].append({
                                    "name": node.name,
                                    "method": decorator.func.attr.upper(),
                                    "path": route_path,
                                    "line": node.lineno,
                                    "file": file_path
                                })
                    if not is_route:
                        symbols["functions"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "file": file_path,
                            "args": [arg.arg for arg in node.args.args]
                        })
                elif isinstance(node, ast.ClassDef):
                    is_model = any(
                        isinstance(base, ast.Name) and base.id in ["BaseModel", "Model", "Base"]
                        for base in node.bases
                    )
                    if is_model:
                        symbols["models"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "file": file_path
                        })
                    else:
                        symbols["classes"].append({
                            "name": node.name,
                            "line": node.lineno,
                            "file": file_path
                        })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        symbols["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    symbols["imports"].append(f"{node.module}.{node.names[0].name}" if node.module else node.names[0].name)
        except Exception:
            # Fallback regex parsing if AST fails
            funcs = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
            symbols["functions"] = [{"name": f, "file": file_path, "line": 1} for f in funcs]
            symbols["classes"] = [{"name": c, "file": file_path, "line": 1} for c in classes]

        return symbols

    @staticmethod
    def parse_typescript(code: str, file_path: str) -> Dict[str, Any]:
        symbols = {
            "functions": [],
            "classes": [],
            "imports": [],
            "exports": [],
            "components": [],
            "routes": []
        }

        # Imports
        import_matches = re.findall(r'import\s+.*?from\s+[\'"](.*?)[\'"]', code)
        symbols["imports"] = list(set(import_matches))

        # Exports
        export_matches = re.findall(r'export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        symbols["exports"] = list(set(export_matches))

        # React Components (JSX/TSX returning functions)
        component_matches = re.findall(r'(?:export\s+default\s+|export\s+)?function\s+([A-Z][a-zA-Z0-9_]*)\s*\(', code)
        symbols["components"] = list(set(component_matches))

        # Regular Functions
        func_matches = re.findall(r'(?:async\s+)?function\s+([a-z_][a-zA-Z0-9_]*)\s*\(', code)
        const_funcs = re.findall(r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?\(', code)
        symbols["functions"] = [{"name": f, "file": file_path} for f in set(func_matches + const_funcs)]

        # Classes & Interfaces
        class_matches = re.findall(r'(?:class|interface|type)\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        symbols["classes"] = [{"name": c, "file": file_path} for c in set(class_matches)]

        # App Router Pages/Routes
        if "page.tsx" in file_path or "page.jsx" in file_path or "route.ts" in file_path:
            route_name = file_path.replace("\\", "/").split("src/app/")[-1] if "src/app/" in file_path else file_path
            symbols["routes"].append({
                "path": f"/{route_name.replace('/page.tsx', '').replace('/page.jsx', '')}",
                "file": file_path
            })

        return symbols

    @classmethod
    def parse_file(cls, file_path: str, content: str) -> Dict[str, Any]:
        if file_path.endswith(".py"):
            return cls.parse_python(content, file_path)
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return cls.parse_typescript(content, file_path)
        return {"functions": [], "classes": [], "imports": [], "exports": [], "components": [], "routes": [], "models": []}
