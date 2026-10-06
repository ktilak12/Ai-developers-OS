from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class BenchmarkTaskCategory(str, Enum):
    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    SECURITY = "security"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"
    API_DESIGN = "api_design"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SWEBenchmarkTask(BaseModel):
    task_id: str
    title: str
    description: str
    category: BenchmarkTaskCategory
    difficulty: DifficultyLevel
    target_files: List[str]
    expected_tools: List[str]
    test_criteria: str
    codebase_context: Optional[str] = None


class EvaluationMetricResult(BaseModel):
    task_id: str
    agent_version: str  # "v1-baseline" or "v2-orchestrated"
    completed: bool
    planning_accuracy: float  # 0 - 100%
    code_correctness: float  # 0 - 100%
    test_success_rate: float  # 0 - 100%
    security_score: float  # 0 - 100
    tool_accuracy: float  # 0 - 100%
    duration_sec: float
    tokens_used: int
    cost_usd: float
    retries_needed: int = 0
    feedback_notes: Optional[str] = None


class AggregateAgentMetrics(BaseModel):
    agent_version: str
    total_tasks: int
    completed_tasks: int
    completion_rate_pct: float
    avg_planning_accuracy: float
    avg_code_correctness: float
    avg_test_success_rate: float
    avg_security_score: float
    avg_tool_accuracy: float
    avg_duration_sec: float
    total_tokens: int
    total_cost_usd: float


class ComparativeScorecard(BaseModel):
    evaluation_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tasks_evaluated_count: int
    v1_baseline: AggregateAgentMetrics
    v2_orchestrated: AggregateAgentMetrics
    completion_improvement_pct: float
    test_success_improvement_pct: float
    security_score_improvement_pct: float
    latency_reduction_pct: float
    task_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
