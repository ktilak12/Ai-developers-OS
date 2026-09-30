from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from typing import Optional, List

app = FastAPI(title="AI Developer OS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_API_BASE = "https://api.github.com"

class RepoRequest(BaseModel):
    owner: str
    repo: str

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
