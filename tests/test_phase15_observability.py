import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from observability.manager import ObservabilityManager
from observability.tracer import AgentTracer
from observability.models import SpanStatus

client = TestClient(app)


def test_agent_tracer_lifecycle_and_cost_calculation():
    tracer = AgentTracer()
    wf_id = "wf-test-101"

    # Start trace
    trace = tracer.start_workflow_trace(wf_id, "Implement Redis caching")
    assert trace.workflow_id == wf_id

    # Agent Span 1: Planner
    span1 = tracer.start_agent_span(wf_id, "Planner Agent", {"agent": "planner"})
    tracer.record_tool_call(wf_id, "Planner Agent", "rag.query", {"query": "redis"}, duration_ms=15.0)
    tracer.end_agent_span(wf_id, "Planner Agent", status=SpanStatus.COMPLETED, duration_sec=2.5, input_tokens=1000, output_tokens=300)

    # Agent Span 2: Coder
    span2 = tracer.start_agent_span(wf_id, "Coder Agent", {"agent": "coder"})
    tracer.record_tool_call(wf_id, "Coder Agent", "fs.write_file", {"path": "cache.py"}, duration_ms=25.0)
    tracer.end_agent_span(wf_id, "Coder Agent", status=SpanStatus.COMPLETED, duration_sec=5.0, input_tokens=2000, output_tokens=800)

    # Complete trace
    completed_trace = tracer.complete_workflow_trace(wf_id, status="COMPLETED", retry_count=0)
    assert completed_trace.status == "COMPLETED"
    assert len(completed_trace.spans) == 2
    assert completed_trace.total_tokens == (1000 + 300 + 2000 + 800)
    assert completed_trace.total_cost_usd > 0.0
    assert completed_trace.total_duration_sec >= 7.5


def test_observability_manager_persistence_and_metrics():
    temp_dir = tempfile.mkdtemp()
    try:
        mgr = ObservabilityManager(temp_dir)
        metrics = mgr.get_metrics()

        assert metrics.total_tasks_executed >= 1
        assert metrics.total_tokens_consumed > 0
        assert metrics.total_cost_usd > 0.0
        assert metrics.avg_execution_time_sec > 0.0
        assert "agent_latency_breakdown" in metrics.model_dump()
        assert "tool_usage_counts" in metrics.model_dump()

        # Retrieve traces
        traces = mgr.list_traces()
        assert len(traces) >= 1
        first_trace = traces[0]

        # Get specific trace detail
        trace_detail = mgr.get_trace(first_trace.trace_id)
        assert trace_detail is not None
        assert trace_detail.trace_id == first_trace.trace_id
    finally:
        shutil.rmtree(temp_dir)


def test_observability_api_endpoints():
    # 1. /api/observability/metrics
    res_metrics = client.get("/api/observability/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert "total_tasks_executed" in metrics_data
    assert "total_cost_usd" in metrics_data

    # 2. /api/observability/traces
    res_traces = client.get("/api/observability/traces")
    assert res_traces.status_code == 200
    traces_data = res_traces.json()
    assert traces_data["status"] == "success"
    assert len(traces_data["traces"]) >= 1

    trace_id = traces_data["traces"][0]["trace_id"]

    # 3. /api/observability/traces/{trace_id}
    res_detail = client.get(f"/api/observability/traces/{trace_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["trace_id"] == trace_id
    assert "spans" in detail_data


def test_observability_api_error_handling():
    # 1. Non-existent trace ID returns 404
    res_404 = client.get("/api/observability/traces/trace-unknown-99999")
    assert res_404.status_code == 404

    # 2. Oversized trace ID returns 400
    res_oversized = client.get(f"/api/observability/traces/{'x' * 101}")
    assert res_oversized.status_code == 400
