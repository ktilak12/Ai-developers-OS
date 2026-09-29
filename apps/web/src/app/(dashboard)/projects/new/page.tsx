import Link from "next/link";

export default function NewProjectPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <Link href="/dashboard" className="text-neutral-500 hover:text-white transition-colors mb-4 inline-flex items-center gap-2 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back to Projects
        </Link>
        <h1 className="text-3xl font-bold text-white tracking-tight">Connect Repository</h1>
        <p className="text-neutral-400 mt-1">Import a GitHub repository to start using AI Developer OS.</p>
      </div>

      <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-8 shadow-2xl">
        <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-neutral-700 rounded-xl bg-neutral-900/30">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-neutral-800 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Connect GitHub Account</h2>
          <p className="text-neutral-400 text-center max-w-sm mb-6">Authorize AI Developer OS to access your repositories and create pull requests on your behalf.</p>
          
          <button className="flex items-center gap-3 rounded-lg bg-white text-black px-6 py-3 font-semibold hover:bg-neutral-200 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            Connect GitHub
          </button>
        </div>
        
        <div className="mt-8 flex items-center justify-between">
          <p className="text-sm text-neutral-500">Need help? <Link href="#" className="text-blue-500 hover:underline">Read the docs</Link></p>
        </div>
      </div>
    </div>
  );
}
