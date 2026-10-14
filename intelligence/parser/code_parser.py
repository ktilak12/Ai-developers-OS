import re
import ast
from typing import Dict, List, Any

class CodeParser:
    """
    Parses Python, TypeScript/JavaScript, Go, Rust, Java, and C/C++ files to extract symbols:
    Functions, Classes, Imports, Exports, Routes, Components, and Models.
    Includes security protections: file size guards, extracted symbol caps,
    identifier length bounds, and resilience against malformed ASTs / ReDoS.
    """

    MAX_CODE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB cap
    MAX_SYMBOLS_PER_FILE = 500  # Cap extracted symbols to prevent memory DoS

    # ---------------------------------------------------------------------------
    # Dispatch
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_file(cls, file_path: str, content: str) -> Dict[str, Any]:
        if not file_path or not content:
            return cls._empty()
        if file_path.endswith(".py"):
            return cls.parse_python(content, file_path)
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return cls.parse_typescript(content, file_path)
        elif file_path.endswith(".go"):
            return cls.parse_go(content, file_path)
        elif file_path.endswith(".rs"):
            return cls.parse_rust(content, file_path)
        elif file_path.endswith(".java"):
            return cls.parse_java(content, file_path)
        elif file_path.endswith((".c", ".cpp", ".cc", ".cxx", ".h", ".hpp")):
            return cls.parse_cpp(content, file_path)
        return cls._empty()

    @classmethod
    def _empty(cls) -> Dict[str, Any]:
        return {
            "functions": [], "classes": [], "imports": [],
            "exports": [], "components": [], "routes": [], "models": []
        }

    @classmethod
    def _guard(cls, code: str) -> bool:
        """Returns True if code passes size guard."""
        return bool(code and isinstance(code, str) and
                    len(code.encode("utf-8", errors="ignore")) <= cls.MAX_CODE_SIZE_BYTES)

    @classmethod
    def _cap(cls, lst: list) -> list:
        return lst[:cls.MAX_SYMBOLS_PER_FILE]

    # ---------------------------------------------------------------------------
    # Python
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_python(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols: Dict[str, List[Any]] = {
            "functions": [], "classes": [], "imports": [], "routes": [], "models": []
        }

        if not cls._guard(code):
            return symbols

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                total_symbols = (
                    len(symbols["functions"]) + len(symbols["classes"]) +
                    len(symbols["routes"]) + len(symbols["models"])
                )
                if total_symbols >= cls.MAX_SYMBOLS_PER_FILE:
                    break

                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_route = False
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                                is_route = True
                                route_path = (
                                    decorator.args[0].value
                                    if decorator.args and isinstance(decorator.args[0], ast.Constant)
                                    else ""
                                )
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
            funcs = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*\(', code)[:cls.MAX_SYMBOLS_PER_FILE]
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*[\(:]', code)[:cls.MAX_SYMBOLS_PER_FILE]
            symbols["functions"] = [{"name": f, "file": file_path, "line": 1} for f in funcs]
            symbols["classes"] = [{"name": c, "file": file_path, "line": 1} for c in classes]

        return symbols

    # ---------------------------------------------------------------------------
    # TypeScript / JavaScript
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_typescript(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols: Dict[str, List[Any]] = {
            "functions": [], "classes": [], "imports": [],
            "exports": [], "components": [], "routes": []
        }

        if not cls._guard(code):
            return symbols

        try:
            import_matches = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]{1,300})[\'"]', code)
            symbols["imports"] = cls._cap(list(set(import_matches)))

            export_matches = re.findall(
                r'export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})',
                code
            )
            symbols["exports"] = cls._cap(list(set(export_matches)))

            component_matches = re.findall(
                r'(?:export\s+default\s+|export\s+)?function\s+([A-Z][a-zA-Z0-9_]{0,199})\s*\(', code
            )
            symbols["components"] = cls._cap(list(set(component_matches)))

            func_matches = re.findall(r'(?:async\s+)?function\s+([a-z_][a-zA-Z0-9_]{0,199})\s*\(', code)
            const_funcs = re.findall(r'const\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*=\s*(?:async\s+)?\(', code)
            symbols["functions"] = cls._cap([
                {"name": f, "file": file_path}
                for f in list(set(func_matches + const_funcs))
            ])

            class_matches = re.findall(r'(?:class|interface|type)\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})', code)
            symbols["classes"] = cls._cap([{"name": c, "file": file_path} for c in list(set(class_matches))])

            if "page.tsx" in file_path or "page.jsx" in file_path or "route.ts" in file_path:
                route_name = file_path.replace("\\", "/").split("src/app/")[-1] if "src/app/" in file_path else file_path
                clean_path = f"/{route_name.replace('/page.tsx', '').replace('/page.jsx', '')}"
                symbols["routes"].append({"path": clean_path[:200], "file": file_path})

        except Exception:
            pass

        return symbols

    # ---------------------------------------------------------------------------
    # Go
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_go(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols = cls._empty()
        if not cls._guard(code):
            return symbols

        try:
            pkg_imports = []
            # Package declaration
            pkg_match = re.search(r'^package\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})', code, re.MULTILINE)
            if pkg_match:
                pkg_imports.append(f"package:{pkg_match.group(1)}")

            # Imports (single and grouped)
            single_imports = re.findall(r'import\s+"([^"]{1,300})"', code)
            grouped_imports = re.findall(r'"([^"]{1,300})"', code)
            all_imports = pkg_imports + list(set(single_imports + grouped_imports))[:cls.MAX_SYMBOLS_PER_FILE]
            symbols["imports"] = cls._cap(all_imports)

            # Functions: func FuncName(
            func_matches = re.findall(
                r'^func\s+(?:\([^)]+\)\s+)?([A-Za-z_][A-Za-z0-9_]{0,199})\s*\(', code, re.MULTILINE
            )
            symbols["functions"] = cls._cap([
                {"name": f, "file": file_path, "language": "go"} for f in list(set(func_matches))
            ])

            # Structs (treated as classes)
            struct_matches = re.findall(
                r'^type\s+([A-Za-z_][A-Za-z0-9_]{0,199})\s+struct\b', code, re.MULTILINE
            )
            symbols["classes"] = cls._cap([
                {"name": s, "file": file_path, "kind": "struct", "language": "go"}
                for s in list(set(struct_matches))
            ])

            # Interfaces
            iface_matches = re.findall(
                r'^type\s+([A-Za-z_][A-Za-z0-9_]{0,199})\s+interface\b', code, re.MULTILINE
            )
            for iface in iface_matches[:cls.MAX_SYMBOLS_PER_FILE]:
                symbols["classes"].append({"name": iface, "file": file_path, "kind": "interface", "language": "go"})

            # HTTP routes (gin/echo/net/http patterns)
            route_matches = re.findall(
                r'\.(GET|POST|PUT|DELETE|PATCH|Handle|HandleFunc)\s*\(\s*"([^"]{1,200})"', code
            )
            symbols["routes"] = cls._cap([
                {"method": m, "path": p, "file": file_path, "language": "go"}
                for m, p in route_matches
            ])

        except Exception:
            pass

        return symbols

    # ---------------------------------------------------------------------------
    # Rust
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_rust(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols = cls._empty()
        if not cls._guard(code):
            return symbols

        try:
            # Functions: fn function_name
            func_matches = re.findall(
                r'\bfn\s+([a-z_][a-z0-9_]{0,199})\s*[<(]', code
            )
            # Public functions
            pub_func_matches = re.findall(
                r'\bpub\s+(?:async\s+)?fn\s+([a-z_][a-z0-9_]{0,199})\s*[<(]', code
            )
            all_funcs = list(set(func_matches + pub_func_matches))
            symbols["functions"] = cls._cap([
                {"name": f, "file": file_path, "language": "rust"} for f in all_funcs
            ])

            # Structs
            struct_matches = re.findall(r'\bstruct\s+([A-Z][a-zA-Z0-9_]{0,199})\b', code)
            symbols["classes"] = cls._cap([
                {"name": s, "file": file_path, "kind": "struct", "language": "rust"}
                for s in list(set(struct_matches))
            ])

            # Enums
            enum_matches = re.findall(r'\benum\s+([A-Z][a-zA-Z0-9_]{0,199})\b', code)
            for e in enum_matches[:cls.MAX_SYMBOLS_PER_FILE]:
                symbols["classes"].append({"name": e, "file": file_path, "kind": "enum", "language": "rust"})

            # Traits (treated as interfaces)
            trait_matches = re.findall(r'\btrait\s+([A-Z][a-zA-Z0-9_]{0,199})\b', code)
            for t in trait_matches[:cls.MAX_SYMBOLS_PER_FILE]:
                symbols["classes"].append({"name": t, "file": file_path, "kind": "trait", "language": "rust"})

            # Modules: mod module_name
            mod_matches = re.findall(r'\bmod\s+([a-z_][a-z0-9_]{0,199})\s*[;{]', code)
            symbols["imports"] = cls._cap([f"mod:{m}" for m in list(set(mod_matches))])

            # extern crate / use declarations
            use_matches = re.findall(r'\buse\s+([\w:]{1,200})', code)
            symbols["imports"] += cls._cap(use_matches)

        except Exception:
            pass

        return symbols

    # ---------------------------------------------------------------------------
    # Java
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_java(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols = cls._empty()
        if not cls._guard(code):
            return symbols

        try:
            # Imports
            import_matches = re.findall(r'^import\s+([\w.]{1,300});', code, re.MULTILINE)
            symbols["imports"] = cls._cap(import_matches)

            # Classes, interfaces, enums, records
            class_matches = re.findall(
                r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?'
                r'(?:class|interface|enum|record)\s+([A-Z][a-zA-Z0-9_]{0,199})',
                code
            )
            symbols["classes"] = cls._cap([
                {"name": c, "file": file_path, "language": "java"} for c in list(set(class_matches))
            ])

            # Methods (public/private/protected + return type + name)
            method_matches = re.findall(
                r'(?:public|private|protected|static|final|synchronized|\s)+\s+'
                r'(?:void|[\w<>\[\]]+)\s+([a-z_][a-zA-Z0-9_]{0,199})\s*\(',
                code
            )
            symbols["functions"] = cls._cap([
                {"name": m, "file": file_path, "language": "java"} for m in list(set(method_matches))
            ])

            # Spring MVC routes
            route_patterns = [
                r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)'
                r'\s*\(\s*(?:value\s*=\s*)?["\']([^"\']{1,200})["\']'
            ]
            for pattern in route_patterns:
                for method, path in re.findall(pattern, code):
                    symbols["routes"].append({"method": method.upper(), "path": path, "file": file_path, "language": "java"})
            symbols["routes"] = cls._cap(symbols["routes"])

            # Models: classes annotated with @Entity, @Table, @Document
            model_annotations = re.findall(
                r'@(?:Entity|Table|Document|Model)\s+(?:public\s+)?class\s+([A-Z][a-zA-Z0-9_]{0,199})',
                code
            )
            symbols["models"] = cls._cap([
                {"name": m, "file": file_path, "language": "java"} for m in model_annotations
            ])

        except Exception:
            pass

        return symbols

    # ---------------------------------------------------------------------------
    # C / C++
    # ---------------------------------------------------------------------------
    @classmethod
    def parse_cpp(cls, code: str, file_path: str) -> Dict[str, Any]:
        symbols = cls._empty()
        if not cls._guard(code):
            return symbols

        try:
            # #include directives
            include_matches = re.findall(r'#\s*include\s+[<"]([^>"]{1,200})[>"]', code)
            symbols["imports"] = cls._cap(include_matches)

            # Classes and structs
            class_matches = re.findall(
                r'\b(?:class|struct)\s+([A-Za-z_][A-Za-z0-9_]{0,199})\s*(?::\s*[^{]+)?\s*\{',
                code
            )
            symbols["classes"] = cls._cap([
                {"name": c, "file": file_path, "language": "cpp"} for c in list(set(class_matches))
            ])

            # Namespaces (treated as modules)
            ns_matches = re.findall(r'\bnamespace\s+([A-Za-z_][A-Za-z0-9_]{0,199})\s*\{', code)
            for ns in ns_matches[:cls.MAX_SYMBOLS_PER_FILE]:
                symbols["classes"].append({"name": ns, "file": file_path, "kind": "namespace", "language": "cpp"})

            # Function definitions (return_type function_name(
            # Simplified pattern — avoids parsing full C++ grammar
            func_matches = re.findall(
                r'\b([a-zA-Z_][a-zA-Z0-9_:]{0,199})\s+([a-zA-Z_][a-zA-Z0-9_]{0,199})\s*\([^;{]*\)\s*(?:const\s*)?\{',
                code
            )
            seen_funcs = set()
            for _ret_type, func_name in func_matches:
                if func_name not in seen_funcs and func_name not in {"if", "while", "for", "switch"}:
                    seen_funcs.add(func_name)
                    symbols["functions"].append({"name": func_name, "file": file_path, "language": "cpp"})
            symbols["functions"] = cls._cap(symbols["functions"])

            # Enums
            enum_matches = re.findall(r'\benum\s+(?:class\s+)?([A-Za-z_][A-Za-z0-9_]{0,199})', code)
            for e in enum_matches[:cls.MAX_SYMBOLS_PER_FILE]:
                symbols["classes"].append({"name": e, "file": file_path, "kind": "enum", "language": "cpp"})

        except Exception:
            pass

        return symbols
