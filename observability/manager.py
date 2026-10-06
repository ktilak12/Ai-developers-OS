import os
import json
from typing import List, Dict, Any, Optional
from observability.models import WorkflowTrace, AgentSpan, ToolCallTrace, ObservabilityMetrics, SpanStatus
from observability.tracer import AgentTracer
from observability.metrics import MetricsCollector


class ObservabilityManager:
    """
    Central manager for Phase 15 Observability.
    Coordinates OpenTelemetry tracing, metrics aggregation, and persistence.
    """

    def __init__(self, root_dir: str, storage_path: Optional[str] = None):
        self.root_dir = root_dir
        self.storage_path = storage_path or os.path.join(root_dir, ".observability", "traces.json")
        self.tracer = AgentTracer()
        self.traces: Dict[str, WorkflowTrace] = {}
        
        self._load_from_storage()
        if not self.traces:
            self._initialize_seed_traces()
            self.save_to_storage()

    def _load_from_storage(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    trace = WorkflowTrace(**item)
                    self.traces[trace.workflow_id] = trace
            except Exception as e:
                print(f"[ObservabilityManager] Error loading traces: {e}")

    def save_to_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = [t.model_dump() for t in self.traces.values()]
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _initialize_seed_traces(self):
        """Seed initial benchmark traces matching project specifications (PDF pages 16 & 33)."""
        # Trace #182 (PDF page 16)
        trace_182 = WorkflowTrace(
            trace_id="trace-182",
            workflow_id="wf-182",
            task_id="task-182",
            task_title="Fix checkout bug when expired coupon is applied",
            status="COMPLETED",
            total_duration_sec=39.4,
            total_tokens=14200,
            total_cost_usd=0.0845,
            retry_count=1,
            spans=[
                AgentSpan(
                    span_id="span-182-1",
                    agent_name="Planner Agent",
                    status=SpanStatus.COMPLETED,
                    duration_sec=4.2,
                    input_tokens=2200,
                    output_tokens=650,
                    estimated_cost_usd=0.0163,
                    tool_calls=[
                        ToolCallTrace(tool_name="rag.query", arguments={"query": "coupon checkout"}),
                        ToolCallTrace(tool_name="ast.search_symbols", arguments={"symbol": "CouponService"}),
                        ToolCallTrace(tool_name="fs.get_metadata", arguments={"path": "apps/api/routes/checkout.py"})
                    ]
                ),
                AgentSpan(
                    span_id="span-182-2",
                    agent_name="Researcher Agent",
                    status=SpanStatus.COMPLETED,
                    duration_sec=2.1,
                    input_tokens=1800,
                    output_tokens=320,
                    estimated_cost_usd=0.0102,
                    tool_calls=[
                        ToolCallTrace(tool_name="docs.search_best_practices", arguments={"topic": "oauth session"})
                    ]
                ),
                AgentSpan(
                    span_id="span-182-3",
                    agent_name="Coder Agent",
                    status=SpanStatus.COMPLETED,
                    duration_sec=13.8,
                    input_tokens=4100,
                    output_tokens=950,
                    estimated_cost_usd=0.0265,
                    tool_calls=[
                        ToolCallTrace(tool_name="fs.read_file", arguments={"path": "apps/api/routes/checkout.py"}),
                        ToolCallTrace(tool_name="coder.generate_diff", arguments={"path": "apps/api/routes/checkout.py"}),
                        ToolCallTrace(tool_name="fs.write_file", arguments={"path": "apps/api/routes/checkout.py"})
                    ]
                ),
                AgentSpan(
                    span_id="span-182-4",
                    agent_name="Testing Agent",
                    status=SpanStatus.COMPLETED,
                    duration_sec=9.4,
                    input_tokens=1900,
                    output_tokens=400,
                    estimated_cost_usd=0.0117,
                    tool_calls=[
                        ToolCallTrace(tool_name="sandbox.run_test", arguments={"command": "npm test"}),
                        ToolCallTrace(tool_name="tester.extract_failure_details", arguments={})
                    ]
                ),
                AgentSpan(
                    span_id="span-182-5",
                    agent_name="Security Agent",
                    status=SpanStatus.COMPLETED,
                    duration_sec=6.2,
                    input_tokens=1400,
                    output_tokens=250,
                    estimated_cost_usd=0.0079,
                    tool_calls=[
                        ToolCallTrace(tool_name="security.scan_content", arguments={"file": "checkout.py"})
                    ]
                ),
                AgentSpan(
                    span_id="span-182-6",
                    agent_name="Review Agent",
                    status=SpanStatus.COMPLETED,
                    duration_sec=5.8,
                    input_tokens=2800,
                    output_tokens=520,
                    estimated_cost_usd=0.0162,
                    tool_calls=[
                        ToolCallTrace(tool_name="reviewer.analyze_diff", arguments={"diff_lines": 40})
                    ]
                )
            ]
        )
        self.traces[trace_182.workflow_id] = trace_182

    def record_workflow_trace(self, trace: WorkflowTrace):
        self.traces[trace.workflow_id] = trace
        self.save_to_storage()

    def get_trace(self, workflow_id_or_trace_id: str) -> Optional[WorkflowTrace]:
        for trace in self.traces.values():
            if trace.workflow_id == workflow_id_or_trace_id or trace.trace_id == workflow_id_or_trace_id:
                return trace
        return None

    def list_traces(self) -> List[WorkflowTrace]:
        return sorted(list(self.traces.values()), key=lambda t: t.created_at, reverse=True)

    def get_metrics(self) -> ObservabilityMetrics:
        return MetricsCollector.compute_metrics(list(self.traces.values()))
