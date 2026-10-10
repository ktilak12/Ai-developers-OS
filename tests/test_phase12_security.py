import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from intelligence.graph.builder import CodeGraphBuilder
from intelligence.graph.storage import KnowledgeGraphStore
from intelligence.graph.models import EdgeType

client = TestClient(app)


def test_graph_build_endpoint_rejects_invalid_directory():
    res = client.post("/api/intelligence/graph/build", json={
        "directory_path": "/invalid/non_existent_graph_dir_xyz"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_graph_overview_endpoint_rejects_invalid_directory():
    res = client.get("/api/intelligence/graph/overview?directory_path=/invalid/non_existent_graph_dir_xyz")
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_graph_blast_radius_endpoint_rejects_invalid_directory():
    res = client.post("/api/intelligence/graph/blast-radius", json={
        "target_symbol": "my_function",
        "directory_path": "/invalid/non_existent_graph_dir_xyz"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_graph_blast_radius_endpoint_rejects_empty_symbol():
    res = client.post("/api/intelligence/graph/blast-radius", json={
        "target_symbol": "   "
    })
    assert res.status_code == 400
    assert "Target symbol cannot be empty" in res.json()["detail"]


def test_graph_blast_radius_endpoint_rejects_oversized_symbol():
    res = client.post("/api/intelligence/graph/blast-radius", json={
        "target_symbol": "a" * 201
    })
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]


def test_graph_blast_radius_endpoint_rejects_null_bytes():
    res = client.post("/api/intelligence/graph/blast-radius", json={
        "target_symbol": "symbol\0evil"
    })
    assert res.status_code == 400
    assert "Null bytes are prohibited" in res.json()["detail"]


def test_graph_symbol_endpoint_rejects_invalid_directory():
    res = client.get("/api/intelligence/graph/symbol/my_func?directory_path=/invalid/non_existent_dir_xyz")
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_graph_symbol_endpoint_rejects_oversized_symbol():
    res = client.get(f"/api/intelligence/graph/symbol/{'x' * 201}")
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]


def test_graph_symbol_endpoint_returns_404_on_unknown_symbol():
    temp_dir = tempfile.mkdtemp()
    try:
        # Build empty graph
        client.post("/api/intelligence/graph/build", json={"directory_path": temp_dir})
        res = client.get(f"/api/intelligence/graph/symbol/completely_unknown_symbol_123?directory_path={temp_dir}")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]
    finally:
        shutil.rmtree(temp_dir)


def test_code_graph_builder_two_pass_forward_references():
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a Python file where alpha calls beta, but alpha is defined FIRST
        py_file = os.path.join(temp_dir, "forward_ref.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("def alpha():\n    beta()\n\ndef beta():\n    pass\n")

        builder = CodeGraphBuilder(root_dir=temp_dir)
        graph_data = builder.build_from_directory()

        # Check that alpha and beta are nodes
        node_names = {n.name for n in graph_data.nodes}
        assert "alpha" in node_names
        assert "beta" in node_names

        # Check that call edge alpha -> beta exists despite forward reference
        call_edges = [e for e in graph_data.edges if e.edge_type == EdgeType.CALLS]
        assert len(call_edges) >= 1
        source_node = next(n for n in graph_data.nodes if n.id == call_edges[0].source)
        target_node = next(n for n in graph_data.nodes if n.id == call_edges[0].target)
        assert source_node.name == "alpha"
        assert target_node.name == "beta"
    finally:
        shutil.rmtree(temp_dir)


def test_knowledge_graph_store_shortest_path_and_blast_radius():
    temp_dir = tempfile.mkdtemp()
    try:
        py_file = os.path.join(temp_dir, "chain.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(
                "def func_a():\n    func_b()\n\n"
                "def func_b():\n    func_c()\n\n"
                "def func_c():\n    pass\n"
            )

        builder = CodeGraphBuilder(root_dir=temp_dir)
        graph_data = builder.build_from_directory()
        store = KnowledgeGraphStore(graph_data)

        # Shortest path using symbol names
        path = store.find_shortest_path("func_a", "func_c")
        assert path is not None
        assert len(path) == 3

        # Blast radius of func_c should include upstream dependents func_b and func_a
        blast = store.calculate_blast_radius("func_c")
        assert blast.target_symbol == "func_c"
        assert "func::chain.py::func_b" in blast.direct_dependents or any("func_b" in d for d in blast.direct_dependents)
        assert len(blast.transitive_dependents) >= 2
        assert blast.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    finally:
        shutil.rmtree(temp_dir)
