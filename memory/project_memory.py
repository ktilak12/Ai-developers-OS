from typing import List, Dict, Optional
from memory.models import ArchitectureRecord


class ArchitectureMemoryStore:
    """
    Manages architecture memory: components, technology stack, entrypoints,
    module boundaries, and architectural conventions.
    """

    def __init__(self, records: Optional[List[ArchitectureRecord]] = None):
        self.records: Dict[str, ArchitectureRecord] = {}
        if records:
            for rec in records:
                self.records[rec.id] = rec

    def add_or_update(self, record: ArchitectureRecord) -> ArchitectureRecord:
        self.records[record.id] = record
        return record

    def get_by_id(self, record_id: str) -> Optional[ArchitectureRecord]:
        return self.records.get(record_id)

    def list_all(self) -> List[ArchitectureRecord]:
        return list(self.records.values())

    def search_components(self, query: str) -> List[ArchitectureRecord]:
        query_lower = query.lower()
        results = []
        for rec in self.records.values():
            if (query_lower in rec.component_name.lower() or 
                query_lower in rec.description.lower() or
                any(query_lower in tech.lower() for tech in rec.technology_stack) or
                any(query_lower in dep.lower() for dep in rec.dependencies)):
                results.append(rec)
        return results

    def get_stack_summary(self) -> Dict[str, List[str]]:
        all_tech = set()
        all_entrypoints = []
        for rec in self.records.values():
            all_tech.update(rec.technology_stack)
            all_entrypoints.extend(rec.entrypoints)
        return {
            "technologies": sorted(list(all_tech)),
            "entrypoints": sorted(list(set(all_entrypoints))),
            "components_count": len(self.records)
        }
