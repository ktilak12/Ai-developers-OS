from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import time
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
from sandbox.resource_limits.limits import ResourceLimits
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
    journey_description: Optional[str] = None
    target_url: Optional[str] = None
    viewport: Optional[str] = None
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
def search_code_intelligence(query: str = Query(..., min_length=1, max_length=200), limit: int = Query(50, ge=1, le=100), directory_path: Optional[str] = None):
    global GLOBAL_CODE_INDEX
    if "\0" in query:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in search query.")
    target_dir = validate_safe_directory(directory_path) if directory_path else os.getcwd()
    if not GLOBAL_CODE_INDEX or getattr(GLOBAL_CODE_INDEX, "_root_dir", None) != target_dir:
        indexer = CodeIndexer(target_dir)
        GLOBAL_CODE_INDEX = indexer.scan_and_index()
        GLOBAL_CODE_INDEX["_root_dir"] = target_dir
        
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
def query_project_rag(question: str = Query(..., min_length=1, max_length=500), top_k: int = Query(4, ge=1, le=20), directory_path: Optional[str] = None):
    global GLOBAL_RAG_PIPELINE
    if "\0" in question:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in query question.")
    target_dir = validate_safe_directory(directory_path) if directory_path else os.getcwd()
    if not GLOBAL_RAG_PIPELINE or GLOBAL_RAG_PIPELINE.root_dir != target_dir:
        GLOBAL_RAG_PIPELINE = ProjectRAGPipeline(target_dir)
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
    if "\0" in req.task_request:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in task request.")

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
    if not all(isinstance(c, dict) for c in req.changes):
        raise HTTPException(status_code=400, detail="All items in changes must be objects.")

    agent = CoderAgent(target_dir)
    return agent.apply_changes(req.changes)


# --- PHASE 7: DOCKER SANDBOX ENDPOINTS ---

@app.post("/api/sandbox/execute")
def execute_sandbox_command(req: SandboxExecuteRequest):
    """
    Executes command inside isolated Docker container with strict CPU/memory limits & command security policy.
    """
    target_dir = validate_safe_directory(req.directory_path)
    if not req.command or not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty.")
    if len(req.command) > 500:
        raise HTTPException(status_code=400, detail="Command exceeds maximum length of 500 characters.")
    if "\0" in req.command:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in command.")

    timeout_val = max(1, min(req.timeout or 60, 300))
    limits = ResourceLimits(execution_timeout=timeout_val)
    executor = SandboxExecutor(target_dir, limits=limits)
    return executor.execute(req.command)

@app.get("/api/sandbox/status")
def get_sandbox_status(directory_path: Optional[str] = None):
    """
    Returns Docker sandbox health, daemon status, resource limits, and allowed command prefixes.
    """
    target_dir = validate_safe_directory(directory_path)
    executor = SandboxExecutor(target_dir)
    return executor.get_status()


# --- PHASE 8: TESTING AGENT ENDPOINTS ---

@app.post("/api/agents/tester/validate")
def validate_tests_in_sandbox(req: TestValidateRequest):
    """
    Executes automated tests in Docker Sandbox, parses results, and performs AI failure analysis if failed.
    """
    target_dir = validate_safe_directory(req.directory_path)
    cmd = req.command or "npm test"
    if len(cmd) > 500:
        raise HTTPException(status_code=400, detail="Command exceeds maximum length of 500 characters.")
    if "\0" in cmd:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in command.")
    agent = TestingAgent(target_dir)
    return agent.validate_code(cmd)

