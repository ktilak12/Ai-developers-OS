import Link from "next/link";

export default function ProjectDashboard({ params }: { params: { id: string } }) {
  const tasks = [
    { id: "T-124", title: "Fix checkout failure when applying expired coupon", status: "In Progress", agent: "Testing Agent", time: "10m ago" },
    { id: "T-123", title: "Add Google OAuth login", status: "Completed", agent: "Reviewer", time: "2h ago" },
    { id: "T-122", title: "Migrate database to PostgreSQL", status: "Failed", agent: "Coder", time: "1d ago" },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <Link href="/dashboard" className="text-neutral-500 hover:text-white transition-colors mb-4 inline-flex items-center gap-2 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back to Projects
        </Link>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-300">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">ShopSphere</h1>
              <p className="text-neutral-400 mt-1">github.com/user/shopsphere • main branch</p>
            </div>
          </div>
          <button className="flex items-center gap-2 rounded-lg bg-neutral-800 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 transition-colors border border-neutral-700">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
            New Task
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6">
            <h2 className="text-lg font-bold text-white mb-4">Active Tasks</h2>
            
            <div className="space-y-4">
              {tasks.map(task => (
                <div key={task.id} className="group relative flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-950 p-4 hover:border-neutral-700 transition-colors cursor-pointer">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-neutral-500">{task.id}</span>
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border ${
                        task.status === "In Progress" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                        task.status === "Completed" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        "bg-red-500/10 text-red-400 border-red-500/20"
                      }`}>
                        {task.status}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-white">{task.title}</p>
                  </div>
                  
                  <div className="flex flex-col items-end gap-1 text-xs text-neutral-500">
                    <span>{task.time}</span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-neutral-500"></span>
                      {task.agent}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6">
            <h2 className="text-lg font-bold text-white mb-4">Quick Task</h2>
            <div className="space-y-4">
              <textarea 
                className="w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 text-sm text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 min-h-[120px] resize-none"
                placeholder="E.g. Fix the checkout failure when a user applies an expired coupon in issue #124."
              ></textarea>
              <button className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-lg shadow-blue-900/20">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
                Deploy Agents
              </button>
            </div>
          </div>
          
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6">
            <h2 className="text-lg font-bold text-white mb-4">System Status</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">Project Knowledge</span>
                <span className="text-emerald-400 flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Indexed</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">Sandbox Docker</span>
                <span className="text-emerald-400 flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Ready</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">GitHub Connection</span>
                <span className="text-emerald-400 flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Connected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
