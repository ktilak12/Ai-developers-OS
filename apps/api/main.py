from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from typing import Optional, List, Dict, Any

from intelligence.indexing.code_indexer import CodeIndexer
from intelligence.retrieval.symbol_search import SymbolSearchEngine
from intelligence.retrieval.retriever import ProjectRAGPipeline
from agents.planner.agent import PlannerAgent
from agents.coder.agent import CoderAgent
from agents.tester.agent import TestingAgent
from agents.security.agent import SecurityAgent
from agents.browser.agent import BrowserAgent
from sandbox.runner.executor import SandboxExecutor
from mcp.registry import get_mcp_registry
from intelligence.graph.builder import CodeGraphBuilder
from intelligence.graph.storage import KnowledgeGraphStore
from intelligence.graph.query import GraphQueryEngine
from memory.manager import ProjectMemoryManager
from memory.models import (
    ArchitectureRecord, DecisionRecord, TaskHistoryRecord,
    DeveloperPreferenceRecord, DecisionStatus, TaskStatus, PreferenceCategory
)
from orchestrator import MultiAgentOrchestrator, OrchestratorState, WorkflowStatus, ApprovalState
from observability.manager import ObservabilityManager
from evaluation.evaluator import SWEEvaluator
from evaluation.dataset import get_all_benchmark_tasks, get_benchmark_task_by_id
from evaluation.report import BenchmarkReportGenerator






from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI(title="AI Developer OS API", version="0.1.0")

# Security: Define explicit allowed origins rather than insecure wildcard with credentials
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security: Add HTTP response security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

GITHUB_API_BASE = "https://api.github.com"

# Global in-memory stores
GLOBAL_CODE_INDEX: Dict[str, Any] = {}
GLOBAL_RAG_PIPELINE: Optional[ProjectRAGPipeline] = None

class IndexRequest(BaseModel):
    directory_path: Optional[str] = None

class PlanRequest(BaseModel):
    task_request: str
    directory_path: Optional[str] = None

class ModifyRequest(BaseModel):
    plan: Dict[str, Any]
    directory_path: Optional[str] = None

class ApplyRequest(BaseModel):
    changes: List[Dict[str, Any]]
    directory_path: Optional[str] = None

class SandboxExecuteRequest(BaseModel):
    command: str
    directory_path: Optional[str] = None
    timeout: Optional[int] = 60

class TestValidateRequest(BaseModel):
    command: Optional[str] = "npm test"
    directory_path: Optional[str] = None

class TestLoopRequest(BaseModel):
    task_request: str
    command: Optional[str] = "npm test"
    directory_path: Optional[str] = None

class SecurityScanRequest(BaseModel):
    changes: Optional[List[Dict[str, Any]]] = None
    file_paths: Optional[List[str]] = None
    directory_path: Optional[str] = None

class MCPCallRequest(BaseModel):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = None
    directory_path: Optional[str] = None

class BrowserVerifyRequest(BaseModel):
    task_name: Optional[str] = "Verify login flow"
    start_url: Optional[str] = "http://localhost:3000/login"
    steps: Optional[List[Dict[str, Any]]] = None
    directory_path: Optional[str] = None






import re

GITHUB_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+$")

def validate_github_params(owner: str, repo: str, path: Optional[str] = None):
    """Security validator for GitHub parameters to prevent SSRF, path traversal, and injection attacks."""
    if not owner or not GITHUB_IDENTIFIER_REGEX.match(owner) or len(owner) > 100:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository owner parameter.")
    if not repo or not GITHUB_IDENTIFIER_REGEX.match(repo) or len(repo) > 100:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository name parameter.")
    if path:
        if ".." in path or path.startswith("/") or "\0" in path:
            raise HTTPException(status_code=400, detail="Path traversal characters are prohibited in repository path.")

