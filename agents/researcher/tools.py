import os
import json
from typing import Dict, Any, List, Optional


class ResearcherTools:
    """Tools for researching technical specifications, dependencies, and APIs."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def inspect_dependencies(self) -> Dict[str, Any]:
        """Scans project files (package.json, requirements.txt, pyproject.toml) to identify active library versions."""
        deps: Dict[str, Any] = {"node_dependencies": {}, "python_dependencies": {}}
        
        # Check package.json
        pkg_path = os.path.join(self.root_dir, "package.json")
        if not os.path.exists(pkg_path):
            pkg_path = os.path.join(self.root_dir, "apps", "web", "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps["node_dependencies"] = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {})
                    }
            except Exception:
                pass

        # Check requirements.txt
        req_path = os.path.join(self.root_dir, "requirements.txt")
        if os.path.exists(req_path):
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                    deps["python_dependencies"] = lines
            except Exception:
                pass

        return deps

    def search_best_practices(self, query: str) -> List[Dict[str, str]]:
        """Simulates retrieving verified architectural best practices and official API documentation."""
        kb = [
            {
                "topic": "oauth",
                "recommendation": "Use PKCE authorization flow for SPAs. Never expose client secrets in frontend. Store tokens in secure HttpOnly cookies.",
                "reference": "RFC 7636 OAuth 2.0 PKCE Best Practices"
            },
            {
                "topic": "fastapi",
                "recommendation": "Use Pydantic v2 BaseModels with explicit type annotations. Use dependency injection for DB sessions and auth scopes.",
                "reference": "FastAPI Official Production Architecture Guide"
            },
            {
                "topic": "react",
                "recommendation": "Leverage React Server Components (RSC) where possible. Use client components only for user interactivity and state.",
                "reference": "Next.js App Router Documentation"
            },
            {
                "topic": "security",
                "recommendation": "Enforce strict CORS policies, helmet headers, Docker resource ceilings, and input sanitization.",
                "reference": "OWASP API Security Top 10"
            }
        ]
        q_lower = query.lower()
        matched = [item for item in kb if any(word in item["topic"] or word in item["recommendation"].lower() for word in q_lower.split())]
        return matched if matched else kb[:2]
