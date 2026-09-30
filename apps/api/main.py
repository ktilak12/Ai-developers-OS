from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from typing import Optional, List, Dict, Any

from intelligence.indexing.code_indexer import CodeIndexer
from intelligence.retrieval.symbol_search import SymbolSearchEngine

app = FastAPI(title="AI Developer OS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_API_BASE = "https://api.github.com"

# Global in-memory code index store
GLOBAL_CODE_INDEX: Dict[str, Any] = {}

class IndexRequest(BaseModel):
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
        # Auto-index current workspace if not indexed yet
        indexer = CodeIndexer(os.getcwd())
        GLOBAL_CODE_INDEX = indexer.scan_and_index()
        
    engine = SymbolSearchEngine(GLOBAL_CODE_INDEX)
    return engine.search(query)