@app.post("/api/agents/tester/loop")
def run_test_and_fix_loop(req: TestLoopRequest):
    """
    Runs autonomous Coder -> Sandbox -> Tests -> Testing Agent -> Fix loop (bounded by MAX_ITERATIONS = 3).
    """
    target_dir = validate_safe_directory(req.directory_path)
    if not req.task_request or not req.task_request.strip():
        raise HTTPException(status_code=400, detail="Task request cannot be empty.")
    if len(req.task_request) > 2000:
        raise HTTPException(status_code=400, detail="Task request exceeds maximum length of 2000 characters.")
    if "\0" in req.task_request:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in task request.")
    cmd = req.command or "npm test"
    if len(cmd) > 500:
        raise HTTPException(status_code=400, detail="Command exceeds maximum length of 500 characters.")
    if "\0" in cmd:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in command.")
    agent = TestingAgent(target_dir)
    return agent.run_autonomous_loop(req.task_request, cmd)


# --- PHASE 9: SECURITY AGENT ENDPOINTS ---

@app.post("/api/agents/security/scan")
def scan_security_vulnerabilities(req: SecurityScanRequest):
    """
    Performs static security scan, secret detection, and code injection auditing.
    """
    target_dir = validate_safe_directory(req.directory_path)
    if req.changes is not None:
        if not isinstance(req.changes, list):
            raise HTTPException(status_code=400, detail="Changes must be a list.")
        if len(req.changes) > 50:
            raise HTTPException(status_code=400, detail="Changes list exceeds maximum limit of 50 items.")
    if req.file_paths is not None:
        if not isinstance(req.file_paths, list):
            raise HTTPException(status_code=400, detail="File paths must be a list.")
        if len(req.file_paths) > 50:
            raise HTTPException(status_code=400, detail="File paths list exceeds maximum limit of 50 items.")
        for fp in req.file_paths:
            if not isinstance(fp, str) or "\0" in fp:
                raise HTTPException(status_code=400, detail="Invalid path or null bytes prohibited in file paths.")
    agent = SecurityAgent(target_dir)
    if req.changes:
        return agent.scan_changes(req.changes)
    return agent.scan_repository(req.file_paths)

@app.get("/api/agents/security/rules")
def get_security_detection_rules(directory_path: Optional[str] = None):
    """
    Returns active security scanning rules and pattern categories.
    """
    target_dir = validate_safe_directory(directory_path)
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
    target_dir = validate_safe_directory(directory_path)
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
    target_dir = validate_safe_directory(directory_path)
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
    target_dir = validate_safe_directory(req.directory_path)
    if not req.tool_name or not req.tool_name.strip():
        raise HTTPException(status_code=400, detail="Tool name cannot be empty.")
    if len(req.tool_name) > 64:
        raise HTTPException(status_code=400, detail="Tool name exceeds maximum length of 64 characters.")
    if "\0" in req.tool_name:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in tool name.")
    if req.arguments is not None and not isinstance(req.arguments, dict):
        raise HTTPException(status_code=400, detail="Arguments must be an object dictionary.")

    registry = get_mcp_registry(target_dir)
    res = registry.call_tool(req.tool_name, req.arguments or {})
    return res.to_dict()


# --- PHASE 11: BROWSER AGENT ENDPOINTS ---

