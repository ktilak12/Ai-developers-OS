"use client";

import { useState, useEffect, useMemo } from "react";

interface ArchitectureComponent {
  id: string;
  component_name: string;
  technology_stack: string[];
  entrypoints: string[];
  conventions: string[];
  description: string;
  dependencies: string[];
  updated_at: string;
}

interface DecisionRecord {
  id: string;
  title: string;
  status: "ACCEPTED" | "PROPOSED" | "SUPERSEDED" | "REJECTED";
  date: string;
  author: string;
  context: string;
  decision: string;
  consequences: string[];
  alternatives_considered: string[];
}

interface TaskRecord {
  id: string;
  task_title: string;
  task_request: string;
  agent_name: string;
  status: "COMPLETED" | "FAILED" | "IN_PROGRESS";
  files_changed: string[];
  test_results?: any;
  fix_summary?: string;
  timestamp: string;
}

interface DeveloperPreference {
  id: string;
  category: "CODING_STYLE" | "TESTING" | "CONVENTIONS" | "FRAMEWORK" | "REVIEW";
  key: string;
  value: string;
  description: string;
  updated_at: string;
}

export default function ProjectMemoryPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "architecture" | "decisions" | "tasks" | "preferences" | "context">("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);

  // Memory states initialized with full offline fallback seeds
  const [architecture, setArchitecture] = useState<ArchitectureComponent[]>([
    {
      id: "arch-fastapi-backend",
      component_name: "FastAPI API Control Plane",
      technology_stack: ["Python", "FastAPI", "Uvicorn", "Pydantic"],
      entrypoints: ["apps/api/main.py"],
      conventions: ["RESTful endpoints", "Type annotations", "Pydantic models"],
      description: "Central backend server providing endpoints for code parsing, graph indexing, agent execution, and memory.",
      dependencies: ["intelligence", "agents", "sandbox", "mcp"],
      updated_at: new Date().toISOString()
    },
    {
      id: "arch-nextjs-web",
      component_name: "Next.js Frontend Control Panel",
      technology_stack: ["Next.js", "React", "TypeScript", "TailwindCSS"],
      entrypoints: ["apps/web/src/app/(dashboard)/layout.tsx"],
      conventions: ["App Router", "Dashboard routes", "Glassmorphic design"],
      description: "Interactive dashboard web application for human oversight, planning, coding, testing, and memory analysis.",
      dependencies: ["FastAPI Backend API"],
      updated_at: new Date().toISOString()
    },
    {
      id: "arch-graphrag-engine",
      component_name: "Code Intelligence & GraphRAG Engine",
      technology_stack: ["Python", "Tree-Sitter", "Vector DB", "Adjacency Index"],
      entrypoints: ["intelligence/graph/builder.py", "intelligence/retrieval/retriever.py"],
      conventions: ["AST parsing", "Symbol resolution", "Blast radius estimation"],
      description: "Analyzes code structures, builds code graph, performs semantic vector retrieval and graph impact analysis.",
      dependencies: [],
      updated_at: new Date().toISOString()
    }
  ]);

  const [decisions, setDecisions] = useState<DecisionRecord[]>([
    {
      id: "adr-001-in-memory-graph",
      title: "ADR-001: Fast In-Memory Knowledge Graph Engine",
      status: "ACCEPTED",
      date: "2026-10-01",
      author: "Lead Architect Agent",
      context: "The system requires high-frequency blast radius and AST symbol dependency lookups during agent coding loops.",
      decision: "Implement an optimized in-memory adjacency list graph store (`KnowledgeGraphStore`) with JSON persistence fallback.",
      consequences: ["Sub-millisecond query latency for blast radius calculations", "Low overhead without needing external graph DB"],
      alternatives_considered: ["Neo4j standalone server", "NetworkX heavy dependency"]
    },
    {
      id: "adr-002-docker-sandbox-isolation",
      title: "ADR-002: Docker-Based Isolated Execution Sandbox",
      status: "ACCEPTED",
      date: "2026-10-03",
      author: "Security Agent",
      context: "Untrusted code execution and shell tool calls must not compromise the host system.",
      decision: "Enforce Docker sandbox isolation with strict resource limits (--memory=512m, cpu=1.5) and restricted permissions.",
      consequences: ["Protects developer OS from malicious scripts", "Reproducible testing environment"],
      alternatives_considered: ["Direct host process execution", "Chroot jail"]
    }
  ]);

  const [tasks, setTasks] = useState<TaskRecord[]>([
    {
      id: "task-001",
      task_title: "Phase 12 Knowledge Graph Integration",
      task_request: "Build AST code parser, graph builder, blast radius impact analyzer, and FastAPI graph endpoints.",
      agent_name: "Coder Agent",
      status: "COMPLETED",
      files_changed: [
        "intelligence/graph/models.py",
        "intelligence/graph/builder.py",
        "intelligence/graph/storage.py",
        "apps/api/main.py"
      ],
      test_results: { passed: true, passed_tests: 8, failed_tests: 0 },
      fix_summary: "Successfully built sub-millisecond GraphRAG engine with full blast radius estimation.",
      timestamp: new Date().toISOString()
    }
  ]);

  const [preferences, setPreferences] = useState<DeveloperPreference[]>([
    {
      id: "pref-python-style",
      category: "CODING_STYLE",
      key: "Python Indentation & Formatting",
      value: "4 spaces per indent level, PEP8 compliance, explicit type annotations",
      description: "All Python files in backend and intelligence packages must follow standard PEP8 conventions.",
      updated_at: new Date().toISOString()
    },
    {
      id: "pref-testing-framework",
      category: "TESTING",
      key: "Primary Test Runner",
      value: "pytest (Python) / npm test (TypeScript/Web)",
      description: "Execute pytest for core backend tests and npm test for web component validation.",
      updated_at: new Date().toISOString()
    },
    {
      id: "pref-ui-aesthetics",
      category: "FRAMEWORK",
      key: "UI Component Design Aesthetics",
      value: "Dark mode glassmorphism, HSL tailwind colors, micro-animations",
      description: "Frontend dashboard interfaces must look state-of-the-art and feel responsive with sleek dark themes.",
      updated_at: new Date().toISOString()
    }
  ]);

  const [promptContext, setPromptContext] = useState<string>("");

  // New ADR Form modal state
  const [showAdrModal, setShowAdrModal] = useState(false);
  const [newAdrTitle, setNewAdrTitle] = useState("");
  const [newAdrContext, setNewAdrContext] = useState("");
  const [newAdrDecision, setNewAdrDecision] = useState("");

  // Fetch memory data from FastAPI backend on load
  useEffect(() => {
    async function loadMemoryData() {
      setLoading(true);
      try {
        const [archRes, decRes, taskRes, prefRes, ctxRes] = await Promise.all([
          fetch("http://localhost:8000/api/memory/architecture").then((r) => r.ok ? r.json() : null),
          fetch("http://localhost:8000/api/memory/decisions").then((r) => r.ok ? r.json() : null),
          fetch("http://localhost:8000/api/memory/tasks").then((r) => r.ok ? r.json() : null),
          fetch("http://localhost:8000/api/memory/preferences").then((r) => r.ok ? r.json() : null),
          fetch("http://localhost:8000/api/memory/context").then((r) => r.ok ? r.json() : null),
        ]);

        if (archRes?.components) setArchitecture(archRes.components);
        if (decRes?.decisions) setDecisions(decRes.decisions);
        if (taskRes?.tasks) setTasks(taskRes.tasks);
        if (prefRes?.preferences) setPreferences(prefRes.preferences);
        if (ctxRes?.context) setPromptContext(ctxRes.context);
      } catch (err) {
        console.warn("Using persistent memory state (offline or fallback)", err);
      } finally {
        setLoading(false);
      }
    }
    loadMemoryData();
  }, []);

  const handleCreateAdr = async () => {
    if (!newAdrTitle || !newAdrDecision) return;
    const newRecord: DecisionRecord = {
      id: `adr-${String(decisions.length + 1).padStart(3, "0")}-${newAdrTitle.toLowerCase().replace(/\s+/g, "-")}`,
      title: newAdrTitle,
      status: "ACCEPTED",
      date: new Date().toISOString().split("T")[0],
      author: "Developer / Lead AI Agent",
      context: newAdrContext || "Manual architectural decision entry.",
      decision: newAdrDecision,
      consequences: ["Documented in Project Memory"],
      alternatives_considered: []
    };

    setDecisions([newRecord, ...decisions]);
    setShowAdrModal(false);
    setNewAdrTitle("");
    setNewAdrContext("");
    setNewAdrDecision("");

    try {
      await fetch("http://localhost:8000/api/memory/decisions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newRecord),
      });
    } catch (e) {
      console.error("Failed to persist ADR to API", e);
    }
  };

  const filteredDecisions = useMemo(() => {
    if (!searchQuery) return decisions;
    const q = searchQuery.toLowerCase();
    return decisions.filter(
      (d) => d.title.toLowerCase().includes(q) || d.decision.toLowerCase().includes(q) || d.context.toLowerCase().includes(q)
    );
  }, [decisions, searchQuery]);

  const filteredArchitecture = useMemo(() => {
    if (!searchQuery) return architecture;
    const q = searchQuery.toLowerCase();
    return architecture.filter(
      (a) => a.component_name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q) || a.technology_stack.some(t => t.toLowerCase().includes(q))
    );
  }, [architecture, searchQuery]);

  return (
    <div className="flex-1 overflow-y-auto bg-neutral-950 p-8 text-neutral-100">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 10.1"/><path d="M12 12v9.9"/><path d="M12 12h9.9"/></svg>
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Project Memory Store
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-medium">Phase 13</span>
              </h1>
              <p className="text-sm text-neutral-400 mt-1">
                Persistent architecture records, decision history (ADRs), task execution logs, and developer preferences.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAdrModal(true)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors flex items-center gap-2 shadow-lg shadow-emerald-600/20"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            New ADR Decision
          </button>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Architecture Components</span>
            <span className="text-blue-400 p-1.5 rounded-lg bg-blue-500/10">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/></svg>
            </span>
          </div>
          <p className="text-2xl font-bold text-white mt-2 font-mono">{architecture.length}</p>
          <p className="text-xs text-neutral-500 mt-1">Modules, tech stack & conventions</p>
        </div>

        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Decision Records (ADRs)</span>
            <span className="text-emerald-400 p-1.5 rounded-lg bg-emerald-500/10">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </span>
          </div>
          <p className="text-2xl font-bold text-white mt-2 font-mono">{decisions.length}</p>
          <p className="text-xs text-emerald-400 mt-1">{decisions.filter(d => d.status === "ACCEPTED").length} Accepted decisions</p>
        </div>

        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Recorded Task History</span>
            <span className="text-purple-400 p-1.5 rounded-lg bg-purple-500/10">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </span>
          </div>
          <p className="text-2xl font-bold text-white mt-2 font-mono">{tasks.length}</p>
          <p className="text-xs text-purple-400 mt-1">Past tasks, fixes & test runs</p>
        </div>

        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Preferences & Rules</span>
            <span className="text-amber-400 p-1.5 rounded-lg bg-amber-500/10">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            </span>
          </div>
          <p className="text-2xl font-bold text-white mt-2 font-mono">{preferences.length}</p>
          <p className="text-xs text-neutral-500 mt-1">Formatting & linting rules</p>
        </div>
      </div>

      {/* Navigation Tabs and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-b border-neutral-800 pb-4 mb-6">
        <div className="flex items-center gap-2 overflow-x-auto">
          {[
            { id: "overview", label: "Overview", icon: "📊" },
            { id: "architecture", label: "Architecture Memory", icon: "🏗️" },
            { id: "decisions", label: "Decision Memory (ADRs)", icon: "📜" },
            { id: "tasks", label: "Task History", icon: "⏱️" },
            { id: "preferences", label: "Preferences & Rules", icon: "⚙️" },
            { id: "context", label: "Agent LLM Context", icon: "💬" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3.5 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-neutral-800 text-white font-semibold border border-neutral-700 shadow-sm"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/50"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative min-w-[260px]">
          <svg className="absolute left-3 top-2.5 h-4 w-4 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search memory records..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-sm bg-neutral-900 border border-neutral-800 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Architecture Overview */}
            <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
              <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <span>🏗️</span> Key Architecture Components
              </h2>
              <div className="space-y-3">
                {architecture.slice(0, 3).map((comp) => (
                  <div key={comp.id} className="p-4 rounded-xl bg-neutral-900/80 border border-neutral-800/80">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-emerald-400 text-sm">{comp.component_name}</h3>
                      <div className="flex gap-1">
                        {comp.technology_stack.map((tech) => (
                          <span key={tech} className="text-[10px] px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 font-mono">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                    <p className="text-xs text-neutral-400 mt-1">{comp.description}</p>
                    <div className="mt-2 text-[11px] text-neutral-500 flex items-center gap-2 font-mono">
                      <span>Entry:</span>
                      <span className="text-neutral-300">{comp.entrypoints.join(", ")}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent ADRs */}
            <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
              <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <span>📜</span> Active Architecture Decisions (ADRs)
              </h2>
              <div className="space-y-3">
                {decisions.slice(0, 3).map((adr) => (
                  <div key={adr.id} className="p-4 rounded-xl bg-neutral-900/80 border border-neutral-800/80">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-white text-sm">{adr.title}</h3>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                        {adr.status}
                      </span>
                    </div>
                    <p className="text-xs text-neutral-300 mt-1 line-clamp-2">{adr.decision}</p>
                    <div className="mt-2 text-[11px] text-neutral-500 flex items-center justify-between font-mono">
                      <span>{adr.author}</span>
                      <span>{adr.date}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ARCHITECTURE */}
      {activeTab === "architecture" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredArchitecture.map((comp) => (
            <div key={comp.id} className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="text-lg font-bold text-white">{comp.component_name}</h3>
                  <span className="text-xs px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono font-medium">
                    {comp.id}
                  </span>
                </div>
                <p className="text-sm text-neutral-300 mb-4">{comp.description}</p>

                <div className="space-y-3">
                  <div>
                    <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1.5">Technology Stack</span>
                    <div className="flex flex-wrap gap-1.5">
                      {comp.technology_stack.map((tech) => (
                        <span key={tech} className="px-2.5 py-1 rounded-lg bg-neutral-800 text-xs font-mono text-emerald-400 border border-neutral-700">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1.5">Entrypoints</span>
                    <ul className="list-disc list-inside text-xs text-neutral-300 font-mono space-y-1">
                      {comp.entrypoints.map((ep) => (
                        <li key={ep}>{ep}</li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1.5">Conventions & Patterns</span>
                    <div className="flex flex-wrap gap-1.5">
                      {comp.conventions.map((conv) => (
                        <span key={conv} className="px-2 py-0.5 rounded bg-neutral-800/80 text-[11px] text-neutral-300">
                          {conv}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: DECISION MEMORY (ADRs) */}
      {activeTab === "decisions" && (
        <div className="space-y-4">
          {filteredDecisions.map((adr) => (
            <div key={adr.id} className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono text-xs font-semibold">
                    {adr.id}
                  </span>
                  <h3 className="text-base font-bold text-white">{adr.title}</h3>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-neutral-400">By {adr.author}</span>
                  <span className="text-neutral-600">•</span>
                  <span className="text-neutral-400">{adr.date}</span>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">
                    {adr.status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-neutral-800/60">
                <div>
                  <h4 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-1">Context</h4>
                  <p className="text-sm text-neutral-300">{adr.context}</p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-1">Decision</h4>
                  <p className="text-sm text-emerald-300 font-medium">{adr.decision}</p>
                </div>
              </div>

              {adr.consequences.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-1">Consequences & Benefits</h4>
                  <ul className="list-disc list-inside text-xs text-neutral-300 space-y-0.5">
                    {adr.consequences.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* TAB 4: TASK HISTORY */}
      {activeTab === "tasks" && (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div key={task.id} className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono text-xs font-bold">
                    {task.id}
                  </span>
                  <h3 className="text-base font-bold text-white">{task.task_title}</h3>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold font-mono">
                  {task.status}
                </span>
              </div>
              <p className="text-sm text-neutral-300 mb-3">{task.task_request}</p>

              <div className="p-3 rounded-xl bg-neutral-950/60 border border-neutral-800/80 mb-3">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1">Files Changed</span>
                <div className="flex flex-wrap gap-1.5 font-mono text-xs text-neutral-300">
                  {task.files_changed.map((f) => (
                    <span key={f} className="px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800">
                      {f}
                    </span>
                  ))}
                </div>
              </div>

              {task.fix_summary && (
                <div className="text-xs text-emerald-400 font-mono flex items-center gap-2">
                  <span>Resolution:</span>
                  <span className="text-neutral-300">{task.fix_summary}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* TAB 5: DEVELOPER PREFERENCES */}
      {activeTab === "preferences" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {preferences.map((pref) => (
            <div key={pref.id} className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold text-white text-base">{pref.key}</h3>
                <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono font-semibold">
                  {pref.category}
                </span>
              </div>
              <p className="text-xs text-neutral-400 mb-3">{pref.description}</p>
              <div className="p-3 rounded-xl bg-neutral-950/80 border border-neutral-800 font-mono text-xs text-emerald-300">
                {pref.value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 6: AGENT LLM CONTEXT */}
      {activeTab === "context" && (
        <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Synthesized Agent LLM Context</h2>
              <p className="text-xs text-neutral-400 mt-0.5">
                This exact structured context is dynamically injected into Planner, Coder, Reviewer, and Security AI prompts.
              </p>
            </div>
          </div>

          <pre className="p-5 rounded-xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {promptContext || "Loading synthesized prompt context..."}
          </pre>
        </div>
      )}

      {/* Create New ADR Modal */}
      {showAdrModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl bg-neutral-900 border border-neutral-800 p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Record Architectural Decision (ADR)</h3>
            <div>
              <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1">Title</label>
              <input
                type="text"
                placeholder="e.g. ADR-003: Use Redis for Memory Cache"
                value={newAdrTitle}
                onChange={(e) => setNewAdrTitle(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-neutral-950 border border-neutral-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1">Context & Problem Statement</label>
              <textarea
                rows={3}
                placeholder="Describe the problem context and constraints..."
                value={newAdrContext}
                onChange={(e) => setNewAdrContext(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-neutral-950 border border-neutral-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-1">Decision & Rationale</label>
              <textarea
                rows={3}
                placeholder="State the decision and key architectural reasons..."
                value={newAdrDecision}
                onChange={(e) => setNewAdrDecision(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-neutral-950 border border-neutral-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-neutral-800">
              <button
                onClick={() => setShowAdrModal(false)}
                className="px-4 py-2 text-sm font-medium rounded-lg text-neutral-400 hover:bg-neutral-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateAdr}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                Save Decision
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