def sanitize_github_error_detail(text: str) -> str:
    """Masks authorization tokens, PATs, and credentials from error responses."""
    sanitized = re.sub(r"(Bearer\s+)[a-zA-Z0-9_\-\.]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    sanitized = re.sub(r"(ghp_[a-zA-Z0-9]{30,}|github_pat_[a-zA-Z0-9_]{30,})", "[REDACTED_TOKEN]", sanitized)
    return sanitized

async def make_github_request(endpoint: str, token: Optional[str] = None):
    # Security: Ensure endpoint strictly stays within GitHub API namespace
    clean_endpoint = endpoint.lstrip("/")
    if "://" in clean_endpoint or clean_endpoint.startswith("//") or ".." in clean_endpoint:
        raise HTTPException(status_code=400, detail="Invalid API endpoint specified.")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Developer-OS/0.1.0"
    }
    
    auth_token = token or os.getenv("GITHUB_TOKEN")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    url = f"{GITHUB_API_BASE}/{clean_endpoint}"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            safe_detail = sanitize_github_error_detail(res.text)
            raise HTTPException(
                status_code=res.status_code, 
                detail=f"GitHub API Error ({res.status_code}): {safe_detail}"
            )
        return res.json()

@app.get("/")
def read_root():
    return {"status": "ok", "service": "AI Developer OS Backend API"}

# --- GITHUB INTEGRATION ENDPOINTS (PHASE 1 / 2) ---

