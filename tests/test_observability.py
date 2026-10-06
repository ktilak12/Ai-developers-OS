import os
import shutil
import tempfile
import pytest
from observability.models import SpanStatus, WorkflowTrace, AgentSpan, ToolCallTrace
from observability.tracer import AgentTracer
from observability.metrics import MetricsCollector
from observability.manager import ObservabilityManager
from orchestrator.workflow import MultiAgentOrchestrator


def test_agent_tracer_lifecycle():
    tracer = AgentTracer()
    trace = tracer.start_workflow_trace("wf-test-1", "Test tracing workflow")
    assert trace.workflow_id == "wf-test-1"
    assert trace.total_tokens == 0

    span = tracer.start_agent_span("wf-test-1", "Planner Agent", {"key": "val"})
    assert span.agent_name == "Planner Agent"
    assert span.status == SpanStatus.RUNNING

    tool_call = tracer.record_tool_call(
        "wf-test-1",
        "Planner Agent",
        "rag.query",
        {"query": "auth"},
        duration_ms=15.0
    )
    assert tool_call.tool_name == "rag.query"
    assert len(span.tool_calls) == 1

    ended_span = tracer.end_agent_span(
        "wf-test-1",
        "Planner Agent",
        status=SpanStatus.COMPLETED,
        duration_sec=2.5,
        input_tokens=1000,
        output_tokens=500
    )
    assert ended_span.status == SpanStatus.COMPLETED
    assert ended_span.duration_sec == 2.5
    assert ended_span.estimated_cost_usd > 0
    assert trace.total_tokens == 1500

    completed_trace = tracer.complete_workflow_trace("wf-test-1", status="COMPLETED")
    assert completed_trace.status == "COMPLETED"
    assert len(completed_trace.spans) == 1
    assert completed_trace.total_duration_sec == 2.5


def test_observability_manager_and_metrics():
    temp_dir = tempfile.mkdtemp()
    try:
        storage_path = os.path.join(temp_dir, "custom_traces.json")
        mgr = ObservabilityManager(temp_dir, storage_path=storage_path)
        
        # Check seed traces loaded
        traces = mgr.list_traces()
        assert len(traces) >= 1
        
        trace = mgr.get_trace("wf-182")
        assert trace is not None
        assert trace.task_id == "task-182"
        assert len(trace.spans) == 6

        metrics = mgr.get_metrics()
        assert metrics.total_tasks_executed >= 1
        assert metrics.task_success_rate == 100.0
        assert metrics.total_tokens_consumed > 0
        assert metrics.total_cost_usd > 0
    finally:
        shutil.rmtree(temp_dir)


def test_orchestrator_observability_integration():
    temp_dir = tempfile.mkdtemp()
    try:
        orchestrator = MultiAgentOrchestrator(temp_dir)
        state = orchestrator.execute_workflow(
            task_request="Add OpenTelemetry tracing to checkout service",
            auto_approve=True,
            test_command="echo PASS"
        )
        assert state.workflow_id in orchestrator.observability.traces
        trace = orchestrator.observability.get_trace(state.workflow_id)
        assert trace is not None
        assert len(trace.spans) >= 5
        assert trace.total_tokens > 0
        assert trace.total_cost_usd > 0
    finally:
        shutil.rmtree(temp_dir)