@app.post("/api/agents/browser/verify")
def verify_browser_journey(req: BrowserVerifyRequest):
    """
    Executes an autonomous end-to-end (E2E) browser verification journey and captures screenshot artifacts.
    """
    target_dir = validate_safe_directory(req.directory_path)
    from urllib.parse import urlparse
    start_url = req.target_url or req.start_url or "http://localhost:3000/login"
    task_name = req.journey_description or req.task_name or "Verify login flow"

    if "\0" in start_url:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in start URL.")
    if len(start_url) > 1000:
        raise HTTPException(status_code=400, detail="Start URL exceeds maximum length of 1000 characters.")
    parsed = urlparse(start_url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(status_code=400, detail=f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.")
    if parsed.hostname in ("169.254.169.254", "metadata.google.internal"):
        raise HTTPException(status_code=400, detail="Access to cloud metadata IP is prohibited.")

    if task_name:
        if "\0" in task_name:
            raise HTTPException(status_code=400, detail="Null bytes are prohibited in task name.")
        if len(task_name) > 200:
            raise HTTPException(status_code=400, detail="Task name exceeds maximum length of 200 characters.")
    if req.steps is not None:
        if not isinstance(req.steps, list):
            raise HTTPException(status_code=400, detail="Steps must be a list.")
        if len(req.steps) > 50:
            raise HTTPException(status_code=400, detail="Steps list exceeds maximum limit of 50 items.")
        if not all(isinstance(s, dict) for s in req.steps):
            raise HTTPException(status_code=400, detail="All items in steps must be objects.")

    agent = BrowserAgent(target_dir)
    res = agent.verify_flow(
        task_name=task_name,
        start_url=start_url,
        steps=req.steps
    )
    # Enrich with frontend dashboard compatibility fields
    passed_count = len([s for s in res.get("executed_steps", []) if s.get("result", {}).get("status") == "success"])
    res["journey_id"] = f"journey-e2e-{int(time.time())}"
    res["target_url"] = start_url
    res["overall_status"] = "passed" if res.get("status") == "PASSED" else "failed"
    res["total_steps"] = res.get("total_steps_executed", 0)
    res["passed_steps"] = passed_count
    res["duration_ms"] = int(res.get("duration_seconds", 0) * 1000)
    res["steps"] = [
        {
            "step_number": s.get("step_number", idx + 1),
            "action": s.get("action", "unknown"),
            "target": s.get("result", {}).get("selector") or s.get("result", {}).get("url") or s.get("description"),
            "value": s.get("result", {}).get("text"),
            "status": "success" if s.get("result", {}).get("status") == "success" else "failed",
            "duration_ms": 150
        }
        for idx, s in enumerate(res.get("executed_steps", []))
    ]
    res["dom_snapshot"] = res.get("dom_summary", {}).get("page_text_preview", "")
    res["console_logs"] = [
        f"[INFO] Initialized headless session for {start_url}",
        f"[{'SUCCESS' if res.get('status') == 'PASSED' else 'ERROR'}] {res.get('observation')}"
    ]
    return res


# --- Phase 12: Code Knowledge Graph & Blast Radius Endpoints ---

GLOBAL_GRAPH_STORE: Optional[KnowledgeGraphStore] = None

def get_graph_store(directory_path: Optional[str] = None) -> KnowledgeGraphStore:
    global GLOBAL_GRAPH_STORE
    target_dir = validate_safe_directory(directory_path) if directory_path else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if not GLOBAL_GRAPH_STORE or getattr(GLOBAL_GRAPH_STORE, "root_dir", None) != target_dir:
        builder = CodeGraphBuilder(root_dir=target_dir)
        graph_data = builder.build_from_directory()
        GLOBAL_GRAPH_STORE = KnowledgeGraphStore(graph_data)
        GLOBAL_GRAPH_STORE.root_dir = target_dir
    return GLOBAL_GRAPH_STORE

class GraphBuildRequest(BaseModel):
    directory_path: Optional[str] = None

class BlastRadiusRequest(BaseModel):
    target_symbol: str
    directory_path: Optional[str] = None

@app.post("/api/intelligence/graph/build")
async def build_code_knowledge_graph(req: GraphBuildRequest = GraphBuildRequest()):
    global GLOBAL_GRAPH_STORE
    target_dir = validate_safe_directory(req.directory_path) if req.directory_path else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    builder = CodeGraphBuilder(root_dir=target_dir)
    graph_data = builder.build_from_directory()
    GLOBAL_GRAPH_STORE = KnowledgeGraphStore(graph_data)
    GLOBAL_GRAPH_STORE.root_dir = target_dir
    
    query_engine = GraphQueryEngine(GLOBAL_GRAPH_STORE)
    return {
        "status": "success",
        "total_nodes": graph_data.total_nodes,
        "total_edges": graph_data.total_edges,
        "density": graph_data.density,
        "entrypoints": query_engine.find_entrypoints(),
        "dead_code_candidates": query_engine.find_dead_code_candidates()[:10],
        "nodes": [n.model_dump() for n in graph_data.nodes[:150]],
        "edges": [e.model_dump() for e in graph_data.edges[:250]]
    }

@app.get("/api/intelligence/graph/overview")
async def get_graph_overview(directory_path: Optional[str] = None):
    store = get_graph_store(directory_path)
    query_engine = GraphQueryEngine(store)
    return {
        "total_nodes": len(store.nodes),
        "total_edges": sum(len(edges) for edges in store.adj.values()),
        "clusters": query_engine.get_architecture_clusters(),
        "entrypoints": query_engine.find_entrypoints(),
        "dead_code_candidates": query_engine.find_dead_code_candidates(),
        "nodes": [n.model_dump() for n in list(store.nodes.values())[:200]],
        "edges": [e.model_dump() for edges in list(store.adj.values()) for e in edges][:300]
    }

@app.post("/api/intelligence/graph/blast-radius")
async def calculate_blast_radius(req: BlastRadiusRequest):
    if not req.target_symbol or not req.target_symbol.strip():
        raise HTTPException(status_code=400, detail="Target symbol cannot be empty.")
    if len(req.target_symbol) > 200:
        raise HTTPException(status_code=400, detail="Target symbol exceeds maximum length of 200 characters.")
    if "\0" in req.target_symbol:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in target symbol.")

    store = get_graph_store(req.directory_path)
    result = store.calculate_blast_radius(req.target_symbol)
    return result.model_dump()

@app.get("/api/intelligence/graph/symbol/{symbol_name}")
async def get_symbol_graph_context(symbol_name: str, directory_path: Optional[str] = None):
    if not symbol_name or not symbol_name.strip():
        raise HTTPException(status_code=400, detail="Symbol name cannot be empty.")
    if len(symbol_name) > 200:
        raise HTTPException(status_code=400, detail="Symbol name exceeds maximum length of 200 characters.")
    if "\0" in symbol_name:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in symbol name.")

    store = get_graph_store(directory_path)
    query_engine = GraphQueryEngine(store)
    context = query_engine.get_symbol_context(symbol_name)
    if "error" in context:
        raise HTTPException(status_code=404, detail=context["error"])
    return context


# --- PHASE 13: PROJECT MEMORY ENDPOINTS ---

GLOBAL_MEMORY_MANAGER: Optional[ProjectMemoryManager] = None

def get_memory_manager(directory_path: Optional[str] = None) -> ProjectMemoryManager:
    global GLOBAL_MEMORY_MANAGER
    target_dir = validate_safe_directory(directory_path) if directory_path else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
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
    if not req.id or not req.id.strip():
        raise HTTPException(status_code=400, detail="ID cannot be empty.")
    if len(req.id) > 200:
        raise HTTPException(status_code=400, detail="ID exceeds maximum length of 200 characters.")
    if "\0" in req.id:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in ID.")

    if not req.component_name or not req.component_name.strip():
        raise HTTPException(status_code=400, detail="Component name cannot be empty.")
    if len(req.component_name) > 200:
        raise HTTPException(status_code=400, detail="Component name exceeds maximum length of 200 characters.")
    if "\0" in req.component_name:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in component name.")

    if not req.description or not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")
    if len(req.description) > 2000:
        raise HTTPException(status_code=400, detail="Description exceeds maximum length of 2000 characters.")
    if "\0" in req.description:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in description.")

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
    if not req.id or not req.id.strip():
        raise HTTPException(status_code=400, detail="ID cannot be empty.")
    if len(req.id) > 200:
        raise HTTPException(status_code=400, detail="ID exceeds maximum length of 200 characters.")
    if "\0" in req.id:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in ID.")

    if not req.title or not req.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    if len(req.title) > 200:
        raise HTTPException(status_code=400, detail="Title exceeds maximum length of 200 characters.")
    if "\0" in req.title:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in title.")

    if not req.context or not req.context.strip():
        raise HTTPException(status_code=400, detail="Context cannot be empty.")
    if len(req.context) > 2000:
        raise HTTPException(status_code=400, detail="Context exceeds maximum length of 2000 characters.")
    if "\0" in req.context:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in context.")

    if not req.decision or not req.decision.strip():
        raise HTTPException(status_code=400, detail="Decision cannot be empty.")
    if len(req.decision) > 2000:
        raise HTTPException(status_code=400, detail="Decision exceeds maximum length of 2000 characters.")
    if "\0" in req.decision:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in decision.")

    if req.author:
        if len(req.author) > 200:
            raise HTTPException(status_code=400, detail="Author exceeds maximum length of 200 characters.")
        if "\0" in req.author:
            raise HTTPException(status_code=400, detail="Null bytes are prohibited in author.")

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
    if not decision_id or not decision_id.strip():
        raise HTTPException(status_code=400, detail="Decision ID cannot be empty.")
    if len(decision_id) > 200:
        raise HTTPException(status_code=400, detail="Decision ID exceeds maximum length of 200 characters.")
    if "\0" in decision_id:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in decision ID.")

    mgr = get_memory_manager(directory_path)
    updated = mgr.decisions.update_status(decision_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Decision record not found")
    mgr.save_to_storage()
    return updated.model_dump()


@app.get("/api/memory/tasks")
async def get_memory_tasks(limit: int = 50, status: Optional[TaskStatus] = None, directory_path: Optional[str] = None):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000.")

    mgr = get_memory_manager(directory_path)
    tasks = mgr.tasks.list_tasks(limit=limit, status=status)
    return {
        "status": "success",
        "total": len(tasks),
        "tasks": [t.model_dump() for t in tasks]
    }


@app.post("/api/memory/tasks")
async def add_memory_task(req: MemoryTaskRequest):
    if not req.id or not req.id.strip():
        raise HTTPException(status_code=400, detail="ID cannot be empty.")
    if len(req.id) > 200:
        raise HTTPException(status_code=400, detail="ID exceeds maximum length of 200 characters.")
    if "\0" in req.id:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in ID.")

    if not req.task_title or not req.task_title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty.")
    if len(req.task_title) > 200:
        raise HTTPException(status_code=400, detail="Task title exceeds maximum length of 200 characters.")
    if "\0" in req.task_title:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in task title.")

    if not req.task_request or not req.task_request.strip():
        raise HTTPException(status_code=400, detail="Task request cannot be empty.")
    if len(req.task_request) > 2000:
        raise HTTPException(status_code=400, detail="Task request exceeds maximum length of 2000 characters.")
    if "\0" in req.task_request:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in task request.")

    if not req.agent_name or not req.agent_name.strip():
        raise HTTPException(status_code=400, detail="Agent name cannot be empty.")
    if len(req.agent_name) > 200:
        raise HTTPException(status_code=400, detail="Agent name exceeds maximum length of 200 characters.")
    if "\0" in req.agent_name:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in agent name.")

    if req.fix_summary:
        if len(req.fix_summary) > 2000:
            raise HTTPException(status_code=400, detail="Fix summary exceeds maximum length of 2000 characters.")
        if "\0" in req.fix_summary:
            raise HTTPException(status_code=400, detail="Null bytes are prohibited in fix summary.")

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
    if not req.id or not req.id.strip():
        raise HTTPException(status_code=400, detail="ID cannot be empty.")
    if len(req.id) > 200:
        raise HTTPException(status_code=400, detail="ID exceeds maximum length of 200 characters.")
    if "\0" in req.id:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in ID.")

    if not req.key or not req.key.strip():
        raise HTTPException(status_code=400, detail="Key cannot be empty.")
    if len(req.key) > 200:
        raise HTTPException(status_code=400, detail="Key exceeds maximum length of 200 characters.")
    if "\0" in req.key:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in key.")

    if not req.value or not req.value.strip():
        raise HTTPException(status_code=400, detail="Value cannot be empty.")
    if len(req.value) > 1000:
        raise HTTPException(status_code=400, detail="Value exceeds maximum length of 1000 characters.")
    if "\0" in req.value:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in value.")

    if not req.description or not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")
    if len(req.description) > 2000:
        raise HTTPException(status_code=400, detail="Description exceeds maximum length of 2000 characters.")
    if "\0" in req.description:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in description.")

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
    if len(query) > 500:
        raise HTTPException(status_code=400, detail="Query exceeds maximum length of 500 characters.")
    if "\0" in query:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in search query.")

    mgr = get_memory_manager(directory_path)
    return mgr.search_all_memory(query)


@app.get("/api/memory/context")
async def get_memory_context(task_description: str = "", directory_path: Optional[str] = None):
    if len(task_description) > 2000:
        raise HTTPException(status_code=400, detail="Task description exceeds maximum length of 2000 characters.")
    if "\0" in task_description:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in task description.")

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
    target_dir = validate_safe_directory(directory_path) if directory_path else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
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
    if not req.task_request or not req.task_request.strip():
        raise HTTPException(status_code=400, detail="Task request cannot be empty.")
    if len(req.task_request) > 2000:
        raise HTTPException(status_code=400, detail="Task request exceeds maximum length of 2000 characters.")
    if "\0" in req.task_request:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in task request.")
    if req.test_command:
        if len(req.test_command) > 500:
            raise HTTPException(status_code=400, detail="Test command exceeds maximum length of 500 characters.")
        if "\0" in req.test_command:
            raise HTTPException(status_code=400, detail="Null bytes are prohibited in test command.")

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
    if not workflow_id or not workflow_id.strip() or len(workflow_id) > 100 or "\0" in workflow_id:
        raise HTTPException(status_code=400, detail="Invalid workflow ID.")
    orch = get_orchestrator(directory_path)
    state = orch.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return state.model_dump()


@app.post("/api/orchestrator/approve")
async def handle_orchestrator_approval(req: OrchestratorApproveRequest):
    """Processes human developer sign-off at the approval gate."""
    if not req.workflow_id or not req.workflow_id.strip():
        raise HTTPException(status_code=400, detail="Workflow ID cannot be empty.")
    if len(req.workflow_id) > 100:
        raise HTTPException(status_code=400, detail="Workflow ID exceeds maximum length of 100 characters.")
    if "\0" in req.workflow_id:
        raise HTTPException(status_code=400, detail="Null bytes are prohibited in workflow ID.")
    if req.notes:
        if len(req.notes) > 1000:
            raise HTTPException(status_code=400, detail="Notes exceeds maximum length of 1000 characters.")
        if "\0" in req.notes:
            raise HTTPException(status_code=400, detail="Null bytes are prohibited in notes.")

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
    root = validate_safe_directory(directory_path) if directory_path else os.getcwd()
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
    if not trace_id or not trace_id.strip() or len(trace_id) > 100 or "\0" in trace_id:
        raise HTTPException(status_code=400, detail="Invalid trace ID.")
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
    root = validate_safe_directory(directory_path) if directory_path else os.getcwd()
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
    if not task_id or not task_id.strip() or len(task_id) > 64 or "\0" in task_id:
        raise HTTPException(status_code=400, detail="Invalid task ID.")
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
    if req.task_ids is not None:
        if not isinstance(req.task_ids, list):
            raise HTTPException(status_code=400, detail="Task IDs must be a list.")
        if len(req.task_ids) > 50:
            raise HTTPException(status_code=400, detail="Task IDs list exceeds maximum limit of 50 items.")
        for tid in req.task_ids:
            if not isinstance(tid, str) or "\0" in tid or len(tid) > 64:
                raise HTTPException(status_code=400, detail="Invalid task ID format.")

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









