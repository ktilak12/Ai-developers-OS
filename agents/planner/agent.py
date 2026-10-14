import os
import re
import json
from typing import Dict, Any, List
from agents.planner.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
from agents.planner.tools import PlannerTools
from intelligence.retrieval.retriever import ProjectRAGPipeline
from intelligence.indexing.code_indexer import CodeIndexer
from intelligence.retrieval.symbol_search import SymbolSearchEngine
from memory.manager import ProjectMemoryManager
from llm.provider import get_llm_provider, LLMMessage


class PlannerAgent:
    """
    Planner Agent: Analyzes software requests and produces structured, context-aware
    implementation plans using Project RAG, Code Intelligence, Project Memory, and
    a configurable LLM provider (Gemini / OpenAI / Anthropic).
    Includes security guards against prompt injection / DoS via task bounding and safe path resolution.
    """

    MAX_TASK_LENGTH = 5000

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))
        self.tools = PlannerTools(self.root_dir)
        self.rag = ProjectRAGPipeline(self.root_dir)
        self.memory = ProjectMemoryManager(self.root_dir)
        self._llm = None  # lazy init

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    # ------------------------------------------------------------------
    # Heuristic plan builder (runs in all cases to populate structured fields)
    # ------------------------------------------------------------------
    def _build_heuristic_plan(
        self,
        clean_request: str,
        retrieved_files: List[str],
        ast_symbols: List[Dict[str, Any]],
        primary_files: List[str],
    ) -> Dict[str, Any]:
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

        structured_steps = [
            {
                "step": 1,
                "title": "Inspect & Verify Dependencies",
                "target_file": primary_files[0] if primary_files else "apps/api/main.py",
                "action": "READ",
                "description": (
                    f"Analyze existing exports and AST symbols matching '{clean_request}' "
                    "to establish baseline constraints."
                )
            },
            {
                "step": 2,
                "title": "Backend API Endpoint / Logic Implementation",
                "target_file": "apps/api/main.py",
                "action": "MODIFY",
                "description": (
                    "Add backend data handlers, Pydantic request models, "
                    "and route definitions with error validation."
                )
            },
            {
                "step": 3,
                "title": "Frontend State & Component Integration",
                "target_file": primary_files[0] if primary_files else "apps/web/src/app/dashboard/page.tsx",
                "action": "MODIFY",
                "description": (
                    "Update React state management, user interactive controls, "
                    "and API client request dispatchers."
                )
            },
            {
                "step": 4,
                "title": "Docker Sandbox Test Execution",
                "target_file": "tests/unit/test_agent.py",
                "action": "EXECUTE",
                "description": "Execute build verification and unit test suite inside isolated Docker Sandbox.",
            },
            {
                "step": 5,
                "title": "Diff Generation & Developer Approval",
                "target_file": "git / workspace",
                "action": "REVIEW",
                "description": (
                    "Generate clean unified diff output and pause workflow "
                    "at developer approval gate before PR creation."
                )
            }
        ]

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

        return {
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
            "implementation_steps": [
                f"{s['step']}. [{s['action']}] {s['title']}: {s['description']}"
                for s in structured_steps
            ],
            "structured_steps": structured_steps,
            "potential_risks": [
                f"[{r['severity']}] {r['risk']} (Mitigation: {r['mitigation']})"
                for r in risks
            ],
            "risk_matrix": risks,
            "testing_requirements": [
                "Run `npm run build` to verify Next.js TypeScript strict compliance.",
                "Run `pytest` test suite to validate backend route contracts.",
                "Execute Docker Sandbox container run with resource limits."
            ],
            "developer_approval_required": True,
        }

    # ------------------------------------------------------------------
    # LLM enrichment layer
    # ------------------------------------------------------------------
    def _enrich_with_llm(
        self,
        plan: Dict[str, Any],
        clean_request: str,
        rag_context: str,
        file_metadata_str: str,
        memory_context: str,
    ) -> Dict[str, Any]:
        """
        Calls the configured LLM to produce a richer, task-specific plan.
        Merges the LLM insights into the structured heuristic plan.
        Gracefully degrades if the LLM is unavailable or returns a stub response.
        """
        user_prompt = PLANNER_USER_TEMPLATE.format(
            task_request=clean_request,
            repo_context=rag_context,
            file_metadata=file_metadata_str,
        )

        if memory_context:
            user_prompt += f"\n\nProject Memory Context:\n{memory_context}"

        try:
            response = self.llm.chat(
                messages=[LLMMessage(role="user", content=user_prompt)],
                system_prompt=PLANNER_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=4096,
            )

            llm_text = response.content.strip()

            # Skip stub responses
            if response.provider == "stub" or "[StubProvider]" in llm_text:
                plan["llm_enrichment"] = None
                plan["llm_provider"] = "stub"
                return plan

            plan["llm_enrichment"] = {
                "provider": response.provider,
                "model": response.model,
                "raw_analysis": llm_text,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            }
            plan["llm_provider"] = response.provider

            # Try to parse LLM JSON if it returned a structured response
            json_match = re.search(r'\{[\s\S]+\}', llm_text)
            if json_match:
                try:
                    llm_plan = json.loads(json_match.group(0))
                    # Merge LLM fields into heuristic plan (LLM wins for content)
                    for key in ("goal", "requirements", "implementation_steps",
                                "potential_risks", "testing_requirements"):
                        if key in llm_plan and llm_plan[key]:
                            plan[key] = llm_plan[key]
                except json.JSONDecodeError:
                    pass  # Use raw_analysis as supplementary context

        except Exception as exc:
            plan["llm_enrichment"] = {"error": str(exc)}
            plan["llm_provider"] = "error"

        return plan

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_plan(self, task_request: str) -> Dict[str, Any]:
        # Sanitize task request input
        clean_request = re.sub(
            r"[\x00-\x1f\x7f-\x9f]", " ", str(task_request or "")
        ).strip()[:self.MAX_TASK_LENGTH]
        if not clean_request:
            clean_request = "Default implementation plan: Inspect repository structure and dependencies."

        # Step 1: Query RAG vector index for relevant code chunks
        rag_res = self.rag.query(clean_request, top_k=4)
        retrieved_files = rag_res.get("retrieved_files", [])
        results_count = rag_res.get("total_results", 0)

        # Build RAG context string for LLM
        rag_context_lines = []
        for chunk in rag_res.get("results", [])[:4]:
            if isinstance(chunk, dict):
                rag_context_lines.append(
                    f"File: {chunk.get('file', '')} (score: {chunk.get('score', 0):.3f})\n"
                    f"{chunk.get('content', '')[:600]}"
                )
        rag_context = "\n\n".join(rag_context_lines) or "No RAG chunks retrieved."

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

        # Step 3: Primary affected files
        primary_files = (
            [f for f in retrieved_files if ".." not in f and not f.startswith("/")]
            if retrieved_files
            else [
                "apps/web/src/app/login/page.tsx",
                "apps/api/main.py",
                "agents/coder/agent.py",
            ]
        )

        # Step 4: Build heuristic plan
        plan = self._build_heuristic_plan(
            clean_request, retrieved_files, ast_symbols, primary_files
        )

        # Step 5: File metadata for LLM context
        file_metadata_lines = []
        for file_path in primary_files[:5]:
            meta = self.tools.get_file_metadata(file_path)
            file_metadata_lines.append(
                f"- {file_path}: exists={meta.get('exists')}, "
                f"lines={meta.get('line_count', 0)}"
            )
        file_metadata_str = "\n".join(file_metadata_lines) or "No file metadata."

        # Step 6: Memory context
        memory_context = self.memory.get_llm_context(clean_request)

        # Step 7: Enrich with LLM
        plan = self._enrich_with_llm(
            plan, clean_request, rag_context, file_metadata_str, memory_context
        )

        # Step 8: Attach retrieved context summary
        plan["retrieved_context_summary"] = {
            "rag_chunks_found": results_count,
            "ast_symbols_matched": len(ast_symbols),
            "top_retrieved_files": retrieved_files[:4],
            "top_matched_symbols": [
                s.get("name", s.get("symbol_name", "")) for s in ast_symbols[:4]
            ],
            "project_memory_context": memory_context,
        }

        return plan
