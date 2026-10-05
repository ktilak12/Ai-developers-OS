from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    CODING = "CODING"
    TESTING = "TESTING"
    SECURITY_SCAN = "SECURITY_SCAN"
    REVIEWING = "REVIEWING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ApprovalState(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AgentStepTrace(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_name: str
    status: str
    duration_sec: float = 0.0
    tool_calls_count: int = 0
    summary: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrchestratorState(BaseModel):
    """
    Maintains the state machine of the AI Developer OS multi-agent system.
    """
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    task: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_agent: str = "orchestrator"
    iteration: int = 1
    max_iterations: int = 3
    
    # Artifacts & Agent Outputs
    plan: Optional[Dict[str, Any]] = None
    research: Optional[Dict[str, Any]] = None
    files_changed: List[str] = Field(default_factory=list)
    diff: str = ""
    tests_passed: int = 0
    tests_failed: int = 0
    test_logs: str = ""
    test_success: bool = False
    security_findings: List[Dict[str, Any]] = Field(default_factory=list)
    review: Optional[Dict[str, Any]] = None
    
    # Human Gate
    approval_status: ApprovalState = ApprovalState.NOT_REQUESTED
    approval_notes: Optional[str] = None
    pr_url: Optional[str] = None
    
    # Tracing & Telemetry
    agent_traces: List[AgentStepTrace] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
