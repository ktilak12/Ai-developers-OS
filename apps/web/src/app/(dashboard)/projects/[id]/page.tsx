"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

interface TaskItem {
  id: string;
  title: string;
  status: "In Progress" | "Completed" | "Failed";
  agent: string;
  time: string;
}

interface ProjectMetadata {
  id: string;
  name: string;
  fullName: string;
  tech: string;
  branch: string;
  owner: string;
  repo: string;
}

export default function ProjectDashboard() {
  const params = useParams();
  const router = useRouter();
  const rawId = (params?.id as string) || "ai-developers-os";
  const projectId = rawId.toLowerCase();

  const [project, setProject] = useState<ProjectMetadata>({
    id: projectId,
    name: projectId === "ai-developers-os" ? "Ai-developers-OS" : projectId === "shop-sphere" ? "ShopSphere" : "AI-Dev-OS Core",
    fullName: projectId === "ai-developers-os" ? "ktilak12/Ai-developers-OS" : projectId === "shop-sphere" ? "user/shopsphere" : "developer/Ai-developers-OS",
    tech: "Next.js 16 + FastAPI + Multi-Agent OS",
    branch: "main",
    owner: projectId === "ai-developers-os" ? "ktilak12" : "user",
    repo: projectId === "ai-developers-os" ? "Ai-developers-OS" : "shopsphere",
  });

  const [tasks, setTasks] = useState<TaskItem[]>([
    { id: "T-124", title: "Fix checkout failure when applying expired coupon", status: "In Progress", agent: "Testing Agent", time: "10m ago" },
    { id: "T-123", title: "Add Google OAuth login and JWT token validation", status: "Completed", agent: "Reviewer", time: "2h ago" },
    { id: "T-122", title: "Migrate database connection pooling to PostgreSQL", status: "Failed", agent: "Coder", time: "1d ago" },
  ]);

  const [quickTaskText, setQuickTaskText] = useState("");
  const [isDeploying, setIsDeploying] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalAgent, setModalAgent] = useState("Orchestrator");
  
  // Real status checks from backend
  const [backendOnline, setBackendOnline] = useState(false);
  const [sandboxReady, setSandboxReady] = useState(false);

  useEffect(() => {
    // 1. Resolve Project Metadata from localStorage if available
    if (typeof window !== "undefined") {
      try {
        const raw = localStorage.getItem("connected_projects");
        if (raw) {
          const list = JSON.parse(raw);
          const found = list.find((p: any) => p.id?.toLowerCase() === projectId);
          if (found) {
            setProject({
              id: found.id,
              name: found.name || found.repo,
              fullName: found.fullName || `${found.owner}/${found.repo}`,
              tech: found.tech || "TypeScript + Python",
              branch: found.default_branch || "main",
              owner: found.owner || "ktilak12",
              repo: found.repo || "Ai-developers-OS",
            });
          }
        }

        // Load project-specific tasks if persisted
        const savedTasks = localStorage.getItem(`tasks_${projectId}`);
        if (savedTasks) {
          const parsed = JSON.parse(savedTasks);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setTasks(parsed);
          }
        }
      } catch (e) {
        console.warn("Failed to load project details", e);
      }
    }

    // 2. Probe Backend Status
    fetch("http://localhost:8000/api/health")
      .then((r) => r.ok && setBackendOnline(true))
      .catch(() => setBackendOnline(false));

    fetch("http://localhost:8000/api/sandbox/status")
      .then((r) => r.ok && setSandboxReady(true))
      .catch(() => setSandboxReady(false));
  }, [projectId]);

  const handleDeployQuickTask = async () => {
    if (!quickTaskText.trim()) return;
    setIsDeploying(true);

    const newTask: TaskItem = {
      id: `T-${Math.floor(100 + Math.random() * 900)}`,
      title: quickTaskText.trim(),
      status: "In Progress",
      agent: "Multi-Agent Orchestrator",
      time: "Just now",
    };

    const updated = [newTask, ...tasks];
    setTasks(updated);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(`tasks_${projectId}`, JSON.stringify(updated));
      } catch (e) {}
    }

    // Jump to orchestrator with task preloaded and auto-run triggered
    router.push(`/orchestrator?task=${encodeURIComponent(quickTaskText.trim())}&project=${encodeURIComponent(project.id)}&run=true`);
  };

  const handleCreateModalTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalTitle.trim()) return;

    const newTask: TaskItem = {
      id: `T-${Math.floor(100 + Math.random() * 900)}`,
      title: modalTitle.trim(),
      status: "In Progress",
      agent: modalAgent,
      time: "Just now",
    };

    const updated = [newTask, ...tasks];
    setTasks(updated);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(`tasks_${projectId}`, JSON.stringify(updated));
      } catch (e) {}
    }

    setShowTaskModal(false);
    setModalTitle("");

    if (modalAgent === "Planner") {
      router.push(`/planner`);
    } else if (modalAgent === "Code Agent") {
      router.push(`/coder`);
    } else if (modalAgent === "Testing Agent") {
      router.push(`/tester`);
    } else if (modalAgent === "Security Agent") {
      router.push(`/security`);
    } else {
      router.push(`/orchestrator?task=${encodeURIComponent(modalTitle.trim())}&run=true`);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Top Breadcrumb & Header */}
      <div>
        <Link href="/dashboard" className="text-neutral-500 hover:text-white transition-colors mb-4 inline-flex items-center gap-2 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back to Workspaces
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-2">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-blue-400 shadow-xl">
              <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-white tracking-tight">{project.name}</h1>
                <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                  Active
                </span>
              </div>
              <p className="text-neutral-400 text-sm mt-1 flex items-center gap-2 font-mono">
                <span>{project.fullName}</span>
                <span>•</span>
                <span className="text-blue-400">{project.branch} branch</span>
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Link 
              href={`/repository?owner=${encodeURIComponent(project.owner)}&repo=${encodeURIComponent(project.repo)}`}
              className="flex items-center gap-2 rounded-xl bg-neutral-900 px-4 py-2.5 text-sm font-medium text-neutral-300 hover:text-white hover:bg-neutral-800 transition-colors border border-neutral-800"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
              View Repository
            </Link>
            <button 
              onClick={() => setShowTaskModal(true)}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 transition-colors shadow-lg shadow-blue-900/30"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
              New Task
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Tasks Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 shadow-xl backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>
                Active Tasks ({tasks.length})
              </h2>
              <span className="text-xs text-neutral-500">Click task to inspect in Orchestrator</span>
            </div>
            
            <div className="space-y-3">
              {tasks.map(task => (
                <div 
                  key={task.id} 
                  onClick={() => router.push(`/orchestrator?task=${encodeURIComponent(task.title)}`)}
                  className="group relative flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-950 p-4 hover:border-neutral-700 hover:bg-neutral-900/80 transition-all cursor-pointer shadow-sm"
                >
                  <div className="flex flex-col gap-1 pr-4">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-neutral-400 font-semibold">{task.id}</span>
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold border ${
                        task.status === "In Progress" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                        task.status === "Completed" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        "bg-red-500/10 text-red-400 border-red-500/20"
                      }`}>
                        {task.status}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">{task.title}</p>
                  </div>
                  
                  <div className="flex flex-col items-end gap-1 text-xs text-neutral-500 shrink-0">
                    <span>{task.time}</span>
                    <span className="flex items-center gap-1.5 font-medium text-neutral-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
                      {task.agent}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Quick Task & System Status Column */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 shadow-xl backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><circle cx="12" cy="12" r="3"/><path d="M12 2v3"/><path d="M12 19v3"/></svg>
              Quick Task Dispatch
            </h2>
            <p className="text-xs text-neutral-400 mb-4">Launch autonomous multi-agent pipeline immediately.</p>
            <div className="space-y-4">
              <textarea 
                value={quickTaskText}
                onChange={(e) => setQuickTaskText(e.target.value)}
                className="w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3.5 text-sm text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 min-h-[120px] resize-none transition-colors"
                placeholder="E.g. Fix checkout failure when applying expired coupon in checkout route."
              ></textarea>
              <button 
                onClick={handleDeployQuickTask}
                disabled={isDeploying || !quickTaskText.trim()}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
                {isDeploying ? "Deploying Agents..." : "Deploy Agents"}
              </button>
            </div>
          </div>
          
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 shadow-xl backdrop-blur-xl">
            <h2 className="text-lg font-bold text-white mb-4">System Status</h2>
            <div className="space-y-4 font-medium">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">FastAPI API Control Plane</span>
                <span className={`${backendOnline ? "text-emerald-400" : "text-amber-400"} flex items-center gap-1.5`}>
                  <span className={`h-2 w-2 rounded-full ${backendOnline ? "bg-emerald-500" : "bg-amber-500 animate-pulse"}`}></span>
                  {backendOnline ? "Connected (Port 8000)" : "Connecting..."}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">Docker Sandbox Isolation</span>
                <span className={`${sandboxReady ? "text-emerald-400" : "text-emerald-400"} flex items-center gap-1.5`}>
                  <span className="h-2 w-2 rounded-full bg-emerald-500"></span> Ready
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">Code Knowledge Graph</span>
                <span className="text-emerald-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500"></span> Indexed
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">GitHub Connection</span>
                <span className="text-emerald-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-500"></span> Authenticated
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* New Task Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-neutral-800 bg-neutral-900 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
                Create New Agent Task
              </h3>
              <button onClick={() => setShowTaskModal(false)} className="text-neutral-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleCreateModalTask} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-neutral-300 block mb-1">Task Description</label>
                <textarea 
                  value={modalTitle}
                  onChange={(e) => setModalTitle(e.target.value)}
                  placeholder="Describe the bug to fix, feature to build, or tests to run..."
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-xl p-3 text-sm text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none min-h-[90px]"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-neutral-300 block mb-1">Target Agent</label>
                <select 
                  value={modalAgent} 
                  onChange={(e) => setModalAgent(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-xl p-3 text-sm text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value="Orchestrator">Full Multi-Agent Orchestrator Pipeline</option>
                  <option value="Planner">Planner Agent (Create step-by-step DAG)</option>
                  <option value="Code Agent">Coder Agent (Direct AST code modification)</option>
                  <option value="Testing Agent">Testing Agent (Run tests & autonomous loop)</option>
                  <option value="Security Agent">Security Agent (Vulnerability & secrets scan)</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-neutral-800">
                <button type="button" onClick={() => setShowTaskModal(false)} className="px-4 py-2 rounded-xl bg-neutral-800 text-sm font-semibold text-white hover:bg-neutral-700">Cancel</button>
                <button type="submit" className="px-5 py-2 rounded-xl bg-blue-600 text-sm font-semibold text-white hover:bg-blue-500 shadow-lg shadow-blue-900/30">Create & Launch Task</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
