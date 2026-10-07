import re
from typing import Dict, Any, List, Set

class SymbolSearchEngine:
    """
    Search engine over the Code Intelligence index.
    Answers queries like 'Where is authentication implemented?' by matching
    symbols, file paths, routes, and component names.
    Includes security protections: input sanitization, query length bounds,
    and result pagination / caps to prevent memory DoS.
    """

    MAX_QUERY_LENGTH = 200
    DEFAULT_MAX_RESULTS = 50
    MAX_TERMS_LIMIT = 10

    def __init__(self, index: Dict[str, Any]):
        self.index = index or {}

    def _sanitize_query(self, query: str) -> str:
        """Sanitizes query input, removing control characters and bounding length."""
        if not query or not isinstance(query, str):
            return ""
        # Strip non-printable and control characters
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", query).strip()
        return cleaned[:self.MAX_QUERY_LENGTH]

    def search(self, query: str, max_results: int = DEFAULT_MAX_RESULTS) -> Dict[str, Any]:
        query_clean = self._sanitize_query(query)
        effective_limit = max(1, min(max_results, 100))

        results: Dict[str, Any] = {
            "query": query_clean,
            "relevant_files": [],
            "matched_functions": [],
            "matched_classes": [],
            "matched_components": [],
            "matched_routes": [],
            "matched_models": [],
            "answer_summary": ""
        }

        if not query_clean:
            results["answer_summary"] = "Empty search query provided. Please provide a symbol, function, or file name."
            return results

        query_lower = query_clean.lower()
        terms = [t for t in re.split(r"[\s_.\-:/]+", query_lower) if len(t) > 1][:self.MAX_TERMS_LIMIT]
        relevant_files_set: Set[str] = set()

        # Match functions
        for func in self.index.get("functions", []):
            if len(results["matched_functions"]) >= effective_limit:
                break
            name = func.get("name", "") if isinstance(func, dict) else str(func)
            file_path = func.get("file", "") if isinstance(func, dict) else ""
            name_lower = name.lower()
            if query_lower in name_lower or (terms and any(term in name_lower for term in terms)):
                results["matched_functions"].append(func)
                if file_path:
                    relevant_files_set.add(file_path)

        # Match classes
        for cls in self.index.get("classes", []):
            if len(results["matched_classes"]) >= effective_limit:
                break
            name = cls.get("name", "") if isinstance(cls, dict) else str(cls)
            file_path = cls.get("file", "") if isinstance(cls, dict) else ""
            name_lower = name.lower()
            if query_lower in name_lower or (terms and any(term in name_lower for term in terms)):
                results["matched_classes"].append(cls)
                if file_path:
                    relevant_files_set.add(file_path)

        # Match components
        for comp in self.index.get("components", []):
            if len(results["matched_components"]) >= effective_limit:
                break
            name = comp.get("name", "") if isinstance(comp, dict) else str(comp)
            file_path = comp.get("file", "") if isinstance(comp, dict) else ""
            name_lower = name.lower()
            if query_lower in name_lower or (terms and any(term in name_lower for term in terms)):
                results["matched_components"].append(comp)
                if file_path:
                    relevant_files_set.add(file_path)

        # Match routes
        for r in self.index.get("routes", []):
            if len(results["matched_routes"]) >= effective_limit:
                break
            path = r.get("path", "") if isinstance(r, dict) else str(r)
            file_path = r.get("file", "") if isinstance(r, dict) else ""
            path_lower = path.lower()
            if query_lower in path_lower or (terms and any(term in path_lower for term in terms)):
                results["matched_routes"].append(r)
                if file_path:
                    relevant_files_set.add(file_path)

        # Match models
        for m in self.index.get("models", []):
            if len(results["matched_models"]) >= effective_limit:
                break
            name = m.get("name", "") if isinstance(m, dict) else str(m)
            file_path = m.get("file", "") if isinstance(m, dict) else ""
            name_lower = name.lower()
            if query_lower in name_lower or (terms and any(term in name_lower for term in terms)):
                results["matched_models"].append(m)
                if file_path:
                    relevant_files_set.add(file_path)

        results["relevant_files"] = list(relevant_files_set)[:effective_limit]

        # Construct natural language answer summary
        if results["relevant_files"]:
            files_str = ", ".join(results["relevant_files"][:3])
            results["answer_summary"] = f"Found relevant code definitions in {files_str} matching '{query_clean}'."
        else:
            results["answer_summary"] = f"No exact symbol match found for '{query_clean}'. Try searching for specific module names."

        return results
