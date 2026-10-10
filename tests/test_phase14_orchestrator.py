import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from orchestrator.workflow import MultiAgentOrchestrator
from orchestrator.state import WorkflowStatus, ApprovalState

client = TestClient(app)


def test_orchestrator_full_workflow_execution_with_human_gate():
    temp_dir = tempfile.mkdtemp()
    try:
        orch = MultiAgentOrchestrator(temp_dir)
        state = orch.execute_workflow(
            task_request="Add login rate limiting middleware",
            auto_approve=False
        )

        assert state.workflow_id.startswith("wf-")
        assert state.status == WorkflowStatus.WAITING_APPROVAL
        assert state.approval_status == ApprovalState.PENDING
        assert state.plan is not None
        assert state.research is not None
        assert len(state.files_changed) > 0
        assert state.test_success is True
        assert state.security_findings is not None
        assert state.review is not None
        assert len(state.agent_traces) >= 5

        # Approve workflow at Human Gate
        updated_state = orch.handle_human_decision(
            workflow_id=state.workflow_id,
            approve=True,
            notes="LGTM, security verified"
        )
        assert updated_state.status == WorkflowStatus.COMPLETED
        assert updated_state.approval_status == ApprovalState.APPROVED
        assert updated_state.pr_url is not None
        assert "github.com" in updated_state.pr_url
        assert updated_state.approval_notes == "LGTM, security verified"

    finally:
        shutil.rmtree(temp_dir)


def test_orchestrator_auto_approve_flow():
    temp_dir = tempfile.mkdtemp()
    try:
        orch = MultiAgentOrchestrator(temp_dir)
        state = orch.execute_workflow(
            task_request="Refactor database connection pool",
            auto_approve=True
        )

        assert state.status == WorkflowStatus.COMPLETED
        assert state.pr_url is not None
        assert state.current_agent == "completed"
    finally:
        shutil.rmtree(temp_dir)


def test_orchestrator_rejection_at_human_gate():
    temp_dir = tempfile.mkdtemp()
    try:
        orch = MultiAgentOrchestrator(temp_dir)
        state = orch.execute_workflow(
            task_request="Change primary key schema",
            auto_approve=False
        )

        assert state.status == WorkflowStatus.WAITING_APPROVAL

        rejected = orch.handle_human_decision(
            workflow_id=state.workflow_id,
            approve=False,
            notes="Requires architecture board approval first."
        )
        assert rejected.status == WorkflowStatus.FAILED
        assert rejected.approval_status == ApprovalState.REJECTED
        assert rejected.approval_notes == "Requires architecture board approval first."
    finally:
        shutil.rmtree(temp_dir)


def test_orchestrator_rejects_invalid_workflow_id():
    temp_dir = tempfile.mkdtemp()
    try:
        orch = MultiAgentOrchestrator(temp_dir)
        with pytest.raises(ValueError):
            orch.handle_human_decision("non_existent_wf_id", approve=True)
    finally:
        shutil.rmtree(temp_dir)


def test_orchestrator_api_run_validation():
    # 1. Empty task request must be rejected
    res_empty = client.post("/api/orchestrator/run", json={"task_request": "   "})
    assert res_empty.status_code == 400
    assert "cannot be empty" in res_empty.json()["detail"]

    # 2. Oversized task request must be rejected
    res_oversized = client.post("/api/orchestrator/run", json={"task_request": "x" * 2001})
    assert res_oversized.status_code == 400
    assert "exceeds maximum length" in res_oversized.json()["detail"]

    # 3. Null bytes must be rejected
    res_null = client.post("/api/orchestrator/run", json={"task_request": "Task\0Injection"})
    assert res_null.status_code == 400
    assert "Null bytes" in res_null.json()["detail"]

    # 4. Invalid directory must be rejected
    res_bad_dir = client.post("/api/orchestrator/run", json={
        "task_request": "Valid task",
        "directory_path": "/non/existent/path/xyz"
    })
    assert res_bad_dir.status_code == 400


def test_orchestrator_api_endpoints_end_to_end():
    # 1. Run workflow via API
    res_run = client.post("/api/orchestrator/run", json={
        "task_request": "Implement OAuth2 PKCE auth flow",
        "auto_approve": False
    })
    assert res_run.status_code == 200
    data = res_run.json()
    wf_id = data["workflow_id"]
    assert data["status"] == "WAITING_APPROVAL"

    # 2. Get state via API
    res_state = client.get(f"/api/orchestrator/state/{wf_id}")
    assert res_state.status_code == 200
    assert res_state.json()["workflow_id"] == wf_id

    # 3. Approve via API
    res_approve = client.post("/api/orchestrator/approve", json={
        "workflow_id": wf_id,
        "approve": True,
        "notes": "Reviewed and verified by test suite"
    })
    assert res_approve.status_code == 200
    approved_data = res_approve.json()
    assert approved_data["status"] == "COMPLETED"
    assert approved_data["approval_status"] == "APPROVED"
    assert "pr_url" in approved_data

    # 4. History API
    res_history = client.get("/api/orchestrator/history")
    assert res_history.status_code == 200
    history = res_history.json()
    assert history["status"] == "success"
    assert history["total"] >= 1


def test_orchestrator_api_approval_error_handling():
    # 1. Non-existent workflow ID returns 404
    res_404 = client.post("/api/orchestrator/approve", json={
        "workflow_id": "wf-invalid-unknown",
        "approve": True
    })
    assert res_404.status_code == 404

    # 2. Null byte in workflow ID returns 400
    res_null = client.post("/api/orchestrator/approve", json={
        "workflow_id": "wf-test\0evil",
        "approve": True
    })
    assert res_null.status_code == 400
