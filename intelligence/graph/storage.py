import json
from collections import deque, defaultdict
from typing import Dict, List, Set, Optional, Tuple
from intelligence.graph.models import (
    GraphNode, GraphEdge, KnowledgeGraphData, BlastRadiusResult, NodeType
)

class KnowledgeGraphStore:
    """
    High-performance in-memory graph engine with adjacency indices,
    blast-radius impact analysis, and GraphRAG neighborhood queries.
    """

    def __init__(self, data: Optional[KnowledgeGraphData] = None):
        self.nodes: Dict[str, GraphNode] = {}
        self.adj: Dict[str, List[GraphEdge]] = defaultdict(list)          # source -> outgoing edges
        self.rev_adj: Dict[str, List[GraphEdge]] = defaultdict(list)      # target -> incoming edges
        
        if data:
            self.load_data(data)

    def load_data(self, data: KnowledgeGraphData):
        self.nodes = {node.id: node for node in data.nodes}
        self.adj.clear()
        self.rev_adj.clear()
        
        for edge in data.edges:
            self.adj[edge.source].append(edge)
            self.rev_adj[edge.target].append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self.nodes.get(node_id)

    def find_node_by_symbol(self, symbol_name: str) -> Optional[GraphNode]:
        if not symbol_name or not isinstance(symbol_name, str):
            return None
        # 1. Exact node name match
        for node in self.nodes.values():
            if node.name == symbol_name:
                return node
        # 2. Node ID match
        if symbol_name in self.nodes:
            return self.nodes[symbol_name]
        # 3. Method qualified match (e.g. Class.method matching method)
        for node in self.nodes.values():
            if node.name.endswith(f".{symbol_name}"):
                return node
        # 4. Case-insensitive match
        symbol_lower = symbol_name.lower()
        for node in self.nodes.values():
            if node.name.lower() == symbol_lower:
                return node
        return None

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[GraphNode]:
        """Get connected neighbor nodes (outgoing, incoming, or both)."""
        neighbor_ids = set()
        
        if direction in ("out", "both"):
            for edge in self.adj.get(node_id, []):
                neighbor_ids.add(edge.target)
                
        if direction in ("in", "both"):
            for edge in self.rev_adj.get(node_id, []):
                neighbor_ids.add(edge.source)

        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def find_shortest_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Find the shortest directional dependency path between two symbols using BFS."""
        s_node = self.nodes.get(start_id) or self.find_node_by_symbol(start_id)
        e_node = self.nodes.get(end_id) or self.find_node_by_symbol(end_id)
        if not s_node or not e_node:
            return None
        s_id = s_node.id
        e_id = e_node.id
            
        queue = deque([[s_id]])
        visited = {s_id}

        while queue:
            path = queue.popleft()
            curr = path[-1]

            if curr == e_id:
                return path

            for edge in self.adj.get(curr, []):
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append(path + [edge.target])

        return None

    def calculate_blast_radius(self, target_symbol_or_id: str) -> BlastRadiusResult:
        """
        Calculates the blast radius (impact analysis) if a given symbol or file is changed.
        Traverses incoming dependency edges to identify all upstream callers & dependents.
        """
        if not target_symbol_or_id or not isinstance(target_symbol_or_id, str):
            return BlastRadiusResult(
                target_symbol=str(target_symbol_or_id or "unknown"),
                target_file="unknown",
                impact_score=0.0,
                risk_level="UNKNOWN"
            )
        target_node = self.find_node_by_symbol(target_symbol_or_id) or self.get_node(target_symbol_or_id)
        
        if not target_node:
            return BlastRadiusResult(
                target_symbol=target_symbol_or_id,
                target_file="unknown",
                impact_score=0.0,
                risk_level="UNKNOWN"
            )

        direct_dependents: Set[str] = set()
        transitive_dependents: Set[str] = set()
        affected_files: Set[str] = {target_node.file_path}

        # Find direct dependents (nodes that point to target_node)
        for edge in self.rev_adj.get(target_node.id, []):
            direct_dependents.add(edge.source)
            if edge.source in self.nodes:
                affected_files.add(self.nodes[edge.source].file_path)

        # BFS for all transitive dependents
        queue = deque(list(direct_dependents))
        visited = set(direct_dependents)

        while queue:
            curr = queue.popleft()
            transitive_dependents.add(curr)
            if curr in self.nodes:
                affected_files.add(self.nodes[curr].file_path)

            for edge in self.rev_adj.get(curr, []):
                if edge.source not in visited and edge.source != target_node.id:
                    visited.add(edge.source)
                    queue.append(edge.source)

        total_affected = len(transitive_dependents) + 1
        total_nodes = len(self.nodes) if self.nodes else 1
        impact_score = min(100.0, round((total_affected / total_nodes) * 100 * (1 + target_node.complexity * 0.1), 2))

        if impact_score > 60.0 or len(affected_files) > 5:
            risk_level = "CRITICAL"
        elif impact_score > 30.0 or len(affected_files) > 2:
            risk_level = "HIGH"
        elif impact_score > 10.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return BlastRadiusResult(
            target_symbol=target_node.name,
            target_file=target_node.file_path,
            direct_dependents=list(direct_dependents),
            transitive_dependents=list(transitive_dependents),
            impact_score=impact_score,
            affected_files=list(affected_files),
            risk_level=risk_level
        )

    def to_dict(self) -> Dict:
        return {
            "nodes": [n.dict() for n in self.nodes.values()],
            "edges": [
                e.dict() for edges in self.adj.values() for e in edges
            ]
        }
