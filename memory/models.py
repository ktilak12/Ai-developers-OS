from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class DecisionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


class TaskStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PreferenceCategory(str, Enum):
    CODING_STYLE = "CODING_STYLE"
    TESTING = "TESTING"
    CONVENTIONS = "CONVENTIONS"
    FRAMEWORK = "FRAMEWORK"
    REVIEW = "REVIEW"


class ArchitectureRecord(BaseModel):
    id: str
    component_name: str
    technology_stack: List[str] = Field(default_factory=list)
    entrypoints: List[str] = Field(default_factory=list)
    conventions: List[str] = Field(default_factory=list)
    description: str
    dependencies: List[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionRecord(BaseModel):
    id: str
    title: str
    status: DecisionStatus = DecisionStatus.ACCEPTED
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    author: str = "AI Developer OS"
    context: str
    decision: str
    consequences: List[str] = Field(default_factory=list)
    alternatives_considered: List[str] = Field(default_factory=list)


class TaskHistoryRecord(BaseModel):
    id: str
    task_title: str
    task_request: str
    agent_name: str
    status: TaskStatus = TaskStatus.COMPLETED
    files_changed: List[str] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    fix_summary: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DeveloperPreferenceRecord(BaseModel):
    id: str
    category: PreferenceCategory
    key: str
    value: str
    description: str
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MemoryOverview(BaseModel):
    total_architecture_components: int
    total_decisions: int
    total_tasks_recorded: int
    total_preferences: int
    recent_decisions: List[DecisionRecord] = Field(default_factory=list)
    recent_tasks: List[TaskHistoryRecord] = Field(default_factory=list)
