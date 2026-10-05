from typing import List, Dict, Optional
from memory.models import DecisionRecord, DecisionStatus


class DecisionMemoryStore:
    """
    Manages Decision Memory: Architectural Decision Records (ADRs), 
    trade-offs, alternatives considered, and rationale.
    """

    def __init__(self, records: Optional[List[DecisionRecord]] = None):
        self.records: Dict[str, DecisionRecord] = {}
        if records:
            for rec in records:
                self.records[rec.id] = rec

    def add_decision(self, record: DecisionRecord) -> DecisionRecord:
        self.records[record.id] = record
        return record

    def get_decision(self, record_id: str) -> Optional[DecisionRecord]:
        return self.records.get(record_id)

    def list_decisions(self, status: Optional[DecisionStatus] = None) -> List[DecisionRecord]:
        if status:
            return [rec for rec in self.records.values() if rec.status == status]
        return list(self.records.values())

    def update_status(self, record_id: str, new_status: DecisionStatus) -> Optional[DecisionRecord]:
        if record_id in self.records:
            self.records[record_id].status = new_status
            return self.records[record_id]
        return None

    def search_decisions(self, query: str) -> List[DecisionRecord]:
        query_lower = query.lower()
        results = []
        for rec in self.records.values():
            if (query_lower in rec.title.lower() or
                query_lower in rec.context.lower() or
                query_lower in rec.decision.lower() or
                any(query_lower in alt.lower() for alt in rec.alternatives_considered)):
                results.append(rec)
        return results
