import Link from "next/link";

export default function ProjectsPage() {
  const projects = [
    {
      id: "shop-sphere",
      name: "ShopSphere",
      tech: "React + Node + PostgreSQL",
      issues: 23,
      prs: 8,
      status: "Active",
      updatedAt: "2 hours ago"
    },
    {
      id: "ai-dev-os",
      name: "AI-Dev-OS",
      tech: "Next.js + Python + Redis",
      issues: 5,
      prs: 2,
      status: "Active",
      updatedAt: "5 mins ago"
    }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Projects</h1>
          <p className="text-neutral-400 mt-1">Manage your active workspaces and repositories.</p>
        </div>
        <Link 
          href="/projects/new" 
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-lg shadow-blue-900/20"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
          Connect Repository
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map(project => (
          <Link href={`/projects/${project.id}`} key={project.id} className="group relative overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 hover:border-neutral-700 hover:bg-neutral-900 transition-all">
            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" className="text-neutral-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </div>
            
            <div className="flex items-start justify-between mb-4">
              <div className="h-10 w-10 rounded-lg bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-300">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
              </div>
              <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                {project.status}
              </span>
            </div>
            
            <h3 className="text-xl font-bold text-white mb-1">{project.name}</h3>
            <p className="text-sm text-neutral-400 mb-6">{project.tech}</p>
            
            <div className="flex items-center gap-6 text-sm">
              <div className="flex flex-col">
                <span className="text-neutral-500 text-xs">Issues</span>
                <span className="font-semibold text-neutral-200">{project.issues}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-neutral-500 text-xs">Open PRs</span>
                <span className="font-semibold text-neutral-200">{project.prs}</span>
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-neutral-800/50 text-xs text-neutral-500 flex justify-between items-center">
              <span>Updated {project.updatedAt}</span>
              <span className="text-blue-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">Open Workspace</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
