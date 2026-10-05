from typing import List, Dict, Optional
from memory.models import TaskHistoryRecord, TaskStatus


class TaskMemoryStore:
    """
    Manages Task History Memory: previous engineering tasks, modified files,
    test results, failures, and resolution summaries.
    """

    def __init__(self, records: Optional[List[TaskHistoryRecord]] = None):
        self.records: Dict[str, TaskHistoryRecord] = {}
        if records:
            for rec in records:
                self.records[rec.id] = rec

    def record_task(self, record: TaskHistoryRecord) -> TaskHistoryRecord:
        self.records[record.id] = record
        return record

    def get_task(self, task_id: str) -> Optional[TaskHistoryRecord]:
        return self.records.get(task_id)

    def list_tasks(self, limit: int = 50, status: Optional[TaskStatus] = None) -> List[TaskHistoryRecord]:
        tasks = list(self.records.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda x: x.timestamp, reverse=True)
        return tasks[:limit]

    def search_tasks(self, query: str) -> List[TaskHistoryRecord]:
        query_lower = query.lower()
        results = []
        for rec in self.records.values():
            if (query_lower in rec.task_title.lower() or
                query_lower in rec.task_request.lower() or
                (rec.fix_summary and query_lower in rec.fix_summary.lower()) or
                any(query_lower in f.lower() for f in rec.files_changed)):
                results.append(rec)
        return results
