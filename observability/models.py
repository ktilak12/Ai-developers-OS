from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class SpanStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class ToolCallTrace(BaseModel):
    call_id: str = Field(default_factory=lambda: f"call-{uuid.uuid4().hex[:6]}")
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"span-{uuid.uuid4().hex[:8]}")
    parent_span_id: Optional[str] = None
    agent_name: str
    status: SpanStatus = SpanStatus.COMPLETED
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    duration_sec: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    tool_calls: List[ToolCallTrace] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid.uuid4().hex[:8]}")
    workflow_id: str
    task_id: str
    task_title: str
    status: str = "COMPLETED"
    total_duration_sec: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    retry_count: int = 0
    spans: List[AgentSpan] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ObservabilityMetrics(BaseModel):
    task_success_rate: float = 100.0
    total_tasks_executed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_execution_time_sec: float = 0.0
    total_tokens_consumed: int = 0
    total_cost_usd: float = 0.0
    agent_failure_count: int = 0
    tool_failure_count: int = 0
    test_pass_rate: float = 100.0
    agent_latency_breakdown: Dict[str, float] = Field(default_factory=dict)
    tool_usage_counts: Dict[str, int] = Field(default_factory=dict)
