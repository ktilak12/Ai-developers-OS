import os
from typing import Dict, Any, List, Optional
from agents.researcher.tools import ResearcherTools


class ResearcherAgent:
    """
    Researcher Agent: Investigates external technical knowledge, official documentation,
    library APIs, migration guides, compatibility, and implementation patterns.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tools = ResearcherTools(root_dir)

    def research_task(self, task_request: str) -> Dict[str, Any]:
        """Performs technical research to inform Planner and Coder agents."""
        deps = self.tools.inspect_dependencies()
        best_practices = self.tools.search_best_practices(task_request)

        # Detect potential breaking changes or specific library patterns
        breaking_changes = []
        task_lower = task_request.lower()

        if "oauth" in task_lower or "auth" in task_lower:
            breaking_changes.append("Verify redirect URIs and CSRF state token handling.")
            breaking_changes.append("Ensure session cookie flags are set to SameSite=Lax and Secure=True.")
        elif "upgrade" in task_lower:
            breaking_changes.append("Check peer dependency conflicts between React 19 and older third-party packages.")
        elif "database" in task_lower or "sql" in task_lower:
            breaking_changes.append("Ensure schema migrations have down/rollback scripts prepared.")

        return {
            "status": "success",
            "task_request": task_request,
            "detected_stack_dependencies": list(deps.get("node_dependencies", {}).keys())[:8],
            "relevant_best_practices": best_practices,
            "breaking_changes_flags": breaking_changes,
            "recommended_approach": f"Implement changes following standard decoupled architecture with proper unit test assertions for '{task_request}'.",
            "references": [bp.get("reference", "") for bp in best_practices]
        }
