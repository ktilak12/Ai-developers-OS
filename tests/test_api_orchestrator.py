import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_api_orchestrator_run_and_state():
    run_payload = {
        "task_request": "Fix expired coupon checkout bug",
        "auto_approve": False
    }
    res = client.post("/api/orchestrator/run", json=run_payload)
    assert res.status_code == 200
    data = res.json()
    assert "workflow_id" in data
    assert data["status"] == "WAITING_APPROVAL"
    assert data["approval_status"] == "PENDING"
    wf_id = data["workflow_id"]

    # Check state
    state_res = client.get(f"/api/orchestrator/state/{wf_id}")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["workflow_id"] == wf_id
    assert len(state_data["agent_traces"]) >= 5

    # Approve
    approve_payload = {
        "workflow_id": wf_id,
        "approve": True,
        "notes": "Verified diff and test suite."
    }
    appr_res = client.post("/api/orchestrator/approve", json=approve_payload)
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] == "COMPLETED"
    assert appr_data["approval_status"] == "APPROVED"
    assert "pull" in appr_data["pr_url"]

def test_api_orchestrator_history():
    res = client.get("/api/orchestrator/history")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "workflows" in data
    assert data["total"] >= 1
