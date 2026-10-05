import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_api_memory_overview():
    response = client.get("/api/memory/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_architecture_components" in data
    assert "total_decisions" in data
    assert "total_tasks_recorded" in data
    assert "total_preferences" in data

def test_api_memory_architecture():
    response = client.get("/api/memory/architecture")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "stack_summary" in data
    assert len(data["components"]) >= 1

def test_api_memory_add_decision_and_get():
    new_adr = {
        "id": "adr-api-test-01",
        "title": "API Test ADR: Modular Architecture",
        "status": "ACCEPTED",
        "author": "FastAPI Tester",
        "context": "Ensure memory endpoints function properly via HTTP.",
        "decision": "Use FastAPI router and JSON serialization for memory CRUD.",
        "consequences": ["Easy integration with web UI", "Strong typing"],
        "alternatives_considered": ["Raw sockets"]
    }
    post_res = client.post("/api/memory/decisions", json=new_adr)
    assert post_res.status_code == 200

    get_res = client.get("/api/memory/decisions")
    assert get_res.status_code == 200
    decisions = get_res.json()["decisions"]
    found = [d for d in decisions if d["id"] == "adr-api-test-01"]
    assert len(found) == 1
    assert found[0]["title"] == "API Test ADR: Modular Architecture"

def test_api_memory_search_and_context():
    search_res = client.get("/api/memory/search?query=FastAPI")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert "query" in search_data
    assert "architecture" in search_data

    context_res = client.get("/api/memory/context?task_description=Add+new+endpoint")
    assert context_res.status_code == 200
    ctx_data = context_res.json()
    assert ctx_data["status"] == "success"
    assert "Project Memory Context" in ctx_data["context"]
