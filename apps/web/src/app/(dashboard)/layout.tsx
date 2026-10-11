"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useState } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [commandQuery, setCommandQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandQuery.trim()) return;
    const q = commandQuery.trim();
    setCommandQuery("");
    if (q.toLowerCase().startsWith("where ") || q.toLowerCase().startsWith("find ") || q.toLowerCase().startsWith("search ")) {
      router.push(`/intelligence?query=${encodeURIComponent(q)}`);
    } else {
      router.push(`/orchestrator?task=${encodeURIComponent(q)}&run=true`);
    }
  };

  const isProjectsActive = pathname === "/dashboard" || pathname.startsWith("/projects");
  const isRepositoryActive = pathname.startsWith("/repository");
  const isIntelligenceActive = pathname.startsWith("/intelligence");
  const isRagActive = pathname.startsWith("/rag");
  const isPlannerActive = pathname.startsWith("/planner");
  const isCoderActive = pathname.startsWith("/coder");
  const isSandboxActive = pathname.startsWith("/sandbox");
  const isTesterActive = pathname.startsWith("/tester");
  const isSecurityActive = pathname.startsWith("/security");
  const isMcpActive = pathname.startsWith("/mcp");
  const isBrowserActive = pathname.startsWith("/browser");
  const isGraphActive = pathname.startsWith("/graph");
  const isMemoryActive = pathname.startsWith("/memory");
  const isOrchestratorActive = pathname.startsWith("/orchestrator");
  const isObservabilityActive = pathname.startsWith("/observability");
  const isEvaluationActive = pathname.startsWith("/evaluation");

  const navClass = (active: boolean) =>
    `flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
      active
        ? "bg-neutral-800 text-white border border-neutral-700/70"
        : "text-neutral-400 hover:bg-neutral-900 hover:text-white"
    }`;

  return (
    <div className="flex h-screen bg-black text-neutral-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-neutral-800/80 bg-neutral-950 flex flex-col">
        <div className="flex h-14 items-center px-5 border-b border-neutral-800/80">
          <Link href="/dashboard" className="flex items-center gap-2.5 text-white">
            <div className="h-6 w-6 rounded-md bg-white text-black flex items-center justify-center font-bold text-xs tracking-tighter">
              AI
            </div>
            <span className="font-semibold text-sm tracking-tight text-white">DEVELOPER OS</span>
          </Link>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-0.5">
          <p className="px-3 text-[10px] font-semibold text-neutral-500 uppercase tracking-wider mb-1.5 mt-2">Workspaces</p>
          <Link href="/dashboard" className={navClass(isProjectsActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
            Projects
          </Link>
          <Link href="/repository" className={navClass(isRepositoryActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            Repository Explorer
          </Link>
          <Link href="/intelligence" className={navClass(isIntelligenceActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            Code Intelligence
          </Link>
          <Link href="/rag" className={navClass(isRagActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            Project RAG
          </Link>

          <p className="px-3 text-[10px] font-semibold text-neutral-500 uppercase tracking-wider mb-1.5 mt-5">Autonomous Agents</p>
          <Link href="/orchestrator" className={navClass(isOrchestratorActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3"/><path d="M12 19v3"/><path d="M2 12h3"/><path d="M19 12h3"/></svg>
            AI Orchestrator
          </Link>
          <Link href="/planner" className={navClass(isPlannerActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="12 8 8 16 16 16 12 8"/></svg>
            Planner Agent
          </Link>
          <Link href="/coder" className={navClass(isCoderActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            Code Agent
          </Link>
          <Link href="/sandbox" className={navClass(isSandboxActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            Docker Sandbox
          </Link>
          <Link href="/tester" className={navClass(isTesterActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m10 2 4 4-2 2-4-4Z"/><path d="m14 6 5 5-2 2-5-5Z"/><path d="m2 22 5.5-1.5L21.3 6.7a2.83 2.83 0 0 0 0-4l-.7-.7a2.83 2.83 0 0 0-4 0L2.8 15.8 1.3 21.3A.5.5 0 0 0 2 22Z"/></svg>
            Testing Agent
          </Link>
          <Link href="/security" className={navClass(isSecurityActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            Security Agent
          </Link>
          <Link href="/browser" className={navClass(isBrowserActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
            Browser Agent
          </Link>

          <p className="px-3 text-[10px] font-semibold text-neutral-500 uppercase tracking-wider mb-1.5 mt-5">Core Engine</p>
          <Link href="/graph" className={navClass(isGraphActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/><line x1="9" y1="6" x2="15" y2="6"/><line x1="6" y1="9" x2="6" y2="15"/></svg>
            Code Graph
          </Link>
          <Link href="/memory" className={navClass(isMemoryActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 10.1"/><path d="M12 12v9.9"/><path d="M12 12h9.9"/></svg>
            Project Memory
          </Link>
          <Link href="/mcp" className={navClass(isMcpActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v8"/><path d="m4.93 10.93 4.24 4.24"/><path d="M2 12h8"/><path d="m4.93 13.07 4.24-4.24"/><path d="M14 18a4 4 0 0 0 4-4V6a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8a4 4 0 0 0 4 4Z"/></svg>
            MCP Tool Hub
          </Link>
          <Link href="/observability" className={navClass(isObservabilityActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            Observability & Traces
          </Link>
          <Link href="/evaluation" className={navClass(isEvaluationActive)}>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>
            SWE Benchmarks
          </Link>
        </nav>
        
        <div className="p-3 border-t border-neutral-800/80">
          <div className="flex items-center gap-3 px-2 py-1.5 rounded-lg bg-neutral-900/60 border border-neutral-800/60">
            <div className="h-7 w-7 rounded-md bg-neutral-800 border border-neutral-700 flex items-center justify-center text-[11px] font-mono text-neutral-300">
              AD
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-xs font-medium text-neutral-200 truncate">Admin</p>
              <p className="text-[10px] text-neutral-500 truncate font-mono">admin@ai-dev.os</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-black">
        {/* Header */}
        <header className="h-14 flex items-center justify-between px-6 border-b border-neutral-800/80 bg-neutral-950 shrink-0">
          <form onSubmit={handleCommandSubmit} className="flex items-center gap-3">
            <div className="relative">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
              <input 
                type="text" 
                value={commandQuery}
                onChange={(e) => setCommandQuery(e.target.value)}
                placeholder="Ask or dispatch a task... (Press Enter)" 
                className="w-80 md:w-96 rounded-lg border border-neutral-800 bg-neutral-900/80 pl-9 pr-3 py-1.5 text-xs text-neutral-200 placeholder-neutral-500 focus:border-neutral-600 focus:outline-none transition-colors"
              />
            </div>
          </form>

          <div className="relative flex items-center gap-3">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="text-neutral-400 hover:text-white transition-colors relative p-1.5 rounded-md hover:bg-neutral-900 border border-transparent hover:border-neutral-800"
              title="Notifications"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
            </button>

            {showNotifications && (
              <div className="absolute right-0 top-11 w-72 rounded-xl border border-neutral-800 bg-neutral-950 p-3.5 shadow-2xl z-50 space-y-2.5">
                <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
                  <span className="text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">System State</span>
                  <span className="text-[10px] text-neutral-400 font-mono">127.0.0.1:8000</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div className="p-2 rounded-lg bg-neutral-900/80 border border-neutral-800">
                    <p className="font-medium text-neutral-200 text-xs">FastAPI Control Plane</p>
                    <p className="text-[11px] text-neutral-400 mt-0.5">Online & responsive</p>
                  </div>
                  <div className="p-2 rounded-lg bg-neutral-900/80 border border-neutral-800">
                    <p className="font-medium text-neutral-200 text-xs">Docker Isolation Engine</p>
                    <p className="text-[11px] text-neutral-400 mt-0.5">Allowlist constraints active</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </header>
        
        {/* Page Content */}
        <div className="flex-1 overflow-auto bg-black p-6 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
