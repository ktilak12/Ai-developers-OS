from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    FILE = "FILE"
    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    VARIABLE = "VARIABLE"
    ROUTE = "ROUTE"
    MODEL = "MODEL"
    INTERFACE = "INTERFACE"

class EdgeType(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    DEFINES = "DEFINES"
    INHERITS = "INHERITS"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    EXPOSES = "EXPOSES"

class GraphNode(BaseModel):
    id: str
    name: str
    node_type: NodeType
    file_path: str
    line: Optional[int] = None
    complexity: int = 1
    incoming_degree: int = 0
    outgoing_degree: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeGraphData(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0

class BlastRadiusResult(BaseModel):
    target_symbol: str
    target_file: str
    direct_dependents: List[str] = Field(default_factory=list)
    transitive_dependents: List[str] = Field(default_factory=list)
    impact_score: float = 0.0
    affected_files: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
