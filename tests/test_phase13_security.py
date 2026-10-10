import os
import shutil
import tempfile
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.main import app, search_memory, get_memory_context
from memory.manager import ProjectMemoryManager
from memory.models import (
    ArchitectureRecord, DecisionRecord, TaskHistoryRecord,
    DeveloperPreferenceRecord, DecisionStatus, TaskStatus, PreferenceCategory
)

client = TestClient(app)


def test_memory_endpoints_reject_invalid_directory():
    endpoints = [
        "/api/memory/overview?directory_path=/invalid/non_existent_dir_123",
        "/api/memory/architecture?directory_path=/invalid/non_existent_dir_123",
        "/api/memory/decisions?directory_path=/invalid/non_existent_dir_123",
        "/api/memory/tasks?directory_path=/invalid/non_existent_dir_123",
        "/api/memory/preferences?directory_path=/invalid/non_existent_dir_123",
        "/api/memory/search?query=test&directory_path=/invalid/non_existent_dir_123",
        "/api/memory/context?task_description=test&directory_path=/invalid/non_existent_dir_123"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 400
        assert "does not exist" in res.json()["detail"]


def test_memory_architecture_endpoint_validates_payload():
    # Empty ID
    res = client.post("/api/memory/architecture", json={
        "id": "",
        "component_name": "API",
        "description": "Test"
    })
    assert res.status_code == 400
    assert "ID cannot be empty" in res.json()["detail"]

    # Null byte in component name
    res = client.post("/api/memory/architecture", json={
        "id": "arch-1",
        "component_name": "API\0Injection",
        "description": "Test"
    })
    assert res.status_code == 400
    assert "Null bytes are prohibited" in res.json()["detail"]

    # Oversized description
    res = client.post("/api/memory/architecture", json={
        "id": "arch-1",
        "component_name": "API",
        "description": "a" * 2001
    })
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]


def test_memory_decision_endpoint_validates_payload():
    # Empty title
    res = client.post("/api/memory/decisions", json={
        "id": "adr-1",
        "title": "  ",
        "context": "Context",
        "decision": "Decision"
    })
    assert res.status_code == 400
    assert "Title cannot be empty" in res.json()["detail"]

    # Null byte in decision
    res = client.post("/api/memory/decisions", json={
        "id": "adr-1",
        "title": "Valid ADR",
        "context": "Context",
        "decision": "Decision\0Exploit"
    })
    assert res.status_code == 400
    assert "Null bytes are prohibited" in res.json()["detail"]

    # Oversized context
    res = client.post("/api/memory/decisions", json={
        "id": "adr-1",
        "title": "Valid ADR",
        "context": "x" * 2001,
        "decision": "Decision"
    })
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]


def test_memory_tasks_endpoint_validates_bounds_and_payload():
    # Invalid limit < 1
    res = client.get("/api/memory/tasks?limit=0")
    assert res.status_code == 400
    assert "Limit must be between 1 and 1000" in res.json()["detail"]

    # Invalid limit > 1000
    res = client.get("/api/memory/tasks?limit=1001")
    assert res.status_code == 400
    assert "Limit must be between 1 and 1000" in res.json()["detail"]

    # Empty task title
    res = client.post("/api/memory/tasks", json={
        "id": "task-1",
        "task_title": "",
        "task_request": "Fix things",
        "agent_name": "Coder"
    })
    assert res.status_code == 400
    assert "Task title cannot be empty" in res.json()["detail"]

    # Null byte in task request
    res = client.post("/api/memory/tasks", json={
        "id": "task-1",
        "task_title": "Task Title",
        "task_request": "Execute\0Payload",
        "agent_name": "Coder"
    })
    assert res.status_code == 400
    assert "Null bytes are prohibited" in res.json()["detail"]


def test_memory_preferences_endpoint_validates_payload():
    # Null byte in key
    res = client.post("/api/memory/preferences", json={
        "id": "pref-1",
        "category": "CODING_STYLE",
        "key": "Tab\0Width",
        "value": "4 spaces",
        "description": "Standard width"
    })
    assert res.status_code == 400
    assert "Null bytes are prohibited" in res.json()["detail"]

    # Empty value
    res = client.post("/api/memory/preferences", json={
        "id": "pref-1",
        "category": "CODING_STYLE",
        "key": "Tab Width",
        "value": "   ",
        "description": "Standard width"
    })
    assert res.status_code == 400
    assert "Value cannot be empty" in res.json()["detail"]


def test_memory_search_and_context_validate_bounds():
    import asyncio
    # Null byte in search query
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(search_memory(query="test\0evil"))
    assert exc_info.value.status_code == 400
    assert "Null bytes are prohibited" in exc_info.value.detail

    # Oversized search query
    res = client.get(f"/api/memory/search?query={'a' * 501}")
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]

    # Null byte in task description
    with pytest.raises(HTTPException) as exc_info2:
        asyncio.run(get_memory_context(task_description="build\0test"))
    assert exc_info2.value.status_code == 400
    assert "Null bytes are prohibited" in exc_info2.value.detail


def test_memory_search_matches_expanded_fields():
    temp_dir = tempfile.mkdtemp()
    try:
        mgr = ProjectMemoryManager(root_dir=temp_dir)
        mgr.tasks.record_task(TaskHistoryRecord(
            id="task-expanded-99",
            task_title="Add telemetry agent",
            task_request="Integrate monitoring",
            agent_name="ObservabilityAgentSpecialist",
            status=TaskStatus.COMPLETED,
            files_changed=["telemetry.py"],
            fix_summary="Done"
        ))
        # Search by agent_name
        results = mgr.tasks.search_tasks("ObservabilityAgentSpecialist")
        assert len(results) == 1
        assert results[0].id == "task-expanded-99"

        # Search preferences by category
        pref_results = mgr.preferences.search_preferences("coding_style")
        assert len(pref_results) >= 1
    finally:
        shutil.rmtree(temp_dir)
