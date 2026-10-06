import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from observability.models import WorkflowTrace, AgentSpan, ToolCallTrace, SpanStatus


class AgentTracer:
    """
    OpenTelemetry-compatible Tracer for autonomous multi-agent software engineering systems.
    Captures end-to-end agent traces, spans, latency, token consumption, and tool execution.
    """

    # Pricing per 1M tokens ($3.00 input, $15.00 output)
    INPUT_TOKEN_COST_PER_M = 3.00
    OUTPUT_TOKEN_COST_PER_M = 15.00

    def __init__(self):
        self._active_traces: Dict[str, WorkflowTrace] = {}
        self._active_spans: Dict[str, AgentSpan] = {}

    def start_workflow_trace(self, workflow_id: str, task_title: str) -> WorkflowTrace:
        trace = WorkflowTrace(
            workflow_id=workflow_id,
            task_id=workflow_id.replace("wf-", "task-"),
            task_title=task_title
        )
        self._active_traces[workflow_id] = trace
        return trace

    def start_agent_span(
        self,
        workflow_id: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentSpan:
        span = AgentSpan(
            agent_name=agent_name,
            status=SpanStatus.RUNNING,
            start_time=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )
        self._active_spans[f"{workflow_id}:{agent_name}"] = span
        return span

    def record_tool_call(
        self,
        workflow_id: str,
        agent_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        duration_ms: float = 12.0,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> ToolCallTrace:
        tool_trace = ToolCallTrace(
            tool_name=tool_name,
            arguments=arguments,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
        span_key = f"{workflow_id}:{agent_name}"
        if span_key in self._active_spans:
            self._active_spans[span_key].tool_calls.append(tool_trace)
        return tool_trace

    def end_agent_span(
        self,
        workflow_id: str,
        agent_name: str,
        status: SpanStatus = SpanStatus.COMPLETED,
        duration_sec: Optional[float] = None,
        input_tokens: int = 1250,
        output_tokens: int = 420
    ) -> Optional[AgentSpan]:
        span_key = f"{workflow_id}:{agent_name}"
        span = self._active_spans.get(span_key)
        if not span:
            span = AgentSpan(agent_name=agent_name)

        span.status = status
        span.end_time = datetime.now(timezone.utc).isoformat()
        if duration_sec is not None:
            span.duration_sec = duration_sec

        span.input_tokens = input_tokens
        span.output_tokens = output_tokens
        
        # Calculate cost
        cost = (
            (input_tokens / 1_000_000.0) * self.INPUT_TOKEN_COST_PER_M +
            (output_tokens / 1_000_000.0) * self.OUTPUT_TOKEN_COST_PER_M
        )
        span.estimated_cost_usd = round(cost, 6)

        # Attach to parent workflow trace
        trace = self._active_traces.get(workflow_id)
        if trace:
            trace.spans.append(span)
            trace.total_tokens += (input_tokens + output_tokens)
            trace.total_cost_usd = round(trace.total_cost_usd + span.estimated_cost_usd, 6)

        return span

    def complete_workflow_trace(
        self,
        workflow_id: str,
        status: str = "COMPLETED",
        retry_count: int = 0
    ) -> Optional[WorkflowTrace]:
        trace = self._active_traces.get(workflow_id)
        if not trace:
            return None

        trace.status = status
        trace.retry_count = retry_count
        trace.total_duration_sec = round(sum(s.duration_sec for s in trace.spans), 2)
        return trace
