from typing import Dict, Any, List

class SymbolSearchEngine:
    """
    Search engine over the Code Intelligence index.
    Answers queries like 'Where is authentication implemented?' by matching
    symbols, file paths, routes, and component names.
    """

    def __init__(self, index: Dict[str, Any]):
        self.index = index

    def search(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        results = {
            "query": query,
            "relevant_files": set(),
            "matched_functions": [],
            "matched_classes": [],
            "matched_components": [],
            "matched_routes": [],
            "matched_models": [],
            "answer_summary": ""
        }

        # Match functions
        for func in self.index.get("functions", []):
            name = func.get("name", "")
            file_path = func.get("file", "")
            if query_lower in name.lower() or any(term in name.lower() for term in query_lower.split()):
                results["matched_functions"].append(func)
                results["relevant_files"].add(file_path)

        # Match classes
        for cls in self.index.get("classes", []):
            name = cls.get("name", "")
            file_path = cls.get("file", "")
            if query_lower in name.lower() or any(term in name.lower() for term in query_lower.split()):
                results["matched_classes"].append(cls)
                results["relevant_files"].add(file_path)

        # Match components
        for comp in self.index.get("components", []):
            name = comp.get("name", "")
            file_path = comp.get("file", "")
            if query_lower in name.lower() or any(term in name.lower() for term in query_lower.split()):
                results["matched_components"].append(comp)
                results["relevant_files"].add(file_path)

        # Match routes
        for r in self.index.get("routes", []):
            path = r.get("path", "")
            file_path = r.get("file", "")
            if query_lower in path.lower() or "auth" in path.lower() or "login" in path.lower():
                results["matched_routes"].append(r)
                results["relevant_files"].add(file_path)

        # Match models
        for m in self.index.get("models", []):
            name = m.get("name", "")
            file_path = m.get("file", "")
            if query_lower in name.lower():
                results["matched_models"].append(m)
                results["relevant_files"].add(file_path)

        results["relevant_files"] = list(results["relevant_files"])

        # Construct natural language answer summary
        if results["relevant_files"]:
            files_str = ", ".join(results["relevant_files"][:3])
            results["answer_summary"] = f"Found relevant code definitions in {files_str} matching '{query}'."
        else:
            results["answer_summary"] = f"No exact symbol match found for '{query}'. Try searching for specific module names."

        return results
