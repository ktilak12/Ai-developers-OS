import os
import json
from typing import List, Dict, Any, Optional
from memory.models import (
    ArchitectureRecord, DecisionRecord, TaskHistoryRecord,
    DeveloperPreferenceRecord, DecisionStatus, TaskStatus,
    PreferenceCategory, MemoryOverview
)
from memory.project_memory import ArchitectureMemoryStore
from memory.decision_memory import DecisionMemoryStore
from memory.task_memory import TaskMemoryStore
from memory.preference_memory import PreferenceMemoryStore


class ProjectMemoryManager:
    """
    Unified manager for Phase 13 Project Memory.
    Combines Architecture, Decision (ADR), Task History, and Developer Preferences
    with persistent storage and LLM context synthesis.
    """

    def __init__(self, root_dir: str, storage_path: Optional[str] = None):
        self.root_dir = os.path.abspath(root_dir)
        self.storage_path = os.path.abspath(storage_path) if storage_path else os.path.join(self.root_dir, ".memory", "store.json")
        
        self.architecture = ArchitectureMemoryStore()
        self.decisions = DecisionMemoryStore()
        self.tasks = TaskMemoryStore()
        self.preferences = PreferenceMemoryStore()
        
        self._load_from_storage()
        if self.is_empty():
            self._initialize_seed_memory()
            self.save_to_storage()

    def is_empty(self) -> bool:
        return (
            len(self.architecture.list_all()) == 0 and
            len(self.decisions.list_decisions()) == 0 and
            len(self.tasks.list_tasks()) == 0 and
            len(self.preferences.list_by_category()) == 0
        )

    def _load_from_storage(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                arch_recs = [ArchitectureRecord(**item) for item in data.get("architecture", [])]
                self.architecture = ArchitectureMemoryStore(arch_recs)

                dec_recs = [DecisionRecord(**item) for item in data.get("decisions", [])]
                self.decisions = DecisionMemoryStore(dec_recs)

                task_recs = [TaskHistoryRecord(**item) for item in data.get("tasks", [])]
                self.tasks = TaskMemoryStore(task_recs)

                pref_recs = [DeveloperPreferenceRecord(**item) for item in data.get("preferences", [])]
                self.preferences = PreferenceMemoryStore(pref_recs)
            except Exception as e:
                print(f"[ProjectMemoryManager] Error loading memory store from {self.storage_path}: {e}")

    def save_to_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            "architecture": [rec.model_dump() for rec in self.architecture.list_all()],
            "decisions": [rec.model_dump() for rec in self.decisions.list_decisions()],
            "tasks": [rec.model_dump() for rec in self.tasks.list_tasks(limit=max(1000, len(self.tasks.records)))],
            "preferences": [rec.model_dump() for rec in self.preferences.list_by_category()]
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _initialize_seed_memory(self):
        """Seed initial project memory based on AI Developer OS repository architecture."""
        # Architecture components
        self.architecture.add_or_update(ArchitectureRecord(
            id="arch-fastapi-backend",
            component_name="FastAPI API Control Plane",
            technology_stack=["Python", "FastAPI", "Uvicorn", "Pydantic"],
            entrypoints=["apps/api/main.py"],
            conventions=["RESTful endpoints", "Type annotations", "Pydantic request models"],
            description="Central backend server providing endpoints for code parsing, graph indexing, agent execution, and memory.",
            dependencies=["intelligence", "agents", "sandbox", "mcp"]
        ))

        self.architecture.add_or_update(ArchitectureRecord(
            id="arch-nextjs-web",
            component_name="Next.js Frontend Control Panel",
            technology_stack=["Next.js", "React", "TypeScript", "TailwindCSS"],
            entrypoints=["apps/web/src/app/(dashboard)/layout.tsx"],
            conventions=["App Router", "Dashboard page routes", "Glassmorphic dark design"],
            description="Interactive dashboard web application for human oversight, planning, coding, testing, and memory analysis.",
            dependencies=["FastAPI Backend API"]
        ))

        self.architecture.add_or_update(ArchitectureRecord(
            id="arch-graphrag-intelligence",
            component_name="Code Intelligence & GraphRAG Engine",
            technology_stack=["Python", "Tree-Sitter", "Vector DB", "Adjacency Index"],
            entrypoints=["intelligence/graph/builder.py", "intelligence/retrieval/retriever.py"],
            conventions=["AST parsing", "Symbol resolution", "Blast radius calculation"],
            description="Analyzes code structures, builds code graph, performs semantic vector retrieval and graph impact analysis.",
            dependencies=[]
        ))

        # Initial ADR Decisions
        self.decisions.add_decision(DecisionRecord(
            id="adr-001-in-memory-knowledge-graph",
            title="ADR-001: Fast In-Memory Knowledge Graph Engine",
            status=DecisionStatus.ACCEPTED,
            date="2026-10-01",
            author="Lead Architect Agent",
            context="The system requires high-frequency blast radius and AST symbol dependency lookups during agent coding loops.",
            decision="Implement an optimized in-memory adjacency list graph store (`KnowledgeGraphStore`) with JSON persistence fallback.",
            consequences=["Sub-millisecond query latency for blast radius calculations", "Low overhead without needing external graph database daemon"],
            alternatives_considered=["Neo4j standalone server", "NetworkX heavy dependency"]
        ))

        self.decisions.add_decision(DecisionRecord(
            id="adr-002-docker-sandbox-isolation",
            title="ADR-002: Docker-Based Isolated Execution Sandbox",
            status=DecisionStatus.ACCEPTED,
            date="2026-10-03",
            author="Security Agent",
            context="Untrusted code execution and shell tool calls must not compromise the host system.",
            decision="Enforce Docker sandbox isolation with strict resource limits (--memory=512m, cpu=1.5) and restricted permissions.",
            consequences=["Protects developer OS from malicious/destructive scripts", "Reproducible testing environment"],
            alternatives_considered=["Direct host process execution", "Chroot jail"]
        ))

        # Initial Task History
        self.tasks.record_task(TaskHistoryRecord(
            id="task-001",
            task_title="Phase 12 Knowledge Graph Integration",
            task_request="Build AST code parser, graph builder, blast radius impact analyzer, and FastAPI graph endpoints.",
            agent_name="Coder Agent",
            status=TaskStatus.COMPLETED,
            files_changed=[
                "intelligence/graph/models.py",
                "intelligence/graph/builder.py",
                "intelligence/graph/storage.py",
                "intelligence/graph/query.py",
                "apps/api/main.py"
            ],
            test_results={"passed": True, "passed_tests": 8, "failed_tests": 0},
            fix_summary="Successfully built sub-millisecond GraphRAG engine with full blast radius estimation."
        ))

        # Initial Developer Preferences & Conventions
        self.preferences.add_or_update_preference(DeveloperPreferenceRecord(
            id="pref-python-style",
            category=PreferenceCategory.CODING_STYLE,
            key="Python Indentation & Linting",
            value="4 spaces per indent level, PEP8 compliance, explicit type annotations",
            description="All Python files in backend and intelligence packages must follow standard PEP8 conventions."
        ))

        self.preferences.add_or_update_preference(DeveloperPreferenceRecord(
            id="pref-testing-framework",
            category=PreferenceCategory.TESTING,
            key="Primary Test Runner",
            value="pytest (Python) / npm test (TypeScript/Web)",
            description="Execute pytest for core backend tests and npm test for web component validation."
        ))

        self.preferences.add_or_update_preference(DeveloperPreferenceRecord(
            id="pref-component-design",
            category=PreferenceCategory.FRAMEWORK,
            key="UI Component Design Aesthetics",
            value="Dark mode glassmorphism, HSL tailwind colors, micro-animations",
            description="Frontend dashboard interfaces must look state-of-the-art and feel responsive with sleek dark themes."
        ))

    def get_overview(self) -> MemoryOverview:
        recent_decs = self.decisions.list_decisions()[:5]
        recent_tsks = self.tasks.list_tasks(limit=5)
        return MemoryOverview(
            total_architecture_components=len(self.architecture.list_all()),
            total_decisions=len(self.decisions.list_decisions()),
            total_tasks_recorded=len(self.tasks.list_tasks()),
            total_preferences=len(self.preferences.list_by_category()),
            recent_decisions=recent_decs,
            recent_tasks=recent_tsks
        )

    def search_all_memory(self, query: str) -> Dict[str, Any]:
        """Cross-memory search across architecture, decisions, tasks, and preferences."""
        return {
            "query": query,
            "architecture": [r.model_dump() for r in self.architecture.search_components(query)],
            "decisions": [r.model_dump() for r in self.decisions.search_decisions(query)],
            "tasks": [r.model_dump() for r in self.tasks.search_tasks(query)],
            "preferences": [r.model_dump() for r in self.preferences.search_preferences(query)]
        }

    def get_llm_context(self, task_description: str = "") -> str:
        """
        Synthesizes formatted project memory context to inject into LLM prompts
        for Planner, Coder, Reviewer, and Security Agents.
        """
        stack = self.architecture.get_stack_summary()
        all_arch = self.architecture.list_all()
        accepted_decisions = self.decisions.list_decisions(status=DecisionStatus.ACCEPTED)
        recent_tasks = self.tasks.list_tasks(limit=3, status=TaskStatus.COMPLETED)
        prefs = self.preferences.list_by_category()

        lines = [
            "### 🧠 Project Memory Context",
            f"**Technologies:** {', '.join(stack['technologies'])}",
            f"**Entrypoints:** {', '.join(stack['entrypoints'])}",
            "",
            "**Key Architecture Components:**"
        ]
        for arch in all_arch[:4]:
            lines.append(f"- **{arch.component_name}**: {arch.description}")

        lines.append("\n**Active Architecture Decisions (ADRs):**")
        for dec in accepted_decisions[:4]:
            lines.append(f"- [{dec.id}] **{dec.title}**: {dec.decision}")

        lines.append("\n**Project Conventions & Developer Preferences:**")
        for pref in prefs[:4]:
            lines.append(f"- **{pref.key}**: {pref.value}")

        if recent_tasks:
            lines.append("\n**Recent Successful Tasks & Fixes:**")
            for tsk in recent_tasks:
                lines.append(f"- Task: '{tsk.task_title}' -> Fix: {tsk.fix_summary or 'Completed'}")

        return "\n".join(lines)