@app.get("/api/github/repo")
async def get_repository_info(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    validate_github_params(owner, repo)
    return await make_github_request(f"repos/{owner}/{repo}", token)

@app.get("/api/github/branches")
async def get_branches(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    validate_github_params(owner, repo)
    return await make_github_request(f"repos/{owner}/{repo}/branches", token)

@app.get("/api/github/issues")
async def get_issues(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    validate_github_params(owner, repo)
    return await make_github_request(f"repos/{owner}/{repo}/issues", token)

@app.get("/api/github/commits")
async def get_commits(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    validate_github_params(owner, repo)
    return await make_github_request(f"repos/{owner}/{repo}/commits", token)

@app.get("/api/github/pulls")
async def get_pull_requests(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    validate_github_params(owner, repo)
    return await make_github_request(f"repos/{owner}/{repo}/pulls", token)

@app.get("/api/github/contents")
async def get_repository_contents(owner: str = Query(...), repo: str = Query(...), path: str = Query(""), token: Optional[str] = None):
    validate_github_params(owner, repo, path)
    endpoint = f"repos/{owner}/{repo}/contents/{path}" if path else f"repos/{owner}/{repo}/contents"
    return await make_github_request(endpoint, token)

def validate_safe_directory(path: Optional[str]) -> str:
    """Security validator for workspace and repository directory paths."""
    target_dir = path or os.getcwd()
    if "\0" in target_dir:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in directory paths.")
    try:
        real_path = os.path.realpath(os.path.abspath(target_dir))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid directory path specified.")

    if not os.path.exists(real_path) or not os.path.isdir(real_path):
        raise HTTPException(status_code=400, detail=f"Directory '{target_dir}' does not exist or is not a directory.")
    
    return real_path

# --- PHASE 3: CODE INTELLIGENCE ENDPOINTS ---

@app.post("/api/intelligence/index")
def index_repository(req: IndexRequest):
    global GLOBAL_CODE_INDEX
    target_dir = validate_safe_directory(req.directory_path)
    
    indexer = CodeIndexer(target_dir)
    GLOBAL_CODE_INDEX = indexer.scan_and_index()
    return {
        "status": "success",
        "message": f"Successfully indexed {GLOBAL_CODE_INDEX['files_scanned']} files.",
        "summary": {
            "files_scanned": GLOBAL_CODE_INDEX["files_scanned"],
            "functions_count": len(GLOBAL_CODE_INDEX["functions"]),
            "classes_count": len(GLOBAL_CODE_INDEX["classes"]),
            "components_count": len(GLOBAL_CODE_INDEX["components"]),
            "routes_count": len(GLOBAL_CODE_INDEX["routes"]),
        }
    }

@app.get("/api/intelligence/search")
def search_code_intelligence(query: str = Query(..., min_length=1, max_length=200), limit: int = Query(50, ge=1, le=100)):
    global GLOBAL_CODE_INDEX
    if not GLOBAL_CODE_INDEX:
        indexer = CodeIndexer(os.getcwd())
        GLOBAL_CODE_INDEX = indexer.scan_and_index()
        
    engine = SymbolSearchEngine(GLOBAL_CODE_INDEX)
    return engine.search(query, max_results=limit)

# --- PHASE 4: PROJECT RAG ENDPOINTS ---

@app.post("/api/rag/index")
def index_project_rag(req: IndexRequest):
    global GLOBAL_RAG_PIPELINE
    target_dir = validate_safe_directory(req.directory_path)
    GLOBAL_RAG_PIPELINE = ProjectRAGPipeline(target_dir)
    total_chunks = GLOBAL_RAG_PIPELINE.build_index()
    return {
        "status": "success",
        "message": f"Successfully chunked and indexed {total_chunks} code windows into VectorStore."
    }

@app.get("/api/rag/query")
def query_project_rag(question: str = Query(..., min_length=1, max_length=500), top_k: int = Query(4, ge=1, le=20)):
    global GLOBAL_RAG_PIPELINE
    if not GLOBAL_RAG_PIPELINE:
        GLOBAL_RAG_PIPELINE = ProjectRAGPipeline(os.getcwd())
        GLOBAL_RAG_PIPELINE.build_index()
        
    return GLOBAL_RAG_PIPELINE.query(question, top_k=top_k)

# --- PHASE 5: PLANNER AGENT ENDPOINTS ---

@app.post("/api/agents/planner/plan")
def create_planner_plan(req: PlanRequest):
    """
    Generate structured implementation plan using RAG context retrieval and AST code intelligence.
    Returns: goal, requirements, affected_files_detailed, structured_steps, risk_matrix, testing_requirements, and retrieved_context_summary.
    """
    target_dir = validate_safe_directory(req.directory_path)
    if not req.task_request or not req.task_request.strip():
        raise HTTPException(status_code=400, detail="task_request cannot be empty.")
    if len(req.task_request) > 5000:
        raise HTTPException(status_code=400, detail="task_request exceeds maximum allowed length of 5000 characters.")

    agent = PlannerAgent(target_dir)
    return agent.generate_plan(req.task_request)


# --- PHASE 6: CODE AGENT ENDPOINTS ---

@app.post("/api/agents/coder/modify")
def execute_code_modification(req: ModifyRequest):
    """
    Executes controlled code modification based on approved implementation plan and generates unified git diffs.
    """
    target_dir = validate_safe_directory(req.directory_path)
    if not isinstance(req.plan, dict) or not req.plan:
        raise HTTPException(status_code=400, detail="Plan must be a non-empty object.")

    agent = CoderAgent(target_dir)
    return agent.execute_modification(req.plan)

@app.post("/api/agents/coder/apply")
def apply_code_modification(req: ApplyRequest):
    """
    Applies developer-approved code changes and unified diffs directly to the workspace files.
    """
    target_dir = validate_safe_directory(req.directory_path)
    if not req.changes or not isinstance(req.changes, list):
        raise HTTPException(status_code=400, detail="Changes must be a non-empty list.")
    if len(req.changes) > 20:
        raise HTTPException(status_code=400, detail="Changes list exceeds maximum limit of 20 items.")

    agent = CoderAgent(target_dir)
    return agent.apply_changes(req.changes)


# --- PHASE 7: DOCKER SANDBOX ENDPOINTS ---

@app.post("/api/sandbox/execute")
def execute_sandbox_command(req: SandboxExecuteRequest):
    """
    Executes command inside isolated Docker container with strict CPU/memory limits & command security policy.
    """
    target_dir = req.directory_path or os.getcwd()
    executor = SandboxExecutor(target_dir)
    return executor.execute(req.command)

@app.get("/api/sandbox/status")
def get_sandbox_status(directory_path: Optional[str] = None):
    """
    Returns Docker sandbox health, daemon status, resource limits, and allowed command prefixes.
    """
    target_dir = directory_path or os.getcwd()
    executor = SandboxExecutor(target_dir)
    return executor.get_status()


# --- PHASE 8: TESTING AGENT ENDPOINTS ---

@app.post("/api/agents/tester/validate")
def validate_tests_in_sandbox(req: TestValidateRequest):
    """
    Executes automated tests in Docker Sandbox, parses results, and performs AI failure analysis if failed.
    """
    target_dir = req.directory_path or os.getcwd()
    agent = TestingAgent(target_dir)
    return agent.validate_code(req.command or "npm test")

@app.post("/api/agents/tester/loop")
def run_test_and_fix_loop(req: TestLoopRequest):
    """
    Runs autonomous Coder -> Sandbox -> Tests -> Testing Agent -> Fix loop (bounded by MAX_ITERATIONS = 3).
    """
    target_dir = req.directory_path or os.getcwd()
    agent = TestingAgent(target_dir)
    return agent.run_autonomous_loop(req.task_request, req.command or "npm test")


# --- PHASE 9: SECURITY AGENT ENDPOINTS ---

@app.post("/api/agents/security/scan")
def scan_security_vulnerabilities(req: SecurityScanRequest):
    """
    Performs static security scan, secret detection, and code injection auditing.
    """
    target_dir = req.directory_path or os.getcwd()
    agent = SecurityAgent(target_dir)
    if req.changes:
        return agent.scan_changes(req.changes)
    return agent.scan_repository(req.file_paths)

@app.get("/api/agents/security/rules")
def get_security_detection_rules(directory_path: Optional[str] = None):
    """
    Returns active security scanning rules and pattern categories.
    """
    target_dir = directory_path or os.getcwd()
    agent = SecurityAgent(target_dir)
    return {
        "secret_patterns_count": len(agent.tools.SECRET_PATTERNS),
        "dangerous_patterns_count": len(agent.tools.DANGEROUS_CODE_PATTERNS),
        "sqli_patterns_count": len(agent.tools.SQL_INJECTION_PATTERNS),
        "insecure_config_count": len(agent.tools.INSECURE_CONFIG_PATTERNS),
        "policy": "ZERO_TOLERANCE_FOR_CRITICAL_HIGH"
    }


# --- PHASE 10: MCP INTEGRATION ENDPOINTS ---

@app.get("/api/mcp/tools")
def list_mcp_tools(directory_path: Optional[str] = None):
    """
    Returns all registered Model Context Protocol (MCP) tools and input schemas.
    """
    target_dir = directory_path or os.getcwd()
    registry = get_mcp_registry(target_dir)
    return {
        "status": "success",
        "tools_count": len(registry.tools),
        "tools": registry.list_tools()
    }

@app.get("/api/mcp/servers")
def list_mcp_servers(directory_path: Optional[str] = None):
    """
    Returns all active MCP servers and registered tool counts.
    """
    target_dir = directory_path or os.getcwd()
    registry = get_mcp_registry(target_dir)
    return {
        "status": "success",
        "servers": registry.list_servers()
    }

@app.post("/api/mcp/call")
def call_mcp_tool(req: MCPCallRequest):
    """
    Invokes an MCP tool using standard JSON-RPC envelope arguments.
    """
    target_dir = req.directory_path or os.getcwd()
    registry = get_mcp_registry(target_dir)
    res = registry.call_tool(req.tool_name, req.arguments or {})
    return res.to_dict()


# --- PHASE 11: BROWSER AGENT ENDPOINTS ---

@app.post("/api/agents/browser/verify")
def verify_browser_journey(req: BrowserVerifyRequest):
    """
    Executes an autonomous end-to-end (E2E) browser verification journey and captures screenshot artifacts.
    """
    target_dir = req.directory_path or os.getcwd()
    agent = BrowserAgent(target_dir)
    return agent.verify_flow(
        task_name=req.task_name or "Verify login flow",
        start_url=req.start_url or "http://localhost:3000/login",
        steps=req.steps
    )


# --- Phase 12: Code Knowledge Graph & Blast Radius Endpoints ---

GLOBAL_GRAPH_STORE: Optional[KnowledgeGraphStore] = None

class GraphBuildRequest(BaseModel):
    directory_path: Optional[str] = None

class BlastRadiusRequest(BaseModel):
    target_symbol: str

@app.post("/api/intelligence/graph/build")
async def build_code_knowledge_graph(req: GraphBuildRequest = GraphBuildRequest()):
    global GLOBAL_GRAPH_STORE
    target_dir = req.directory_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    builder = CodeGraphBuilder(root_dir=target_dir)
    graph_data = builder.build_from_directory()
    GLOBAL_GRAPH_STORE = KnowledgeGraphStore(graph_data)
    
    query_engine = GraphQueryEngine(GLOBAL_GRAPH_STORE)
    return {
        "status": "success",
        "total_nodes": graph_data.total_nodes,
        "total_edges": graph_data.total_edges,
        "density": graph_data.density,
        "entrypoints": query_engine.find_entrypoints(),
        "dead_code_candidates": query_engine.find_dead_code_candidates()[:10],
        "nodes": [n.dict() for n in graph_data.nodes[:150]],
        "edges": [e.dict() for e in graph_data.edges[:250]]
    }

@app.get("/api/intelligence/graph/overview")
async def get_graph_overview():
    global GLOBAL_GRAPH_STORE
    if not GLOBAL_GRAPH_STORE:
        # Build lazily if not yet initialized
        target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        builder = CodeGraphBuilder(root_dir=target_dir)
        graph_data = builder.build_from_directory()
        GLOBAL_GRAPH_STORE = KnowledgeGraphStore(graph_data)
        
    query_engine = GraphQueryEngine(GLOBAL_GRAPH_STORE)
    return {
        "total_nodes": len(GLOBAL_GRAPH_STORE.nodes),
        "total_edges": sum(len(edges) for edges in GLOBAL_GRAPH_STORE.adj.values()),
        "clusters": query_engine.get_architecture_clusters(),
        "entrypoints": query_engine.find_entrypoints(),
        "dead_code_candidates": query_engine.find_dead_code_candidates(),
        "nodes": [n.dict() for n in list(GLOBAL_GRAPH_STORE.nodes.values())[:200]],
        "edges": [e.dict() for edges in list(GLOBAL_GRAPH_STORE.adj.values()) for e in edges][:300]
    }

@app.post("/api/intelligence/graph/blast-radius")
async def calculate_blast_radius(req: BlastRadiusRequest):
    global GLOBAL_GRAPH_STORE
    if not GLOBAL_GRAPH_STORE:
        target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        builder = CodeGraphBuilder(root_dir=target_dir)
        graph_data = builder.build_from_directory()
        GLOBAL_GRAPH_STORE = KnowledgeGraphStore(graph_data)
        
    result = GLOBAL_GRAPH_STORE.calculate_blast_radius(req.target_symbol)
    return result.dict()

@app.get("/api/intelligence/graph/symbol/{symbol_name}")
async def get_symbol_graph_context(symbol_name: str):
    global GLOBAL_GRAPH_STORE
    if not GLOBAL_GRAPH_STORE:
        target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        builder = CodeGraphBuilder(root_dir=target_dir)
        graph_data = builder.build_from_directory()
        GLOBAL_GRAPH_STORE = KnowledgeGraphStore(graph_data)
        
    query_engine = GraphQueryEngine(GLOBAL_GRAPH_STORE)
    context = query_engine.get_symbol_context(symbol_name)
    return context


# --- PHASE 13: PROJECT MEMORY ENDPOINTS ---

GLOBAL_MEMORY_MANAGER: Optional[ProjectMemoryManager] = None

def get_memory_manager(directory_path: Optional[str] = None) -> ProjectMemoryManager:
    global GLOBAL_MEMORY_MANAGER
    target_dir = directory_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if not GLOBAL_MEMORY_MANAGER or GLOBAL_MEMORY_MANAGER.root_dir != target_dir:
        GLOBAL_MEMORY_MANAGER = ProjectMemoryManager(root_dir=target_dir)
    return GLOBAL_MEMORY_MANAGER

class MemoryArchitectureRequest(BaseModel):
    id: str
    component_name: str
    technology_stack: List[str] = []
    entrypoints: List[str] = []
    conventions: List[str] = []
    description: str
    dependencies: List[str] = []
    directory_path: Optional[str] = None

class MemoryDecisionRequest(BaseModel):
    id: str
    title: str
    status: DecisionStatus = DecisionStatus.ACCEPTED
    author: Optional[str] = "AI Developer OS"
    context: str
    decision: str
    consequences: List[str] = []
    alternatives_considered: List[str] = []
    directory_path: Optional[str] = None

class MemoryTaskRequest(BaseModel):
    id: str
    task_title: str
    task_request: str
    agent_name: str
    status: TaskStatus = TaskStatus.COMPLETED
    files_changed: List[str] = []
    test_results: Optional[Dict[str, Any]] = None
    fix_summary: Optional[str] = None
    directory_path: Optional[str] = None

class MemoryPreferenceRequest(BaseModel):
    id: str
    category: PreferenceCategory
    key: str
    value: str
    description: str
    directory_path: Optional[str] = None


@app.get("/api/memory/overview")
async def get_memory_overview(directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    return mgr.get_overview().model_dump()


@app.get("/api/memory/architecture")
async def get_memory_architecture(directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    return {
        "status": "success",
        "stack_summary": mgr.architecture.get_stack_summary(),
        "components": [c.model_dump() for c in mgr.architecture.list_all()]
    }


@app.post("/api/memory/architecture")
async def add_memory_architecture(req: MemoryArchitectureRequest):
    mgr = get_memory_manager(req.directory_path)
    record = ArchitectureRecord(
        id=req.id,
        component_name=req.component_name,
        technology_stack=req.technology_stack,
        entrypoints=req.entrypoints,
        conventions=req.conventions,
        description=req.description,
        dependencies=req.dependencies
    )
    saved = mgr.architecture.add_or_update(record)
    mgr.save_to_storage()
    return saved.model_dump()


@app.get("/api/memory/decisions")
async def get_memory_decisions(status: Optional[DecisionStatus] = None, directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    decs = mgr.decisions.list_decisions(status=status)
    return {
        "status": "success",
        "total": len(decs),
        "decisions": [d.model_dump() for d in decs]
    }


@app.post("/api/memory/decisions")
async def add_memory_decision(req: MemoryDecisionRequest):
    mgr = get_memory_manager(req.directory_path)
    record = DecisionRecord(
        id=req.id,
        title=req.title,
        status=req.status,
        author=req.author or "AI Developer OS",
        context=req.context,
        decision=req.decision,
        consequences=req.consequences,
        alternatives_considered=req.alternatives_considered
    )
    saved = mgr.decisions.add_decision(record)
    mgr.save_to_storage()
    return saved.model_dump()


@app.put("/api/memory/decisions/{decision_id}/status")
async def update_decision_status(decision_id: str, status: DecisionStatus, directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    updated = mgr.decisions.update_status(decision_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Decision record not found")
    mgr.save_to_storage()
    return updated.model_dump()


@app.get("/api/memory/tasks")
async def get_memory_tasks(limit: int = 50, status: Optional[TaskStatus] = None, directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    tasks = mgr.tasks.list_tasks(limit=limit, status=status)
    return {
        "status": "success",
        "total": len(tasks),
        "tasks": [t.model_dump() for t in tasks]
    }


@app.post("/api/memory/tasks")
async def add_memory_task(req: MemoryTaskRequest):
    mgr = get_memory_manager(req.directory_path)
    record = TaskHistoryRecord(
        id=req.id,
        task_title=req.task_title,
        task_request=req.task_request,
        agent_name=req.agent_name,
        status=req.status,
        files_changed=req.files_changed,
        test_results=req.test_results,
        fix_summary=req.fix_summary
    )
    saved = mgr.tasks.record_task(record)
    mgr.save_to_storage()
    return saved.model_dump()


@app.get("/api/memory/preferences")
async def get_memory_preferences(category: Optional[PreferenceCategory] = None, directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    prefs = mgr.preferences.list_by_category(category=category)
    return {
        "status": "success",
        "total": len(prefs),
        "preferences": [p.model_dump() for p in prefs]
    }


@app.post("/api/memory/preferences")
async def add_memory_preference(req: MemoryPreferenceRequest):
    mgr = get_memory_manager(req.directory_path)
    record = DeveloperPreferenceRecord(
        id=req.id,
        category=req.category,
        key=req.key,
        value=req.value,
        description=req.description
    )
    saved = mgr.preferences.add_or_update_preference(record)
    mgr.save_to_storage()
    return saved.model_dump()


@app.get("/api/memory/search")
async def search_memory(query: str = Query(..., min_length=1), directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    return mgr.search_all_memory(query)


@app.get("/api/memory/context")
async def get_memory_context(task_description: str = "", directory_path: Optional[str] = None):
    mgr = get_memory_manager(directory_path)
    return {
        "status": "success",
        "task_description": task_description,
        "context": mgr.get_llm_context(task_description)
    }


# --- PHASE 14: MULTI-AGENT ORCHESTRATION ENDPOINTS ---

GLOBAL_ORCHESTRATOR: Optional[MultiAgentOrchestrator] = None

def get_orchestrator(directory_path: Optional[str] = None) -> MultiAgentOrchestrator:
    global GLOBAL_ORCHESTRATOR
    target_dir = directory_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if not GLOBAL_ORCHESTRATOR or GLOBAL_ORCHESTRATOR.root_dir != target_dir:
        GLOBAL_ORCHESTRATOR = MultiAgentOrchestrator(root_dir=target_dir)
    return GLOBAL_ORCHESTRATOR

class OrchestratorRunRequest(BaseModel):
    task_request: str
    auto_approve: Optional[bool] = False
    test_command: Optional[str] = None
    directory_path: Optional[str] = None

class OrchestratorApproveRequest(BaseModel):
    workflow_id: str
    approve: bool
    notes: Optional[str] = None
    directory_path: Optional[str] = None


@app.post("/api/orchestrator/run")
async def run_multi_agent_workflow(req: OrchestratorRunRequest):
    """
    Executes the autonomous multi-agent pipeline:
    Planner -> Researcher -> Coder -> Sandbox/Tester -> Security -> Reviewer -> Human Approval Gate -> GitHub PR.
    """
    orch = get_orchestrator(req.directory_path)
    state = orch.execute_workflow(
        task_request=req.task_request,
        auto_approve=req.auto_approve or False,
        test_command=req.test_command
    )
    return state.model_dump()


@app.get("/api/orchestrator/state/{workflow_id}")
async def get_orchestrator_state(workflow_id: str, directory_path: Optional[str] = None):
    """Returns the current state and telemetry of a running or completed workflow."""
    orch = get_orchestrator(directory_path)
    state = orch.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return state.model_dump()


@app.post("/api/orchestrator/approve")
async def handle_orchestrator_approval(req: OrchestratorApproveRequest):
    """Processes human developer sign-off at the approval gate."""
    orch = get_orchestrator(req.directory_path)
    try:
        updated = orch.handle_human_decision(
            workflow_id=req.workflow_id,
            approve=req.approve,
            notes=req.notes
        )
        return updated.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/orchestrator/history")
async def get_orchestrator_history(directory_path: Optional[str] = None):
    """Lists recent workflow executions, traces, and metrics."""
    orch = get_orchestrator(directory_path)
    workflows = orch.list_workflows()
    return {
        "status": "success",
        "total": len(workflows),
        "workflows": [w.model_dump() for w in workflows]
    }


# =====================================================================
# PHASE 15: OBSERVABILITY & AGENT TRACING
# =====================================================================

GLOBAL_OBSERVABILITY_MGR: Optional[ObservabilityManager] = None

def get_observability_manager(directory_path: Optional[str] = None) -> ObservabilityManager:
    global GLOBAL_OBSERVABILITY_MGR
    root = directory_path or os.getcwd()
    if GLOBAL_OBSERVABILITY_MGR is None or GLOBAL_OBSERVABILITY_MGR.root_dir != root:
        GLOBAL_OBSERVABILITY_MGR = ObservabilityManager(root)
    return GLOBAL_OBSERVABILITY_MGR


@app.get("/api/observability/metrics")
async def get_observability_metrics(directory_path: Optional[str] = None):
    """Returns aggregated OpenTelemetry metrics, tool execution latency, and token costs."""
    mgr = get_observability_manager(directory_path)
    metrics = mgr.get_metrics()
    return metrics.model_dump()


@app.get("/api/observability/traces")
async def list_observability_traces(directory_path: Optional[str] = None):
    """Returns all recorded multi-agent workflow traces."""
    mgr = get_observability_manager(directory_path)
    traces = mgr.list_traces()
    return {
        "status": "success",
        "total": len(traces),
        "traces": [t.model_dump() for t in traces]
    }


@app.get("/api/observability/traces/{trace_id}")
async def get_observability_trace_detail(trace_id: str, directory_path: Optional[str] = None):
    """Returns granular spans and tool calls for a specific agent trace."""
    mgr = get_observability_manager(directory_path)
    trace = mgr.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found.")
    return trace.model_dump()


# =====================================================================
# PHASE 16: EVALUATION & BENCHMARKS
# =====================================================================

GLOBAL_EVALUATOR: Optional[SWEEvaluator] = None

def get_evaluator(directory_path: Optional[str] = None) -> SWEEvaluator:
    global GLOBAL_EVALUATOR
    root = directory_path or os.getcwd()
    if GLOBAL_EVALUATOR is None or GLOBAL_EVALUATOR.root_dir != root:
        GLOBAL_EVALUATOR = SWEEvaluator(root)
    return GLOBAL_EVALUATOR


class BenchmarkRunRequest(BaseModel):
    task_ids: Optional[List[str]] = None
    directory_path: Optional[str] = None


@app.get("/api/evaluation/benchmark/tasks")
async def get_benchmark_tasks():
    """Returns the 20 SWE Benchmark Tasks dataset."""
    tasks = get_all_benchmark_tasks()
    return {
        "status": "success",
        "total": len(tasks),
        "tasks": [t.model_dump() for t in tasks]
    }


@app.get("/api/evaluation/benchmark/tasks/{task_id}")
async def get_benchmark_task_detail(task_id: str):
    """Returns details for a specific benchmark task."""
    task = get_benchmark_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Benchmark task not found.")
    return task.model_dump()


@app.get("/api/evaluation/benchmark/scorecard")
async def get_benchmark_scorecard(directory_path: Optional[str] = None):
    """Returns the latest comparative scorecard (Agent v1 vs Agent v2)."""
    evaluator = get_evaluator(directory_path)
    scorecard = evaluator.get_latest_scorecard()
    if not scorecard:
        scorecard = evaluator.run_benchmark()
    return scorecard.model_dump()


@app.post("/api/evaluation/benchmark/run")
async def run_benchmark_evaluation(req: BenchmarkRunRequest):
    """Executes SWE benchmark suite comparing Agent v1 vs Agent v2."""
    evaluator = get_evaluator(req.directory_path)
    scorecard = evaluator.run_benchmark(task_ids=req.task_ids)
    return scorecard.model_dump()


@app.get("/api/evaluation/benchmark/report")
async def get_benchmark_report_markdown(directory_path: Optional[str] = None):
    """Returns a formatted Markdown benchmark report for display and export."""
    evaluator = get_evaluator(directory_path)
    scorecard = evaluator.get_latest_scorecard()
    if not scorecard:
        scorecard = evaluator.run_benchmark()
    markdown = BenchmarkReportGenerator.generate_markdown_report(scorecard)
    return {
        "evaluation_id": scorecard.evaluation_id,
        "markdown": markdown
    }









