"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function NewProjectPage() {
  const router = useRouter();
  const [repoInput, setRepoInput] = useState("ktilak12/Ai-developers-OS");
  const [tokenInput, setTokenInput] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const parseOwnerRepo = (input: string): { owner: string; repo: string } | null => {
    const cleaned = input.trim().replace(/^https?:\/\/github\.com\//i, "").replace(/\.git$/i, "");
    const parts = cleaned.split("/").map(s => s.trim()).filter(Boolean);
    if (parts.length >= 2) {
      return { owner: parts[parts.length - 2], repo: parts[parts.length - 1] };
    }
    return null;
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const parsed = parseOwnerRepo(repoInput);
    if (!parsed) {
      setError("Please enter a valid repository format like 'owner/repository' or a GitHub URL.");
      return;
    }

    setIsVerifying(true);
    try {
      const tokenParam = tokenInput.trim() ? `&token=${encodeURIComponent(tokenInput.trim())}` : "";
      const res = await fetch(`http://localhost:8000/api/github/repo?owner=${encodeURIComponent(parsed.owner)}&repo=${encodeURIComponent(parsed.repo)}${tokenParam}`);
      
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data.detail || `GitHub API error (${res.status})`;
        if (res.status === 403 && detail.toLowerCase().includes("rate limit")) {
          setError("GitHub API rate limit reached (60 req/hr unauthenticated). Please provide a GitHub Personal Access Token below to authenticate.");
        } else if (res.status === 404) {
          setError(`Repository '${parsed.owner}/${parsed.repo}' not found. Check repository visibility or provide a GitHub token for private repositories.`);
        } else {
          setError(detail);
        }
        setIsVerifying(false);
        return;
      }

      const repoData = await res.json();
      
      // Persist to connected_projects list for Dashboard and Project views
      if (typeof window !== "undefined") {
        try {
          const raw = localStorage.getItem("connected_projects");
          const existing = raw ? JSON.parse(raw) : [];
          const projectId = parsed.repo.toLowerCase();
          const newProject = {
            id: projectId,
            name: repoData.name || parsed.repo,
            fullName: repoData.full_name || `${parsed.owner}/${parsed.repo}`,
            tech: repoData.language ? `${repoData.language} (GitHub)` : "TypeScript + Python",
            issues: repoData.open_issues_count || 0,
            prs: 0,
            stars: repoData.stargazers_count || 0,
            status: "Active",
            updatedAt: "Just now",
            owner: parsed.owner,
            repo: parsed.repo,
            default_branch: repoData.default_branch || "main",
            description: repoData.description || "Connected GitHub workspace"
          };
          const filtered = existing.filter((p: any) => p.id !== projectId);
          localStorage.setItem("connected_projects", JSON.stringify([newProject, ...filtered]));
        } catch (e) {
          console.warn("Could not save to localStorage", e);
        }
      }

      setSuccess(`Connected to ${repoData.full_name || `${parsed.owner}/${parsed.repo}`}! Redirecting to Repository Explorer...`);
      
      setTimeout(() => {
        router.push(`/repository?owner=${encodeURIComponent(parsed.owner)}&repo=${encodeURIComponent(parsed.repo)}`);
      }, 1000);
    } catch (err: any) {
      setError(`Failed to reach backend API (http://localhost:8000). Ensure the backend service is running.`);
      setIsVerifying(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-4">
      <div className="mb-8">
        <Link href="/dashboard" className="text-neutral-500 hover:text-white transition-colors mb-4 inline-flex items-center gap-2 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          Back to Projects
        </Link>
        <h1 className="text-3xl font-bold text-white tracking-tight">Connect Repository</h1>
        <p className="text-neutral-400 mt-1">Import a GitHub repository to start using AI Developer OS autonomous multi-agent pipelines.</p>
      </div>

      <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-8 shadow-2xl backdrop-blur-sm">
        <form onSubmit={handleConnect} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-neutral-200 mb-2">
              GitHub Repository (URL or Owner/Name)
            </label>
            <div className="relative">
              <input 
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="e.g. ktilak12/Ai-developers-OS or vercel/next.js"
                className="w-full rounded-xl border border-neutral-700 bg-neutral-950 px-4 py-3 text-sm text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
                required
              />
            </div>
            <p className="text-xs text-neutral-500 mt-2">
              Accepts <code className="text-neutral-400">owner/repo</code> or full URL <code className="text-neutral-400">https://github.com/owner/repo</code>
            </p>
          </div>

          {/* Quick presets */}
          <div>
            <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block mb-2">Quick Presets:</span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setRepoInput("ktilak12/Ai-developers-OS")}
                className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-xs text-neutral-200 transition-colors"
              >
                ktilak12/Ai-developers-OS (Current Project)
              </button>
              <button
                type="button"
                onClick={() => setRepoInput("vercel/next.js")}
                className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-xs text-neutral-200 transition-colors"
              >
                vercel/next.js
              </button>
              <button
                type="button"
                onClick={() => setRepoInput("facebook/react")}
                className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-xs text-neutral-200 transition-colors"
              >
                facebook/react
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-200 mb-2">
              GitHub Personal Access Token <span className="text-neutral-500 text-xs">(Optional — for private repos & higher rate limits)</span>
            </label>
            <input 
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx or github_pat_xxxx"
              className="w-full rounded-xl border border-neutral-700 bg-neutral-950 px-4 py-3 text-sm text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
            />
            <p className="text-xs text-neutral-500 mt-2">
              GitHub limits unauthenticated requests to 60/hr. Supplying a PAT gives 5,000 requests/hr and access to private repos.
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400 flex items-start gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <div>{error}</div>
            </div>
          )}

          {success && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-400 flex items-center gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
              <div>{success}</div>
            </div>
          )}

          <div className="pt-2">
            <button 
              type="submit" 
              disabled={isVerifying}
              className="w-full flex items-center justify-center gap-3 rounded-xl bg-blue-600 text-white px-6 py-3.5 font-semibold hover:bg-blue-500 transition-colors shadow-lg shadow-blue-950/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isVerifying ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Verifying & Connecting...
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
                  Connect Repository
                </>
              )}
            </button>
          </div>
        </form>

        <div className="mt-8 pt-6 border-t border-neutral-800 flex items-center justify-between text-xs text-neutral-500">
          <span>Supported: GitHub Cloud & GitHub Enterprise</span>
          <Link href="/repository" className="text-blue-400 hover:underline">
            Go to Repository Explorer directly &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
