import os
import ast
import re
from typing import Dict, List, Set, Any, Tuple, Optional
from intelligence.graph.models import NodeType, EdgeType, GraphNode, GraphEdge, KnowledgeGraphData

class CodeGraphBuilder:
    """
    Parses repository source files (Python & TypeScript/JavaScript) to build
    a directed Knowledge Graph representing AST hierarchy, symbol definitions,
    inter-function calls, inheritance, and module import dependencies.
    """

    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._symbol_registry: Dict[str, str] = {} # Symbol Name -> Node ID
        self._deferred_calls: List[Tuple[ast.AST, str, str, Optional[str]]] = [] # (func_ast, caller_id, rel_path, class_name)
        self._deferred_bases: List[Tuple[str, List[ast.AST]]] = [] # (class_node_id, bases)

    def build_from_directory(self, target_dir: str = None) -> KnowledgeGraphData:
        """Traverse directory and build complete codebase knowledge graph."""
        scan_dir = os.path.abspath(target_dir or self.root_dir)
        self.nodes.clear()
        self.edges.clear()
        self._symbol_registry.clear()
        self._deferred_calls.clear()
        self._deferred_bases.clear()
        
        # Step 1: Scan and create file & symbol nodes across all files
        for root, _, files in os.walk(scan_dir):
            if any(ignored in root for ignored in [".git", "node_modules", ".next", "__pycache__", "venv", ".venv", "dist", ".pytest_cache"]):
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, scan_dir).replace("\\", "/")
                
                if file.endswith(".py"):
                    self._parse_python_file(file_path, rel_path)
                elif file.endswith((".ts", ".tsx", ".js", ".jsx")):
                    self._parse_ts_file(file_path, rel_path)

        # Step 2: Resolve deferred inheritance and function calls (handles forward refs & cross-file calls)
        for class_node_id, bases in self._deferred_bases:
            for base in bases:
                base_name = base.id if isinstance(base, ast.Name) else ""
                if base_name and base_name in self._symbol_registry:
                    self._add_edge(class_node_id, self._symbol_registry[base_name], EdgeType.INHERITS)

        for func_ast, caller_id, rel_path, class_name in self._deferred_calls:
            self._extract_function_calls(func_ast, caller_id, rel_path, class_name)

        # Step 3: Calculate in/out degree for all nodes
        for edge in self.edges:
            if edge.source in self.nodes:
                self.nodes[edge.source].outgoing_degree += 1
            if edge.target in self.nodes:
                self.nodes[edge.target].incoming_degree += 1

        total_nodes = len(self.nodes)
        total_edges = len(self.edges)
        possible_edges = total_nodes * (total_nodes - 1) if total_nodes > 1 else 1
        density = round(total_edges / possible_edges, 4) if possible_edges > 0 else 0.0

        return KnowledgeGraphData(
            nodes=list(self.nodes.values()),
            edges=self.edges,
            total_nodes=total_nodes,
            total_edges=total_edges,
            density=density
        )

    def _parse_python_file(self, full_path: str, rel_path: str):
        file_node_id = f"file::{rel_path}"
        self.nodes[file_node_id] = GraphNode(
            id=file_node_id,
            name=os.path.basename(rel_path),
            node_type=NodeType.FILE,
            file_path=rel_path,
            line=1,
            complexity=1,
            metadata={"language": "python"}
        )

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            tree = ast.parse(code)
        except Exception:
            return

        # Track file imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imp_id = f"module::{alias.name}"
                    if imp_id not in self.nodes:
                        self.nodes[imp_id] = GraphNode(
                            id=imp_id,
                            name=alias.name,
                            node_type=NodeType.MODULE,
                            file_path=rel_path,
                            line=node.lineno,
                            metadata={"external": True}
                        )
                    self._add_edge(file_node_id, imp_id, EdgeType.IMPORTS)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imp_id = f"module::{module}.{alias.name}" if module else f"module::{alias.name}"
                    if imp_id not in self.nodes:
                        self.nodes[imp_id] = GraphNode(
                            id=imp_id,
                            name=alias.name,
                            node_type=NodeType.MODULE,
                            file_path=rel_path,
                            line=node.lineno,
                            metadata={"module": module}
                        )
                    self._add_edge(file_node_id, imp_id, EdgeType.IMPORTS)

        # Track classes and methods
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_node_id = f"class::{rel_path}::{node.name}"
                complexity = len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))]) + 1
                
                self.nodes[class_node_id] = GraphNode(
                    id=class_node_id,
                    name=node.name,
                    node_type=NodeType.CLASS,
                    file_path=rel_path,
                    line=node.lineno,
                    complexity=complexity,
                    metadata={"bases": [ast.unparse(b) for b in node.bases] if hasattr(ast, "unparse") else []}
                )
                self._symbol_registry[node.name] = class_node_id
                self._add_edge(file_node_id, class_node_id, EdgeType.DEFINES)

                # Defer inheritance edges to Pass 2 after all classes are registered
                if node.bases:
                    self._deferred_bases.append((class_node_id, list(node.bases)))

                # Methods inside class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"method::{rel_path}::{node.name}.{item.name}"
                        m_complexity = len([n for n in ast.walk(item) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))]) + 1
                        self.nodes[method_id] = GraphNode(
                            id=method_id,
                            name=f"{node.name}.{item.name}",
                            node_type=NodeType.METHOD,
                            file_path=rel_path,
                            line=item.lineno,
                            complexity=m_complexity,
                            metadata={"args": [a.arg for a in item.args.args]}
                        )
                        self._symbol_registry[f"{node.name}.{item.name}"] = method_id
                        self._add_edge(class_node_id, method_id, EdgeType.DEFINES)
                        self._deferred_calls.append((item, method_id, rel_path, node.name))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = f"func::{rel_path}::{node.name}"
                complexity = len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))]) + 1
                
                # Check for FastAPI/Flask route decorators
                is_route = any(
                    isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ["get", "post", "put", "delete", "patch"]
                    for d in node.decorator_list
                )

                self.nodes[func_id] = GraphNode(
                    id=func_id,
                    name=node.name,
                    node_type=NodeType.ROUTE if is_route else NodeType.FUNCTION,
                    file_path=rel_path,
                    line=node.lineno,
                    complexity=complexity,
                    metadata={"is_async": isinstance(node, ast.AsyncFunctionDef)}
                )
                self._symbol_registry[node.name] = func_id
                self._add_edge(file_node_id, func_id, EdgeType.EXPOSES if is_route else EdgeType.DEFINES)
                self._deferred_calls.append((node, func_id, rel_path, None))

    def _extract_function_calls(self, func_node: ast.AST, caller_node_id: str, rel_path: str, class_name: Optional[str] = None):
        for sub in ast.walk(func_node):
            if isinstance(sub, ast.Call):
                target_name = ""
                if isinstance(sub.func, ast.Name):
                    target_name = sub.func.id
                elif isinstance(sub.func, ast.Attribute):
                    target_name = sub.func.attr
                
                target_id = None
                if target_name and target_name in self._symbol_registry:
                    target_id = self._symbol_registry[target_name]
                elif class_name and target_name and f"{class_name}.{target_name}" in self._symbol_registry:
                    target_id = self._symbol_registry[f"{class_name}.{target_name}"]

                if target_id:
                    self._add_edge(caller_node_id, target_id, EdgeType.CALLS)

    def _parse_ts_file(self, full_path: str, rel_path: str):
        file_node_id = f"file::{rel_path}"
        self.nodes[file_node_id] = GraphNode(
            id=file_node_id,
            name=os.path.basename(rel_path),
            node_type=NodeType.FILE,
            file_path=rel_path,
            line=1,
            complexity=1,
            metadata={"language": "typescript"}
        )

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return

        # Extract TS/JS functions
        func_matches = re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(", content)
        for m in func_matches:
            name = m.group(1)
            line = content[:m.start()].count("\n") + 1
            func_id = f"func::{rel_path}::{name}"
            self.nodes[func_id] = GraphNode(
                id=func_id,
                name=name,
                node_type=NodeType.FUNCTION,
                file_path=rel_path,
                line=line,
                complexity=2
            )
            self._symbol_registry[name] = func_id
            self._add_edge(file_node_id, func_id, EdgeType.DEFINES)

        # Extract TS Interfaces / Types
        type_matches = re.finditer(r"(?:export\s+)?(?:interface|type)\s+([a-zA-Z0-9_]+)", content)
        for m in type_matches:
            name = m.group(1)
            line = content[:m.start()].count("\n") + 1
            type_id = f"interface::{rel_path}::{name}"
            self.nodes[type_id] = GraphNode(
                id=type_id,
                name=name,
                node_type=NodeType.INTERFACE,
                file_path=rel_path,
                line=line,
                complexity=1
            )
            self._symbol_registry[name] = type_id
            self._add_edge(file_node_id, type_id, EdgeType.DEFINES)

    def _add_edge(self, source: str, target: str, edge_type: EdgeType):
        if source == target:
            return
        edge = GraphEdge(source=source, target=target, edge_type=edge_type)
        if not any(e.source == source and e.target == target and e.edge_type == edge_type for e in self.edges):
            self.edges.append(edge)
