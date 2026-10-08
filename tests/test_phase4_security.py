import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from intelligence.retrieval.text_chunker import TextChunker
from intelligence.embeddings.embeddings import EmbeddingEngine
from intelligence.retrieval.vector_store import VectorStore
from intelligence.reranking.reranker import Reranker
from intelligence.retrieval.retriever import ProjectRAGPipeline

client = TestClient(app)


def test_text_chunker_infinite_loop_and_bounds_protection():
    # 1. Overlap >= chunk_size should be clamped to chunk_size - 1 (prevent zero-stride infinite loop)
    chunker_bad = TextChunker(chunk_size=20, overlap=30)
    assert chunker_bad.chunk_size == 20
    assert chunker_bad.overlap == 19  # clamped

    # 2. Chunking file should never loop infinitely
    content = "\n".join([f"line_{i} = {i}" for i in range(100)])
    chunks = chunker_bad.chunk_file("test.py", content)
    assert len(chunks) > 0
    assert len(chunks) <= TextChunker.MAX_CHUNKS_PER_FILE

    # 3. None/empty input handling
    assert chunker_bad.chunk_file("test.py", "") == []
    assert chunker_bad.chunk_file("test.py", None) == []


def test_embedding_engine_sanitization_and_dimension_bounds():
    # 1. Vector dimension bounds
    engine_small = EmbeddingEngine(vector_dim=5)
    assert engine_small.vector_dim == 16  # minimum clamped

    engine_large = EmbeddingEngine(vector_dim=5000)
    assert engine_large.vector_dim == 1024  # maximum clamped

    engine = EmbeddingEngine(vector_dim=64)

    # 2. Empty / invalid text generates zero vector
    vec_empty = engine.generate_embedding("")
    assert len(vec_empty) == 64
    assert all(v == 0.0 for v in vec_empty)

    # 3. Massive string input is bounded safely without memory exhaustion
    huge_text = "token " * 100000
    vec_huge = engine.generate_embedding(huge_text)
    assert len(vec_huge) == 64
    assert sum(v * v for v in vec_huge) > 0.0


def test_vector_store_capacity_limits_and_query_sanitization():
    store = VectorStore()

    # 1. Capacity limit enforcement
    huge_chunk_list = [{"text": f"function test_{i}() {{}}", "file_path": f"f_{i}.py"} for i in range(12000)]
    store.add_chunks(huge_chunk_list)
    assert len(store.store) <= VectorStore.MAX_STORE_CAPACITY

    # 2. Query sanitization and top_k bounding
    results = store.search("   \x00\x1btest_1   ", top_k=5)
    assert len(results) > 0
    assert len(results) <= 5

    # 3. Search with empty string returns empty
    assert store.search("") == []


def test_reranker_resilience_and_term_capping():
    reranker = Reranker()

    # 1. Malformed candidates handling
    malformed_candidates = [
        None,
        {},
        {"score": "invalid", "chunk": None},
        {"score": 0.8, "chunk": {"file_path": "auth.py", "text": "def authenticate(): pass"}}
    ]
    results = reranker.rerank("authenticate", malformed_candidates)
    assert len(results) == 1
    assert results[0]["chunk"]["file_path"] == "auth.py"

    # 2. Query term capping
    long_query = " ".join([f"term_{i}" for i in range(50)])
    results_long = reranker.rerank(long_query, malformed_candidates)
    assert len(results_long) == 1


def test_project_rag_pipeline_secret_shielding_and_directory_jailing():
    temp_dir = tempfile.mkdtemp()
    try:
        # Create normal code file
        code_file = os.path.join(temp_dir, "service.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("def login_user(username, password):\n    return True\n" * 5)

        # Create sensitive secrets file
        env_file = os.path.join(temp_dir, ".env")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("API_SECRET_KEY=super_sensitive_api_token_12345\n")

        # Create oversized file (3MB)
        large_file = os.path.join(temp_dir, "huge_data.json")
        with open(large_file, "w", encoding="utf-8") as f:
            f.write("{\"key\": \"val\"}\n" * 200000)

        rag = ProjectRAGPipeline(temp_dir)
        total_chunks = rag.build_index()

        assert total_chunks > 0

        # Query vector index
        query_res = rag.query("login user", top_k=4)
        retrieved_files = query_res["retrieved_files"]

        # service.py should be indexed
        assert any("service.py" in f for f in retrieved_files)

        # .env and huge_data.json must NOT be indexed
        assert not any(".env" in f for f in retrieved_files)
        assert not any("huge_data.json" in f for f in retrieved_files)

    finally:
        shutil.rmtree(temp_dir)


def test_rag_api_endpoints_validation():
    # 1. Valid query
    res_query = client.get("/api/rag/query?question=test&top_k=2")
    assert res_query.status_code == 200

    # 2. Empty question should fail validation (min_length=1)
    res_empty_q = client.get("/api/rag/query?question=&top_k=2")
    assert res_empty_q.status_code == 422

    # 3. Invalid top_k (< 1) should fail validation
    res_bad_k = client.get("/api/rag/query?question=hello&top_k=0")
    assert res_bad_k.status_code == 422

    # 4. Index endpoint with non-existent directory should return 400
    res_index_bad = client.post("/api/rag/index", json={"directory_path": "/non/existent/rag/folder"})
    assert res_index_bad.status_code == 400
