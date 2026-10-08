import os
import re
from typing import Dict, Any, List
from agents.planner.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
from agents.planner.tools import PlannerTools
from intelligence.retrieval.retriever import ProjectRAGPipeline
from intelligence.indexing.code_indexer import CodeIndexer
from intelligence.retrieval.symbol_search import SymbolSearchEngine
from memory.manager import ProjectMemoryManager

class PlannerAgent:
    """
    Planner Agent: Analyzes software requests and produces structured, context-aware implementation plans
    using Project RAG, Code Intelligence, and Project Memory (ADRs, preferences, architecture).
    Includes security guards against prompt injection / DoS via task bounding and safe path resolution.
    """

    MAX_TASK_LENGTH = 5000

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))
        self.tools = PlannerTools(self.root_dir)
        self.rag = ProjectRAGPipeline(self.root_dir)
        self.memory = ProjectMemoryManager(self.root_dir)
        
    def generate_plan(self, task_request: str) -> Dict[str, Any]:
        # Sanitize task request input
        clean_request = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(task_request or "")).strip()[:self.MAX_TASK_LENGTH]
        if not clean_request:
            clean_request = "Default implementation plan: Inspect repository structure and dependencies."

        # Step 1: Query RAG vector index for relevant code chunks
        rag_res = self.rag.query(clean_request, top_k=4)
        retrieved_files = rag_res.get("retrieved_files", [])
        results_count = rag_res.get("total_results", 0)

        # Step 2: Query Code Intelligence AST symbols
        ast_symbols: List[Dict[str, Any]] = []
        try:
            indexer = CodeIndexer(self.root_dir)
            index_data = indexer.scan_and_index()
            search_engine = SymbolSearchEngine(index_data)
            search_res = search_engine.search(clean_request)
            if isinstance(search_res, dict):
                ast_symbols = (
                    search_res.get("matched_functions", []) +
                    search_res.get("matched_classes", []) +
                    search_res.get("matched_components", [])
                )
            elif isinstance(search_res, list):
                ast_symbols = search_res
        except Exception:
            ast_symbols = []

        # Step 3: Inspect metadata for key affected files
        primary_files = [f for f in retrieved_files if ".." not in f and not f.startswith("/")] if retrieved_files else [
            "apps/web/src/app/login/page.tsx",
            "apps/api/main.py",
            "agents/coder/agent.py"
        ]

        affected_files_detailed = []
        for file_path in primary_files[:5]:
            meta = self.tools.get_file_metadata(file_path)

            action = "MODIFY" if meta.get("exists", False) else "CREATE"
            line_count = meta.get("line_count", 0)
            affected_files_detailed.append({
                "path": file_path,
                "action": action,
                "line_count": line_count,
                "est_changes": "+15 / -5" if action == "MODIFY" else "+45 / -0"
            })

        # Step 4: Build detailed structured implementation steps
        structured_steps = [
            {
                "step": 1,
                "title": "Inspect & Verify Dependencies",
                "target_file": primary_files[0] if primary_files else "apps/api/main.py",
                "action": "READ",
                "description": f"Analyze existing exports and AST symbols matching '{task_request}' to establish baseline constraints."
            },
            {
                "step": 2,
                "title": "Backend API Endpoint / Logic Implementation",
                "target_file": "apps/api/main.py",
                "action": "MODIFY",
                "description": "Add backend data handlers, Pydantic request models, and route definitions with error validation."
            },
            {
                "step": 3,
                "title": "Frontend State & Component Integration",
                "target_file": primary_files[0] if primary_files else "apps/web/src/app/dashboard/page.tsx",
                "action": "MODIFY",
                "description": "Update React state management, user interactive controls, and API client request dispatchers."
            },
            {
                "step": 4,
                "title": "Docker Sandbox Test Execution",
                "target_file": "tests/unit/test_agent.py",
                "action": "EXECUTE",
                "description": "Execute build verification and unit test suite inside isolated Docker Sandbox environment."
            },
            {
                "step": 5,
                "title": "Diff Generation & Developer Approval",
                "target_file": "git / workspace",
                "action": "REVIEW",
                "description": "Generate clean unified diff output and pause workflow at developer approval gate before PR creation."
            }
        ]

        # Step 5: Risk Assessment Matrix
        risks = [
            {
                "risk": "Breaking REST API backward compatibility for active sessions.",
                "severity": "HIGH",
                "mitigation": "Enforce optional parameters and versioned route handlers."
            },
            {
                "risk": "State synchronization mismatch between Next.js frontend and FastAPI backend.",
                "severity": "MEDIUM",
                "mitigation": "Share explicit TypeScript interface contracts matching FastAPI Pydantic schema."
            },
            {
                "risk": "Performance regression during large codebase AST indexing.",
                "severity": "LOW",
                "mitigation": "Cache AST symbol lookup table in memory with lazy invalidation."
            }
        ]

        # Step 6: Construct complete Plan response matching PDF specifications
        plan = {
            "task_request": clean_request,
            "goal": f"Execute software update for: '{clean_request}'",
            "requirements": [
                f"Verify requirements for '{clean_request}' against codebase architecture.",
                "Ensure zero breaking changes to active endpoints or component states.",
                "Maintain dark theme design system styling (neutral-950 background, tailored glows).",
                "Require explicit developer approval gate before code merging or PR creation."
            ],
            "affected_files": [f["path"] for f in affected_files_detailed],
            "affected_files_detailed": affected_files_detailed,
            "implementation_steps": [f"{s['step']}. [{s['action']}] {s['title']}: {s['description']}" for s in structured_steps],
            "structured_steps": structured_steps,
            "potential_risks": [f"[{r['severity']}] {r['risk']} (Mitigation: {r['mitigation']})" for r in risks],
            "risk_matrix": risks,
            "testing_requirements": [
                "Run `npm run build` to verify Next.js TypeScript strict compliance.",
                "Run `pytest` test suite to validate backend route contracts.",
                "Execute Docker Sandbox container run with resource limits."
            ],
            "retrieved_context_summary": {
                "rag_chunks_found": results_count,
                "ast_symbols_matched": len(ast_symbols),
                "top_retrieved_files": retrieved_files[:4],
                "top_matched_symbols": [s.get("name", s.get("symbol_name", "")) for s in ast_symbols[:4]],
                "project_memory_context": self.memory.get_llm_context(task_request)
            },
            "developer_approval_required": True
        }

        return plan

