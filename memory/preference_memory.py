from typing import List, Dict, Optional
from memory.models import DeveloperPreferenceRecord, PreferenceCategory


class PreferenceMemoryStore:
    """
    Manages Developer Preferences and Project Conventions Memory:
    Code formatting, naming rules, preferred test runners, linting, and framework rules.
    """

    def __init__(self, records: Optional[List[DeveloperPreferenceRecord]] = None):
        self.records: Dict[str, DeveloperPreferenceRecord] = {}
        if records:
            for rec in records:
                self.records[rec.id] = rec

    def add_or_update_preference(self, record: DeveloperPreferenceRecord) -> DeveloperPreferenceRecord:
        self.records[record.id] = record
        return record

    def get_preference(self, pref_id: str) -> Optional[DeveloperPreferenceRecord]:
        return self.records.get(pref_id)

    def list_by_category(self, category: Optional[PreferenceCategory] = None) -> List[DeveloperPreferenceRecord]:
        if category:
            return [rec for rec in self.records.values() if rec.category == category]
        return list(self.records.values())

    def search_preferences(self, query: str) -> List[DeveloperPreferenceRecord]:
        query_lower = query.lower()
        results = []
        for rec in self.records.values():
            if (query_lower in rec.key.lower() or
                query_lower in rec.value.lower() or
                query_lower in rec.description.lower()):
                results.append(rec)
        return results
