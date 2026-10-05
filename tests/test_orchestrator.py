import pytest
import os
import shutil
import tempfile
from orchestrator import (
    MultiAgentOrchestrator, OrchestratorState, WorkflowStatus,
    ApprovalState, PermissionPolicy, ActionPermission, AgentRouter,
    EventBus, WorkflowEventType
)


@pytest.fixture
def temp_repo():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def test_permission_policy():
    assert PermissionPolicy.is_allowed_autonomously("create_branch") is True
    assert PermissionPolicy.is_allowed_autonomously("modify_source") is True
    assert PermissionPolicy.is_allowed_autonomously("run_tests") is True
    assert PermissionPolicy.requires_approval("create_pr") is True
    assert PermissionPolicy.requires_approval("deploy_production") is True
    assert PermissionPolicy.check_permission("delete_repository") == ActionPermission.FORBIDDEN


def test_router_transitions():
    state = OrchestratorState(task="Fix bug")
    assert state.status == WorkflowStatus.PENDING

    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.PLANNING

    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.RESEARCHING

    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.CODING

    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.TESTING

    # Test passes
    state.test_success = True
    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.SECURITY_SCAN

    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.REVIEWING

    state.status = AgentRouter.get_next_step(state)
    assert state.status == WorkflowStatus.WAITING_APPROVAL


def test_event_bus():
    bus = EventBus()
    received = []

    def on_event(evt):
        received.append(evt)

    bus.subscribe(WorkflowEventType.WORKFLOW_STARTED, on_event)
    bus.publish(WorkflowEventType.WORKFLOW_STARTED, {"workflow_id": "wf-123", "msg": "started"})

    assert len(received) == 1
    assert received[0]["type"] == WorkflowEventType.WORKFLOW_STARTED.value
    assert received[0]["payload"]["workflow_id"] == "wf-123"


def test_orchestrator_execution_and_approval(temp_repo):
    orch = MultiAgentOrchestrator(root_dir=temp_repo)
    task_desc = "Fix checkout failure when expired coupon is applied"
    
    # Run workflow requiring human approval
    state = orch.execute_workflow(task_desc, auto_approve=False)

    assert state.task == task_desc
    assert state.status == WorkflowStatus.WAITING_APPROVAL
    assert state.approval_status == ApprovalState.PENDING
    assert state.plan is not None
    assert state.research is not None
    assert len(state.files_changed) >= 1
    assert state.test_success is True
    assert state.review is not None
    assert len(state.agent_traces) >= 5

    # Human Approves
    approved_state = orch.handle_human_decision(state.workflow_id, approve=True, notes="Looks solid, approved.")
    assert approved_state.status == WorkflowStatus.COMPLETED
    assert approved_state.approval_status == ApprovalState.APPROVED
    assert approved_state.pr_url is not None
    assert "pull" in approved_state.pr_url


def test_orchestrator_human_rejection(temp_repo):
    orch = MultiAgentOrchestrator(root_dir=temp_repo)
    state = orch.execute_workflow("Refactor auth", auto_approve=False)
    assert state.status == WorkflowStatus.WAITING_APPROVAL

    rejected_state = orch.handle_human_decision(state.workflow_id, approve=False, notes="Needs more tests.")
    assert rejected_state.status == WorkflowStatus.FAILED
    assert rejected_state.approval_status == ApprovalState.REJECTED


def test_orchestrator_auto_approve(temp_repo):
    orch = MultiAgentOrchestrator(root_dir=temp_repo)
    state = orch.execute_workflow("Update README banner", auto_approve=True)
    assert state.status == WorkflowStatus.COMPLETED
    assert state.pr_url is not None
