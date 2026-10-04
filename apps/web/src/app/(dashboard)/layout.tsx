"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

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





  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-neutral-800 bg-neutral-900/50 backdrop-blur-xl flex flex-col">
        <div className="flex h-16 items-center px-6 border-b border-neutral-800">
          <div className="flex items-center gap-2 text-blue-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
            <span className="font-bold text-white tracking-wide">AI DEV OS</span>
          </div>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          <p className="px-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2 mt-4">Workspace</p>
          <Link 
            href="/dashboard" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isProjectsActive 
                ? "bg-blue-600/10 text-blue-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
            Projects
          </Link>
          <Link 
            href="/repository" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isRepositoryActive 
                ? "bg-blue-600/10 text-blue-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            Repository Explorer
          </Link>
          <Link 
            href="/intelligence" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isIntelligenceActive 
                ? "bg-purple-600/10 text-purple-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            Code Intelligence
          </Link>
          <Link 
            href="/rag" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isRagActive 
                ? "bg-cyan-600/10 text-cyan-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            Project RAG
          </Link>
          <Link 
            href="/planner" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isPlannerActive 
                ? "bg-amber-600/10 text-amber-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="12 8 8 16 16 16 12 8"/></svg>
            Planner Agent
          </Link>
          <Link 
            href="/coder" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isCoderActive 
                ? "bg-blue-600/10 text-blue-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            Code Agent
          </Link>
          <Link 
            href="/sandbox" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isSandboxActive 
                ? "bg-cyan-600/10 text-cyan-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
            Docker Sandbox
          </Link>
          <Link 
            href="/tester" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isTesterActive 
                ? "bg-emerald-600/10 text-emerald-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m10 2 4 4-2 2-4-4Z"/><path d="m14 6 5 5-2 2-5-5Z"/><path d="m4.5 15.5 2 2"/><path d="m8.5 11.5 2 2"/><path d="m2 22 5.5-1.5L21.3 6.7a2.83 2.83 0 0 0 0-4l-.7-.7a2.83 2.83 0 0 0-4 0L2.8 15.8 1.3 21.3A.5.5 0 0 0 2 22Z"/></svg>
            Testing Agent
          </Link>
          <Link 
            href="/security" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isSecurityActive 
                ? "bg-rose-600/10 text-rose-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            Security Agent
          </Link>
          <Link 
            href="/mcp" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isMcpActive 
                ? "bg-indigo-600/10 text-indigo-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v8"/><path d="m4.93 10.93 4.24 4.24"/><path d="M2 12h8"/><path d="m4.93 13.07 4.24-4.24"/><path d="M14 18a4 4 0 0 0 4-4V6a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8a4 4 0 0 0 4 4Z"/></svg>
            MCP Tool Hub
          </Link>
          <Link 
            href="/browser" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isBrowserActive 
                ? "bg-teal-600/10 text-teal-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
            Browser Agent
          </Link>
          <Link 
            href="/graph" 
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isGraphActive 
                ? "bg-violet-600/10 text-violet-400 font-semibold" 
                : "text-neutral-400 hover:bg-neutral-800/50 hover:text-white"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/><line x1="9" y1="6" x2="15" y2="6"/><line x1="6" y1="9" x2="6" y2="15"/><line x1="9" y1="18" x2="15" y2="18"/><line x1="18" y1="9" x2="18" y2="15"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/></svg>
            Code Graph
          </Link>




          
          <p className="px-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2 mt-6">System</p>
          <Link href="#" className="flex items-center gap-3 rounded-lg text-neutral-400 hover:bg-neutral-800/50 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
            Agents
          </Link>
          <Link href="#" className="flex items-center gap-3 rounded-lg text-neutral-400 hover:bg-neutral-800/50 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Billing
          </Link>
          <Link href="#" className="flex items-center gap-3 rounded-lg text-neutral-400 hover:bg-neutral-800/50 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            Settings
          </Link>
        </nav>
        
        <div className="p-4 border-t border-neutral-800">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white">
              AD
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-white truncate">Admin User</p>
              <p className="text-xs text-neutral-500 truncate">admin@ai-dev.os</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-8 border-b border-neutral-800 bg-neutral-900/30 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-4">
            <div className="relative">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
              <input 
                type="text" 
                placeholder="AI Command Bar (Ask me anything...)" 
                className="w-96 rounded-full border border-neutral-700/50 bg-neutral-900/50 pl-10 pr-4 py-2 text-sm text-neutral-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="text-neutral-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
            </button>
          </div>
        </header>
        
        {/* Page Content */}
        <div className="flex-1 overflow-auto bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-900/20 via-neutral-950 to-neutral-950 p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
