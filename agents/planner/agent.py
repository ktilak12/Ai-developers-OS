import os
from typing import Dict, Any, List
from agents.planner.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
from agents.planner.tools import PlannerTools
from intelligence.retrieval.retriever import ProjectRAGPipeline

class PlannerAgent:
    """
    Planner Agent: Analyzes software requests and produces structured implementation plans
    before code modifications are executed.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tools = PlannerTools(root_dir)
        self.rag = ProjectRAGPipeline(root_dir)

    def generate_plan(self, task_request: str) -> Dict[str, Any]:
        # Step 1: Query RAG for relevant context
        rag_res = self.rag.query(task_request, top_k=3)
        retrieved_files = rag_res.get("retrieved_files", [])

        # Step 2: Determine affected files and implementation steps based on task
        affected_files = retrieved_files if retrieved_files else ["apps/web/src/app/login/page.tsx", "apps/api/main.py"]

        # Step 3: Construct structured implementation plan object
        plan = {
            "task_request": task_request,
            "goal": f"Implement changes required for: {task_request}",
            "requirements": [
                f"Verify requirements for '{task_request}' against existing codebase architecture.",
                "Ensure zero breaking changes to existing endpoints.",
                "Maintain dark theme design system conventions."
            ],
            "affected_files": affected_files,
            "implementation_steps": [
                "Inspect existing module dependencies using Code Intelligence AST.",
                "Modify state handler and service layers in affected files.",
                "Execute automated unit tests inside Docker Sandbox.",
                "Perform security review for exposed credentials or unsanitized inputs.",
                "Generate code diff and present to developer for approval."
            ],
            "potential_risks": [
                "API contract backwards incompatibility if parameter names change.",
                "Authentication token invalidation during session refresh."
            ],
            "testing_requirements": [
                "Run `npm run build` to verify TypeScript type checking.",
                "Run pytest test suite for API endpoints."
            ]
        }

        return plan
