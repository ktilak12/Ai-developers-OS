import os
from typing import Dict, Any, List, Optional
from agents.researcher.tools import ResearcherTools
from llm.provider import get_llm_provider, LLMMessage


RESEARCHER_SYSTEM_PROMPT = """You are the Research Agent for AI Developer OS.
Your role is to gather and synthesize technical knowledge to inform the Planner and Coder agents.

When given a task, you must research:
1. Relevant library APIs, version compatibility, and breaking changes
2. Security best practices for the technologies involved
3. Common implementation patterns and pitfalls to avoid
4. Official documentation references and recommended approaches
5. Dependency conflicts or upgrade considerations

Provide concise, actionable technical intelligence. Focus on what the Coder Agent needs to know.
"""


class ResearcherAgent:
    """
    Researcher Agent: Investigates external technical knowledge, official documentation,
    library APIs, migration guides, compatibility, and implementation patterns.
    Uses an LLM to synthesize research findings from codebase dependency analysis.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.tools = ResearcherTools(root_dir)
        self._llm = None  # lazy init

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    def research_task(self, task_request: str) -> Dict[str, Any]:
        """Performs technical research to inform Planner and Coder agents."""
        deps = self.tools.inspect_dependencies()
        best_practices = self.tools.search_best_practices(task_request)

        # Detect potential breaking changes or specific library patterns
        breaking_changes = []
        task_lower = task_request.lower()

        if "oauth" in task_lower or "auth" in task_lower:
            breaking_changes.append("Verify redirect URIs and CSRF state token handling.")
            breaking_changes.append("Ensure session cookie flags are set to SameSite=Lax and Secure=True.")
        elif "upgrade" in task_lower:
            breaking_changes.append("Check peer dependency conflicts between React 19 and older third-party packages.")
        elif "database" in task_lower or "sql" in task_lower:
            breaking_changes.append("Ensure schema migrations have down/rollback scripts prepared.")

        # Detected stack
        node_deps = deps.get("node_dependencies", {})
        python_deps = deps.get("python_dependencies", [])
        node_list = list(node_deps.keys()) if isinstance(node_deps, dict) else list(node_deps)
        python_list = list(python_deps.keys()) if isinstance(python_deps, dict) else list(python_deps)
        detected_stack = node_list[:8] + python_list[:8]

        # LLM-powered research synthesis
        llm_synthesis = self._synthesize_with_llm(
            task_request=task_request,
            detected_stack=detected_stack,
            breaking_changes=breaking_changes,
            best_practices=best_practices,
        )

        return {
            "status": "success",
            "task_request": task_request,
            "detected_stack_dependencies": detected_stack,
            "relevant_best_practices": best_practices,
            "breaking_changes_flags": breaking_changes,
            "recommended_approach": (
                llm_synthesis.get("recommended_approach")
                or f"Implement changes following standard decoupled architecture "
                   f"with proper unit test assertions for '{task_request}'."
            ),
            "references": [bp.get("reference", "") for bp in best_practices],
            "llm_synthesis": llm_synthesis,
        }

    def _synthesize_with_llm(
        self,
        task_request: str,
        detected_stack: List[str],
        breaking_changes: List[str],
        best_practices: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calls LLM to synthesize research findings into actionable engineering guidance."""
        practices_str = "\n".join([
            f"- {bp.get('title', '')}: {bp.get('description', '')}"
            for bp in best_practices[:5]
        ])
        breaking_str = "\n".join(f"- {b}" for b in breaking_changes) or "None detected."
        stack_str = ", ".join(detected_stack) or "Not detected."

        user_prompt = f"""Research technical requirements for this software engineering task:

Task: {task_request}

Detected technology stack: {stack_str}

Known breaking change risks:
{breaking_str}

Existing best practices in codebase:
{practices_str}

Provide:
1. Recommended implementation approach (2-3 sentences)
2. Key API patterns or library usage to follow
3. Security considerations specific to this task
4. Any version-specific gotchas or compatibility notes
5. Suggested test cases to validate the implementation
"""

        try:
            response = self.llm.chat(
                messages=[LLMMessage(role="user", content=user_prompt)],
                system_prompt=RESEARCHER_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=1536,
            )

            if response.provider == "stub" or "[StubProvider]" in response.content:
                return {}

            text = response.content.strip()
            lines = text.splitlines()

            # Extract recommended approach (first substantive paragraph)
            recommended_approach = None
            for line in lines:
                stripped = line.strip()
                if len(stripped) > 40 and not stripped.startswith(("#", "-", "*", "1.", "2.")):
                    recommended_approach = stripped[:500]
                    break

            return {
                "provider": response.provider,
                "model": response.model,
                "raw_synthesis": text,
                "recommended_approach": recommended_approach,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            }

        except Exception:
            return {}
