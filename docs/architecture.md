# System Architecture

## Overview
AI Developer OS is an AI-powered developer workspace that understands a software project and coordinates specialized AI agents to analyze issues, modify code, run tests, inspect results, and prepare changes for developer approval.

## Main Components
1. **Developer Workspace:** Frontend UI (Next.js)
2. **AI Orchestrator:** Coordinates agents.
3. **Agent System:** Planner, Coder, Tester, Security, Research, Reviewer.
4. **Tool Layer:** MCP connections to GitHub, Docker, Browser, etc.
5. **Project Intelligence:** Tree-sitter parser, Embeddings, RAG, GraphRAG.
6. **Memory:** Project, Task, Decision, and History memory.
7. **Secure Sandbox:** Docker container for code execution.
8. **Observability:** Logs, traces, metrics.
9. **Human Approval Layer:** Explicit approval for critical actions.

## User Flow
1. User connects a GitHub repository.
2. User enters a software task/issue.
3. System (Orchestrator) invokes Planner Agent to create an implementation plan.
4. Orchestrator invokes Coder Agent to modify code inside a Docker sandbox.
5. Orchestrator invokes Testing Agent to run tests.
6. (If tests fail, loop back to Coder).
7. Orchestrator invokes Security Agent for checks.
8. Orchestrator invokes Reviewer Agent.
9. Changes are shown to the user (Diff).
10. User approves and a PR is created.
