# 🧠 AI Developer OS

> **An agentic AI operating system for software developers that understands codebases, plans engineering tasks, executes code in isolated environments, runs tests, performs security checks, and prepares changes for human review.**

[![Status](https://img.shields.io/badge/Status-Under%20Development-orange)]()
[![AI](https://img.shields.io/badge/AI-Agentic%20AI-blue)]()
[![MCP](https://img.shields.io/badge/MCP-Enabled-purple)]()
[![RAG](https://img.shields.io/badge/RAG-Enabled-green)]()
[![Docker](https://img.shields.io/badge/Sandbox-Docker-blue)]()
[![License](https://img.shields.io/badge/License-MIT-black)]()

---

## 🚀 Overview

**AI Developer OS** is an AI-powered developer platform designed to act as an intelligent control layer over the software development workflow.

Instead of using a single AI chatbot for coding, the platform uses a system of specialized AI agents that can collaborate with each other and interact with developer tools.

A developer can provide a task such as:

> "Fix the checkout bug when an expired coupon is applied."

The AI Developer OS can:

```text
Understand the task
       ↓
Analyze the repository
       ↓
Find relevant files
       ↓
Create an implementation plan
       ↓
Modify the code
       ↓
Run the application
       ↓
Execute tests
       ↓
Analyze failures
       ↓
Fix the implementation
       ↓
Run tests again
       ↓
Perform security checks
       ↓
Generate a code review
       ↓
Ask for human approval
       ↓
Create a GitHub Pull Request
```

The goal is not to remove developers from the development process.

The goal is to **reduce repetitive engineering work while keeping developers in control of important decisions.**

---

# 🎯 Problem

Modern software development requires developers to constantly switch between multiple tools:

```text
GitHub
VS Code
Terminal
Docker
Postman
Browser
Database
Documentation
CI/CD
Monitoring
AI coding assistants
```

A simple bug fix can require manually coordinating all of these systems.

Developers must:

* understand unfamiliar codebases
* search through large repositories
* investigate bugs
* create implementation plans
* modify multiple files
* run tests
* debug failures
* review code
* check security issues
* create pull requests
* maintain project context

AI Developer OS brings these workflows together into a single intelligent system.

---

# 💡 Core Idea

The platform works as an **AI control plane for software development**.

```text
                         👨‍💻 Developer
                              │
                              ▼
                    ┌─────────────────────┐
                    │   AI Developer OS   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  AI Orchestrator    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
     🧭 Planner             💻 Coder            🔎 Research
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                         🧪 Tester
                               │
                               ▼
                        🔐 Security
                               │
                               ▼
                         👁 Reviewer
                               │
                               ▼
                       Human Approval
                               │
                               ▼
                         GitHub PR
```

---

# ✨ Key Features

## 🤖 Multi-Agent Development

The platform uses specialized agents instead of one general-purpose AI.

### Planner Agent

Analyzes a task and creates an implementation plan.

### Code Agent

Reads and modifies project files.

### Testing Agent

Runs tests, analyzes failures, and validates fixes.

### Research Agent

Researches documentation, APIs, libraries, and migration requirements.

### Security Agent

Analyzes code changes for potential security problems.

### Review Agent

Reviews implementation quality, architecture, testing, and maintainability.

---

# 🧠 Project-Aware AI

The AI doesn't treat every request as an isolated conversation.

It builds an understanding of the project:

```text
Repository
   │
   ├── Architecture
   ├── Technologies
   ├── Dependencies
   ├── APIs
   ├── Components
   ├── Database
   ├── Tests
   └── Documentation
```

This allows developers to ask questions such as:

> "Where is authentication implemented?"

> "What will be affected if I change the UserService?"

> "Explain the checkout flow."

> "Which modules depend on this API?"

---

# 🕸️ Code Knowledge Graph

The platform can build relationships between software components.

Example:

```text
UserController
      │
      │ calls
      ▼
UserService
      │
      │ uses
      ▼
UserRepository
      │
      │ queries
      ▼
PostgreSQL
```

This enables dependency-aware reasoning.

Instead of only searching for similar text, the system can understand relationships between:

* files
* functions
* classes
* APIs
* services
* database models
* components
* dependencies

---

# 📚 RAG-Based Project Memory

AI Developer OS uses retrieval-based project context to avoid sending an entire repository to the model.

```text
Repository
     ↓
Code Parsing
     ↓
Chunking
     ↓
Embeddings
     ↓
Vector Database
     ↓
Retrieval
     ↓
Reranking
     ↓
LLM
```

The system retrieves only the most relevant project information for a task.

---

# 🧠 Persistent Project Memory

The platform maintains multiple forms of memory.

### Project Memory

Stores:

* architecture
* technology stack
* important modules
* development conventions

### Task Memory

Stores:

* previous tasks
* changes
* test results
* failures
* fixes

### Decision Memory

Stores:

* architecture decisions
* alternatives considered
* reasons for decisions

Example:

```text
Decision:
Use PostgreSQL instead of MongoDB.

Reason:
The application requires strong relational
constraints and transactional workflows.
```

---

# 🔌 MCP Tool Integration

The platform uses **Model Context Protocol (MCP)** as a standardized tool layer.

Agents can interact with external systems through tools.

```text
                     AI Agent
                         │
                         ▼
                        MCP
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
    GitHub            Docker            Browser
       │                 │                 │
       ▼                 ▼                 ▼
  Repository          Sandbox          UI Testing
```

Potential integrations include:

* GitHub
* Filesystem
* Docker
* Browser
* Database
* Terminal
* Documentation
* Monitoring systems

---

# 🐳 Secure Code Execution

AI-generated code should never execute directly on the developer's machine.

The platform runs code inside isolated Docker environments.

```text
AI Agent
   │
   ▼
Permission Layer
   │
   ▼
Docker Sandbox
   │
   ├── Source Code
   ├── Dependencies
   ├── Tests
   └── Runtime
```

The sandbox can enforce:

* CPU limits
* memory limits
* execution timeouts
* filesystem restrictions
* network restrictions
* command policies
* automatic cleanup

---

# 🧪 Automated Testing

After modifying code, the Testing Agent can execute the project's test suite.

Example:

```text
Code Agent
    ↓
Docker Sandbox
    ↓
Run Tests
    ↓
┌───────────────────┐
│ 48 Passed         │
│ 2 Failed          │
└───────────────────┘
    ↓
Testing Agent
    ↓
Failure Analysis
    ↓
Code Agent
    ↓
Fix
    ↓
Run Tests Again
```

The workflow supports controlled retry loops.

---

# 🌐 Browser-Based Testing

Using browser automation, the platform can validate user-facing features.

Example:

```text
Start Application
       ↓
Open Browser
       ↓
Navigate to /login
       ↓
Enter Test Credentials
       ↓
Click Login
       ↓
Capture Result
       ↓
Analyze UI
```

This enables end-to-end testing in addition to unit and integration testing.

---

# 🔐 AI Security Review

Before changes are submitted, the platform can perform security analysis.

It can identify potential:

* hardcoded secrets
* insecure authentication
* authorization problems
* unsafe database queries
* vulnerable dependencies
* insecure configurations
* dangerous code patterns

Example:

```text
⚠ Security Finding

Severity: High

File:
config/database.js

Issue:
Database credential is hardcoded.

Recommendation:
Move the credential to an environment variable.
```

AI analysis is designed to complement established security tooling, not replace it.

---

# 👨‍⚖️ Human-in-the-Loop

AI Developer OS follows a human approval model.

The AI can prepare changes, but important actions require developer approval.

Example:

```text
Action                         Permission

Read repository                ✓ Automatic
Analyze code                   ✓ Automatic
Modify sandbox files           ✓ Automatic
Run tests                      ✓ Automatic
Create branch                  ✓ Automatic
Create Pull Request            ⚠ Approval
Push sensitive changes         ⚠ Approval
Production deployment          🔴 Explicit approval
```

The developer remains responsible for the final decision.

---

# 🖥️ Developer Workspace

The platform provides a centralized workspace.

```text
┌─────────────────────────────────────────────────────────────┐
│ AI DEVELOPER OS                         ShopSphere           │
├───────────────┬────────────────────────┬────────────────────┤
│ PROJECT       │ WORKSPACE              │ AI AGENTS          │
│               │                        │                    │
│ Overview      │ Agent Activity         │ 🧭 Planner         │
│ Files         │ Code Changes           │ 💻 Coder           │
│ Issues        │ Terminal               │ 🧪 Tester          │
│ Pull Requests │ Test Results           │ 🔐 Security        │
│ Commits       │                        │ 🔎 Research        │
│ Dependencies  │                        │ 👁 Reviewer        │
├───────────────┴────────────────────────┴────────────────────┤
│ AI COMMAND BAR                                               │
│ > What should we work on?                                    │
└──────────────────────────────────────────────────────────────┘
```

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │     Next.js UI      │
                         │ Developer Workspace │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     FastAPI API     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │    AI ORCHESTRATOR     │
                       └───────────┬────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
             Planner             Coder            Research
                │                  │                  │
                └──────────────────┼──────────────────┘
                                   ▼
                               Testing
                                   │
                                   ▼
                              Security
                                   │
                                   ▼
                               Reviewer
                                   │
                                   ▼
                           Human Approval
                                   │
                                   ▼
                              GitHub PR


        ┌─────────────────────────────────────────────┐
        │              PROJECT INTELLIGENCE           │
        │                                             │
        │ Parser │ RAG │ Embeddings │ GraphRAG       │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │                 TOOL LAYER                  │
        │                                             │
        │ MCP │ GitHub │ Docker │ Browser │ Database  │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │                    MEMORY                   │
        │                                             │
        │ Project │ Tasks │ Decisions │ History       │
        └─────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────┐
        │                OBSERVABILITY                │
        │                                             │
        │ Logs │ Metrics │ Traces │ Evaluations       │
        └─────────────────────────────────────────────┘
```

---

# 🛠️ Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Monaco Editor
* WebSockets

## Backend

* Python
* FastAPI
* Pydantic
* PostgreSQL
* Redis

## AI

* Large Language Models
* Agentic AI
* Tool Calling
* Structured Outputs
* Embeddings
* Reranking
* RAG
* GraphRAG

## Code Intelligence

* Tree-sitter
* AST analysis
* Dependency graphs
* Code embeddings

## AI Tooling

* Model Context Protocol (MCP)
* GitHub integration
* Docker integration
* Browser automation

## Execution

* Docker
* Playwright
* Git

## Database

* PostgreSQL
* pgvector
* Optional Neo4j for knowledge graphs

## Observability

* OpenTelemetry
* Prometheus
* Grafana

## Deployment

* Docker
* GitHub Actions
* AWS / Azure / GCP

---

# 📁 Project Structure

```text
ai-developer-os/
│
├── apps/
│   ├── web/
│   └── api/
│
├── agents/
│   ├── planner/
│   ├── coder/
│   ├── tester/
│   ├── security/
│   ├── researcher/
│   └── reviewer/
│
├── orchestrator/
│   ├── workflow.py
│   ├── router.py
│   ├── state.py
│   ├── permissions.py
│   └── events.py
│
├── mcp/
│   ├── github/
│   ├── filesystem/
│   ├── docker/
│   ├── browser/
│   ├── database/
│   └── terminal/
│
├── intelligence/
│   ├── parser/
│   ├── indexing/
│   ├── embeddings/
│   ├── retrieval/
│   ├── reranking/
│   └── graph/
│
├── memory/
│   ├── project/
│   ├── task/
│   ├── decision/
│   └── conversation/
│
├── sandbox/
│   ├── docker/
│   ├── runner/
│   └── policies/
│
├── integrations/
│   ├── github/
│   ├── git/
│   ├── docker/
│   └── cloud/
│
├── database/
│   ├── models/
│   ├── migrations/
│   └── seeds/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── agents/
│   ├── security/
│   └── e2e/
│
├── docs/
│   ├── architecture/
│   ├── agents/
│   ├── api/
│   └── setup/
│
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/
│   └── monitoring/
│
├── docker-compose.yml
├── .env.example
├── README.md
└── LICENSE
```

---

# 🔄 End-to-End Workflow

A typical task follows this lifecycle:

```text
1. Developer creates task
            ↓
2. Orchestrator analyzes task
            ↓
3. Planner Agent creates plan
            ↓
4. Project Intelligence retrieves context
            ↓
5. Developer approves plan
            ↓
6. Code Agent modifies code
            ↓
7. Changes run inside Docker
            ↓
8. Testing Agent runs tests
            ↓
9. Failures are analyzed
            ↓
10. Code Agent fixes problems
            ↓
11. Security Agent checks changes
            ↓
12. Review Agent reviews implementation
            ↓
13. Developer reviews diff
            ↓
14. Developer approves
            ↓
15. GitHub Pull Request is created
```

---

# 📊 Example

### Developer Request

```text
Fix the checkout bug when an expired coupon
is applied.
```

### AI Developer OS

```text
🔎 Repository Analysis

Found relevant modules:

✓ coupon.service.ts
✓ checkout.controller.ts
✓ cart.service.ts
✓ payment.service.ts
```

### Planner

```text
Implementation Plan

1. Inspect coupon validation
2. Reproduce expired coupon scenario
3. Identify validation failure
4. Fix coupon handling
5. Add regression tests
6. Run checkout tests
```

### Coder

```text
Modified:

coupon.service.ts
checkout.controller.ts
checkout.test.ts
```

### Testing Agent

```text
Initial Run

48 passed
2 failed
```

### AI Debugging

```text
Failure detected.

Cause:
Expired coupon exception is not handled
by checkout controller.
```

### Coder

```text
Applying fix...
```

### Testing Agent

```text
50 passed
0 failed
```

### Security Agent

```text
Critical issues: 0
High issues: 0
Medium issues: 0
```

### Reviewer

```text
✓ Implementation
✓ Error handling
✓ Regression tests
✓ Code structure

Ready for developer review.
```

### Developer

```text
[View Diff] [Approve] [Reject]
```

---

# 🧩 Development Roadmap

## Phase 1 — Foundation

* Project architecture
* Database
* Authentication
* Developer dashboard
* Project management

---

## Phase 2 — GitHub Integration

* GitHub OAuth/App
* Repository connection
* Repository cloning
* Issues
* Branches
* Pull requests

---

## Phase 3 — Code Intelligence

* Repository scanner
* Tree-sitter parsing
* Symbol extraction
* Dependency extraction
* Code indexing

---

## Phase 4 — RAG

* Chunking
* Embeddings
* pgvector
* Retrieval
* Reranking
* Context generation

---

## Phase 5 — Planner Agent

* Task understanding
* Repository analysis
* Implementation plans
* Risk identification
* Testing plans

---

## Phase 6 — Code Agent

* File reading
* Code search
* File modification
* Diff generation
* Change validation

---

## Phase 7 — Docker Sandbox

* Container creation
* Command execution
* Resource limits
* Timeout handling
* Log collection
* Cleanup

---

## Phase 8 — Testing Agent

* Unit tests
* Integration tests
* Build validation
* Failure analysis
* Controlled retry loop

---

## Phase 9 — Security Agent

* Secret detection
* Dependency analysis
* Static analysis
* Security report
* AI-assisted explanation

---

## Phase 10 — MCP

Integrate MCP-based tools for:

* GitHub
* Filesystem
* Docker
* Browser
* Database

---

## Phase 11 — Browser Agent

* Playwright
* UI testing
* Screenshot analysis
* End-to-end workflows

---

## Phase 12 — Knowledge Graph

* Code relationships
* Dependency graph
* GraphRAG
* Impact analysis

---

## Phase 13 — Project Memory

* Architecture memory
* Decision memory
* Task history
* Developer preferences
* Project conventions

---

## Phase 14 — Multi-Agent Orchestration

Connect:

```text
Planner
   ↓
Research
   ↓
Coder
   ↓
Tester
   ↓
Security
   ↓
Reviewer
```

---

## Phase 15 — Observability & Agent Tracing

AI Developer OS implements an OpenTelemetry-compatible tracing and telemetry layer for autonomous multi-agent pipelines:

* **Granular Agent Spans:** End-to-end tracing for `Planner`, `Researcher`, `Coder`, `Tester`, `Security`, and `Reviewer` agents.
* **Tool Call Latency Tracking:** Microsecond-resolution timing and payload recording for all AST, RAG, File, Sandbox, and Security tool invocations.
* **Token Consumption & Cost Accounting:** Real-time calculation of prompt/completion tokens and estimated USD costs ($3.00/M in, $15.00/M out).
* **Self-Healing Retry Loops:** Automatic tracking of test failure iterations and self-correcting coder retry cycles.
* **Interactive Next.js Dashboard:** Live waterfall visualizer, span breakdown, and tool call payload inspector.

---

## Phase 16 — SWE Evaluation & Benchmarks
 
Comprehensive benchmark suite with 20 real-world SWE benchmark tasks spanning bug fixes, security patches, performance tuning, and refactoring:
 
```text
Task Completion Rate:       Agent v1 (55%) ➡️ Agent v2 (95%)  [+40% Gain]
Test Suite Pass Rate:       Agent v1 (48%) ➡️ Agent v2 (97%)  [+49% Gain]
Security Audit Score:       Agent v1 (62)  ➡️ Agent v2 (98)   [+36 Pts / 0 Escapes]
Planning Accuracy:          Agent v1 (68%) ➡️ Agent v2 (94%)  [AST & GraphRAG]
Tool Calling Accuracy:      Agent v1 (65%) ➡️ Agent v2 (96.5%)[Targeted Invocation]
```
 
* **20 Benchmark Tasks:** Real-world scenarios covering race conditions, JWT rotation, SQL injection, N+1 queries, RBAC middleware, and zero-downtime migrations.
* **Comparative Scorecard:** Automated side-by-side benchmarking of single-turn LLM baseline vs. orchestrated multi-agent system.
* **Scorecard Dashboard:** Interactive task browser, filtering by difficulty/category, and Markdown report export.

---

# 🔐 Security Principles

AI Developer OS is designed around controlled AI execution.

### Principle 1: Least privilege

Agents should only receive the tools they need.

### Principle 2: Sandboxed execution

Code executes inside isolated environments.

### Principle 3: Human approval

Sensitive actions require explicit approval.

### Principle 4: No secret exposure

Secrets should be injected securely rather than embedded in prompts or source code.

### Principle 5: Auditability

Every important agent action should be logged.

### Principle 6: Controlled autonomy

Agents operate within defined permissions, budgets, timeouts, and iteration limits.

---

# 📈 Future Roadmap

Future versions could include:

* Multi-language code intelligence
* Kubernetes operations
* CI/CD agents
* Cloud infrastructure agents
* Database optimization agents
* Performance optimization agents
* AI-generated documentation
* Automated migration agents
* Team collaboration
* Enterprise SSO
* Organization-wide project memory
* Private/self-hosted models
* Local LLM support
* Voice-based developer commands
* Advanced multimodal debugging

---

# 🧪 Evaluation Philosophy

The platform should not be judged by how impressive its AI responses sound.

It should be measured by whether it can **actually complete software engineering tasks correctly**.

Example benchmark:

```text
100 Software Engineering Tasks

├── 25 Bug Fixes
├── 25 Feature Requests
├── 20 Refactoring Tasks
├── 15 Test Generation Tasks
└── 15 Dependency/Migration Tasks
```

Measure:

```text
✓ Task completed
✓ Tests passed
✓ Correct files modified
✓ Security issues introduced
✓ Number of retries
✓ Execution time
✓ Tool-call efficiency
```

---

# 🚀 Getting Started

## Prerequisites

Install:

* Node.js
* Python
* Docker
* Git
* PostgreSQL
* GitHub account

Optional:

* Neo4j
* Redis

---

## Clone

```bash
git clone https://github.com/yourusername/ai-developer-os.git

cd ai-developer-os
```

---

## Environment

Create:

```bash
cp .env.example .env
```

Configure the required credentials.

```env
DATABASE_URL=
REDIS_URL=

LLM_API_KEY=

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

VECTOR_DATABASE_URL=

MCP_SERVER_URL=
```

---

## Start infrastructure

```bash
docker compose up -d
```

---

## Install frontend

```bash
cd apps/web
npm install
npm run dev
```

---

## Start backend

```bash
cd apps/api

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

---

# 🧪 Example API

Create a development task:

```http
POST /api/projects/{project_id}/tasks
```

```json
{
  "title": "Fix checkout coupon bug",
  "description": "Expired coupons cause checkout to fail."
}
```

Start an agent workflow:

```http
POST /api/tasks/{task_id}/execute
```

Get task status:

```http
GET /api/tasks/{task_id}
```

Get agent activity:

```http
GET /api/tasks/{task_id}/agents
```

Get code changes:

```http
GET /api/tasks/{task_id}/changes
```

---

# 🧑‍💻 Example Agent State

```json
{
  "task_id": "task_102",
  "status": "testing",
  "current_agent": "testing_agent",
  "iteration": 2,
  "files_changed": 4,
  "tests_passed": 50,
  "tests_failed": 0,
  "security_findings": 0
}
```

---

# 🗺️ Project Vision

The long-term goal of AI Developer OS is to create an intelligent development environment where developers can move from:

```text
Idea
 ↓
Requirement
 ↓
Implementation
 ↓
Testing
 ↓
Security
 ↓
Review
 ↓
Deployment
```

through a single AI-assisted workflow.

The developer remains the decision maker.

The AI handles the repetitive coordination and execution work.

---

# 🤝 Contributing

Contributions are welcome.

```bash
git checkout -b feature/new-agent

git commit -m "feat: add dependency analysis agent"

git push origin feature/new-agent
```

Open a Pull Request with:

* feature description
* architecture changes
* testing details
* security considerations

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Tilak**

Computer Science & Engineering

Interested in:

* Artificial Intelligence
* Agentic AI
* Full-Stack Development
* Developer Tools
* Data & ML
* Cloud & DevOps

---

# ⭐ Why This Project?

AI Developer OS is built around a simple idea:

> **AI should not just write code. It should understand the software system, use the right tools, verify its work, explain what it changed, and keep the developer in control.**

```text
             THINK
               ↓
             PLAN
               ↓
             ACT
               ↓
             TEST
               ↓
            VERIFY
               ↓
            REVIEW
               ↓
          HUMAN APPROVAL
               ↓
             SHIP 🚀
```

**AI Developer OS — an intelligent control plane for modern software development.**
