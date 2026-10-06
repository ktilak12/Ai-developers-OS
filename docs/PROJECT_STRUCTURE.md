# 📁 AI Developer OS — Project File Structure

```text
Ai-developers-OS/
├── .gitignore                          # Git ignore rules
├── pyproject.toml                      # Project metadata & pytest configuration
├── requirements.txt                    # Python runtime & test dependencies
├── README.md                           # Master documentation and overview
│
├── agents/                             # Autonomous Specialized AI Agents
│   ├── __init__.py                     # Package exports for all agents
│   ├── planner/                        # 🧭 Planner Agent (Task breakdown & step DAGs)
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   ├── researcher/                     # 🔎 Research Agent (Codebase & docs investigations)
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   ├── coder/                          # 💻 Coder Agent (AST-aware edits & unified diffs)
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   ├── tester/                         # 🧪 Testing Agent (Sandbox validation & retry loop)
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   ├── security/                       # 🔐 Security Agent (AST scan & entropy checks)
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   ├── rules.py
│   │   └── tools.py
│   ├── reviewer/                       # 👁 Reviewer Agent (Code review & PR standards)
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   └── tools.py
│   └── browser/                        # 🌐 Browser Verification Agent (End-to-end UI testing)
│       ├── __init__.py
│       ├── agent.py
│       └── tools.py
│
├── apps/                               # Full-Stack Applications
│   ├── api/                            # 🚀 FastAPI REST & WebSocket Backend
│   │   └── main.py                     # Main application entrypoint & API endpoints
│   └── web/                            # 💻 Next.js 16 + Tailwind CSS Frontend Dashboard
│       ├── package.json
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── src/
│           ├── app/
│           │   ├── layout.tsx
│           │   ├── page.tsx
│           │   ├── login/
│           │   └── (dashboard)/
│           │       ├── layout.tsx      # Sidebar navigation & command bar
│           │       ├── dashboard/      # Project overview
│           │       ├── repository/     # Interactive code repository explorer
│           │       ├── intelligence/   # AST symbols & semantic search
│           │       ├── rag/            # Project RAG query engine
│           │       ├── graph/          # GraphRAG knowledge graph visualizer
│           │       ├── orchestrator/   # Autonomous multi-agent pipeline
│           │       ├── memory/         # Architectural memory & decisions
│           │       ├── observability/  # OpenTelemetry spans & waterfall traces
│           │       ├── evaluation/     # 20 SWE benchmark tasks & scorecard
│           │       ├── planner/
│           │       ├── coder/
│           │       ├── tester/
│           │       ├── security/
│           │       ├── sandbox/
│           │       ├── mcp/
│           │       └── browser/
│           └── components/             # Reusable UI component library
│
├── intelligence/                       # Code Intelligence & Graph Engine
│   ├── __init__.py
│   ├── indexing/                       # Tree-Sitter AST parser & symbol extraction
│   ├── retrieval/                      # Hybrid semantic search & Project RAG pipeline
│   ├── graph/                          # GraphRAG knowledge graph builder, store, query
│   ├── embeddings/                     # Embedding generators
│   └── reranking/                      # Cross-encoder context rerankers
│
├── orchestrator/                       # Multi-Agent Workflow Engine
│   ├── __init__.py
│   ├── workflow.py                     # Central execution pipeline (Planner->Coder->Tester->PR)
│   ├── state.py                        # OrchestratorState & workflow lifecycle models
│   ├── router.py                       # Dynamic agent routing
│   ├── events.py                       # Asynchronous EventBus & telemetry
│   └── permissions.py                  # Human approval gate policies
│
├── memory/                             # Persistent Project Memory (Phase 13)
│   ├── __init__.py
│   ├── manager.py                      # Storage coordinator
│   ├── models.py                       # Architecture, Decision, Task, Preference records
│   ├── architecture.py                 # System design & tech stack store
│   ├── decisions.py                    # ADRs (Architecture Decision Records)
│   ├── tasks.py                        # Historical task logs & self-healing learnings
│   └── preferences.py                  # Developer coding style preferences
│
├── observability/                      # OpenTelemetry Agent Tracing (Phase 15)
│   ├── __init__.py
│   ├── models.py                       # WorkflowTrace, AgentSpan, ToolCallTrace schemas
│   ├── tracer.py                       # AgentTracer lifecycle & USD cost calculation
│   ├── metrics.py                      # Aggregates success rates, latencies, failure stats
│   └── manager.py                      # ObservabilityManager with persistence
│
├── evaluation/                         # SWE Evaluation & Benchmarks (Phase 16)
│   ├── __init__.py
│   ├── models.py                       # SWEBenchmarkTask, ComparativeScorecard schemas
│   ├── dataset.py                      # 20 real-world SWE benchmark tasks dataset
│   ├── evaluator.py                    # SWEEvaluator comparing Agent v1 vs Agent v2
│   └── report.py                       # Markdown report & summary generator
│
├── sandbox/                            # Secure Execution Environment
│   ├── __init__.py
│   ├── runner/                         # ContainerRunner & Subprocess executor
│   ├── docker/                         # Dockerfile definitions
│   ├── policies/                       # Security & timeout rules
│   └── resource_limits/                # CPU, Memory, PID quota configurations
│
├── mcp/                                # Model Context Protocol (MCP) Server Layer
│   ├── __init__.py
│   ├── protocol.py                     # MCP message definitions
│   ├── registry.py                     # Dynamic tool registry
│   ├── filesystem/                     # MCP Filesystem tools
│   ├── terminal/                       # MCP Terminal tools
│   ├── github/                         # MCP GitHub tools
│   ├── docker/                         # MCP Docker tools
│   └── browser/                        # MCP Browser tools
│
├── docs/                               # Architectural Documentation
│   └── PROJECT_STRUCTURE.md            # Complete file tree and directory map
│
└── tests/                              # Automated Test Suite (29 tests)
    ├── test_agents_helpers.py
    ├── test_api_memory.py
    ├── test_api_observability_evaluation.py
    ├── test_api_orchestrator.py
    ├── test_evaluation.py
    ├── test_memory.py
    ├── test_observability.py
    └── test_orchestrator.py
```
