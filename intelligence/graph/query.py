from typing import Dict, List, Any, Optional
from intelligence.graph.models import NodeType, EdgeType, GraphNode, KnowledgeGraphData
from intelligence.graph.storage import KnowledgeGraphStore

class GraphQueryEngine:
    """
    High-level Graph-RAG and structural query engine for AI coding agents
    and Developer Intelligence dashboards.
    """

    def __init__(self, store: KnowledgeGraphStore):
        self.store = store

    def get_symbol_context(self, symbol_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        Retrieves complete structural context of a symbol for GraphRAG prompting:
        definitions, upstream callers, downstream callees, and enclosing file.
        """
        target_node = self.store.find_node_by_symbol(symbol_name)
        if not target_node:
            return {"error": f"Symbol '{symbol_name}' not found in knowledge graph"}

        callers = []
        for edge in self.store.rev_adj.get(target_node.id, []):
            if edge.edge_type == EdgeType.CALLS and edge.source in self.store.nodes:
                caller = self.store.nodes[edge.source]
                callers.append({"name": caller.name, "file": caller.file_path, "line": caller.line})

        callees = []
        for edge in self.store.adj.get(target_node.id, []):
            if edge.edge_type == EdgeType.CALLS and edge.target in self.store.nodes:
                callee = self.store.nodes[edge.target]
                callees.append({"name": callee.name, "file": callee.file_path, "line": callee.line})

        neighbors = self.store.get_neighbors(target_node.id, direction="both")

        return {
            "symbol": target_node.name,
            "node_type": target_node.node_type.value,
            "file_path": target_node.file_path,
            "line": target_node.line,
            "complexity": target_node.complexity,
            "callers": callers,
            "callees": callees,
            "related_nodes": [{"id": n.id, "name": n.name, "type": n.node_type.value} for n in neighbors[:15]]
        }

    def get_architecture_clusters(self) -> Dict[str, List[Dict[str, Any]]]:
        """Groups symbols into logical architecture clusters by directory."""
        clusters: Dict[str, List[Dict[str, Any]]] = {}
        
        for node in self.store.nodes.values():
            dir_name = node.file_path.split("/")[0] if "/" in node.file_path else "root"
            if dir_name not in clusters:
                clusters[dir_name] = []
                
            clusters[dir_name].append({
                "id": node.id,
                "name": node.name,
                "type": node.node_type.value,
                "complexity": node.complexity,
                "file": node.file_path
            })
            
        return clusters

    def find_entrypoints(self) -> List[Dict[str, Any]]:
        """Identifies API routes and main entry points in the codebase."""
        entrypoints = []
        for node in self.store.nodes.values():
            if node.node_type in [NodeType.ROUTE] or node.name in ["main", "app", "handler"]:
                entrypoints.append({
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type.value,
                    "file": node.file_path,
                    "line": node.line
                })
        return entrypoints

    def find_dead_code_candidates(self) -> List[Dict[str, Any]]:
        """Finds non-entrypoint functions and methods with 0 callers."""
        dead_candidates = []
        for node in self.store.nodes.values():
            if node.node_type in [NodeType.FUNCTION, NodeType.METHOD]:
                if node.incoming_degree == 0 and not node.name.startswith("__") and node.name not in ["main", "test"]:
                    dead_candidates.append({
                        "id": node.id,
                        "name": node.name,
                        "type": node.node_type.value,
                        "file": node.file_path,
                        "line": node.line
                    })
        return dead_candidates
