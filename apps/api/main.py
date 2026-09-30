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

app = FastAPI(title="AI Developer OS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

async def make_github_request(endpoint: str, token: Optional[str] = None):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Developer-OS/0.1.0"
    }
    
    auth_token = token or os.getenv("GITHUB_TOKEN")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code, 
                detail=f"GitHub API Error ({res.status_code}): {res.text}"
            )
        return res.json()

@app.get("/")
def read_root():
    return {"status": "ok", "service": "AI Developer OS Backend API"}

# --- GITHUB INTEGRATION ENDPOINTS ---

@app.get("/api/github/repo")
async def get_repository_info(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    return await make_github_request(f"repos/{owner}/{repo}", token)

@app.get("/api/github/branches")
async def get_branches(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    return await make_github_request(f"repos/{owner}/{repo}/branches", token)

@app.get("/api/github/issues")
async def get_issues(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    return await make_github_request(f"repos/{owner}/{repo}/issues", token)

@app.get("/api/github/commits")
async def get_commits(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    return await make_github_request(f"repos/{owner}/{repo}/commits", token)

@app.get("/api/github/pulls")
async def get_pull_requests(owner: str = Query(...), repo: str = Query(...), token: Optional[str] = None):
    return await make_github_request(f"repos/{owner}/{repo}/pulls", token)

@app.get("/api/github/contents")
async def get_repository_contents(owner: str = Query(...), repo: str = Query(...), path: str = Query(""), token: Optional[str] = None):
    endpoint = f"repos/{owner}/{repo}/contents/{path}" if path else f"repos/{owner}/{repo}/contents"
    return await make_github_request(endpoint, token)

# --- PHASE 3: CODE INTELLIGENCE ENDPOINTS ---

@app.post("/api/intelligence/index")
def index_repository(req: IndexRequest):
    global GLOBAL_CODE_INDEX
    target_dir = req.directory_path or os.getcwd()
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=400, detail=f"Directory {target_dir} does not exist.")
    
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
def search_code_intelligence(query: str = Query(...)):
    global GLOBAL_CODE_INDEX
    if not GLOBAL_CODE_INDEX:
        indexer = CodeIndexer(os.getcwd())
        GLOBAL_CODE_INDEX = indexer.scan_and_index()
        
    engine = SymbolSearchEngine(GLOBAL_CODE_INDEX)
    return engine.search(query)

# --- PHASE 4: PROJECT RAG ENDPOINTS ---

@app.post("/api/rag/index")
def index_project_rag(req: IndexRequest):
    global GLOBAL_RAG_PIPELINE
    target_dir = req.directory_path or os.getcwd()
    GLOBAL_RAG_PIPELINE = ProjectRAGPipeline(target_dir)
    total_chunks = GLOBAL_RAG_PIPELINE.build_index()
    return {
        "status": "success",
        "message": f"Successfully chunked and indexed {total_chunks} code windows into VectorStore."
    }

@app.get("/api/rag/query")
def query_project_rag(question: str = Query(...), top_k: int = Query(4)):
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
    target_dir = req.directory_path or os.getcwd()
    agent = PlannerAgent(target_dir)
    return agent.generate_plan(req.task_request)


# --- PHASE 6: CODE AGENT ENDPOINTS ---

@app.post("/api/agents/coder/modify")
def execute_code_modification(req: ModifyRequest):
    target_dir = req.directory_path or os.getcwd()
    agent = CoderAgent(target_dir)
    return agent.execute_modification(req.plan)
