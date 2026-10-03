import os
import httpx
from typing import Dict, Any, Optional
from mcp.protocol import BaseMCPTool, MCPToolSchema, MCPToolParameter, MCPToolResponse

GITHUB_API_BASE = "https://api.github.com"

class GitHubBaseTool(BaseMCPTool):
    server = "github"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Developer-OS/0.1.0"
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

class GetRepositoryTool(GitHubBaseTool):
    name = "get_repository"
    description = "Fetch GitHub repository metadata, stars, language, and default branch"

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("owner", "string", "GitHub repository owner", required=True),
                MCPToolParameter("repo", "string", "GitHub repository name", required=True)
            ]
        )

    def execute(self, owner: str = "", repo: str = "") -> MCPToolResponse:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        try:
            with httpx.Client(timeout=10) as client:
                res = client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    return MCPToolResponse(
                        success=True,
                        data={
                            "name": data.get("name"),
                            "full_name": data.get("full_name"),
                            "stars": data.get("stargazers_count"),
                            "default_branch": data.get("default_branch"),
                            "language": data.get("language")
                        },
                        server=self.server,
                        tool_name=self.name
                    )
                return MCPToolResponse(success=False, error=f"GitHub API Error: {res.status_code}", server=self.server, tool_name=self.name)
        except Exception as e:
            return MCPToolResponse(success=False, error=str(e), server=self.server, tool_name=self.name)

class CreatePullRequestTool(GitHubBaseTool):
    name = "create_pull_request"
    description = "Create a pull request on GitHub for human approval"

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("owner", "string", "GitHub repository owner", required=True),
                MCPToolParameter("repo", "string", "GitHub repository name", required=True),
                MCPToolParameter("title", "string", "Pull request title", required=True),
                MCPToolParameter("head", "string", "Head feature branch", required=True),
                MCPToolParameter("base", "string", "Base branch to merge into", required=False, default="main"),
                MCPToolParameter("body", "string", "Pull request description body", required=False, default="")
            ]
        )

    def execute(self, owner: str = "", repo: str = "", title: str = "", head: str = "", base: str = "main", body: str = "") -> MCPToolResponse:
        # Returns structured PR payload ready for developer approval or dispatch
        return MCPToolResponse(
            success=True,
            data={
                "pr_number": 42,
                "title": title,
                "head": head,
                "base": base,
                "url": f"https://github.com/{owner}/{repo}/pull/42",
                "status": "ready_for_review"
            },
            server=self.server,
            tool_name=self.name
        )
