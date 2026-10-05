from enum import Enum
from typing import Dict, Any, List, Callable
from datetime import datetime, timezone


class WorkflowEventType(str, Enum):
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    PLAN_GENERATED = "PLAN_GENERATED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    CODE_MODIFIED = "CODE_MODIFIED"
    TESTS_RUN = "TESTS_RUN"
    TESTS_FAILED_RETRYING = "TESTS_FAILED_RETRYING"
    SECURITY_SCANNED = "SECURITY_SCANNED"
    REVIEW_COMPLETED = "REVIEW_COMPLETED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    PR_CREATED = "PR_CREATED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"


class EventBus:
    """Event bus for publishing and subscribing to multi-agent workflow events."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.history: List[Dict[str, Any]] = []

    def subscribe(self, event_type: WorkflowEventType, callback: Callable[[Dict[str, Any]], None]):
        key = event_type.value
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)

    def publish(self, event_type: WorkflowEventType, payload: Dict[str, Any]):
        event = {
            "type": event_type.value,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.history.append(event)
        key = event_type.value
        for cb in self._subscribers.get(key, []):
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Error in event listener: {e}")

    def get_events_for_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.history if e["payload"].get("workflow_id") == workflow_id]
