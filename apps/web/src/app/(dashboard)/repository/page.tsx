"use client";

import { useState, useEffect } from "react";
import { 
  fetchRepoInfo, 
  fetchBranches, 
  fetchIssues, 
  fetchCommits, 
  fetchPullRequests, 
  fetchRepoContents,
  RepoInfo, BranchInfo, IssueInfo, CommitInfo, PullRequestInfo, FileContent 
} from "@/lib/github";

export default function RepositoryExplorerPage() {
  const [repoInput, setRepoInput] = useState("vercel/next.js");
  const [owner, setOwner] = useState("vercel");
  const [repo, setRepo] = useState("next.js");

  const [activeTab, setActiveTab] = useState<"files" | "issues" | "commits" | "pulls">("files");
  const [repoInfo, setRepoInfo] = useState<RepoInfo | null>(null);
  const [branches, setBranches] = useState<BranchInfo[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("main");
  const [issues, setIssues] = useState<IssueInfo[]>([]);
  const [commits, setCommits] = useState<CommitInfo[]>([]);
  const [pulls, setPulls] = useState<PullRequestInfo[]>([]);
  const [contents, setContents] = useState<FileContent[]>([]);
  const [currentPath, setCurrentPath] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const loadRepositoryData = async (targetOwner: string, targetRepo: string) => {
    setLoading(true);
    const [infoData, branchData, issueData, commitData, prData, contentData] = await Promise.all([
      fetchRepoInfo(targetOwner, targetRepo),
      fetchBranches(targetOwner, targetRepo),
      fetchIssues(targetOwner, targetRepo),
      fetchCommits(targetOwner, targetRepo),
      fetchPullRequests(targetOwner, targetRepo),
      fetchRepoContents(targetOwner, targetRepo, ""),
    ]);

    setRepoInfo(infoData);
    setBranches(branchData);
    if (branchData.length > 0) {
      setSelectedBranch(infoData.default_branch || branchData[0].name);
    }
    setIssues(issueData);
    setCommits(commitData);
    setPulls(prData);
    setContents(contentData);
    setCurrentPath("");
    setLoading(false);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlOwner = params.get("owner");
      const urlRepo = params.get("repo");
      if (urlOwner && urlRepo) {
        setOwner(urlOwner);
        setRepo(urlRepo);
        setRepoInput(`${urlOwner}/${urlRepo}`);
        loadRepositoryData(urlOwner, urlRepo);
        return;
      }
    }
    loadRepositoryData(owner, repo);
  }, []);

  const handleConnectRepo = (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = repoInput.trim().replace(/^https?:\/\/github\.com\//i, "").replace(/\.git$/i, "");
    const parts = cleaned.split("/").map(s => s.trim()).filter(Boolean);
    if (parts.length >= 2) {
      const newOwner = parts[parts.length - 2];
      const newRepo = parts[parts.length - 1];
      setOwner(newOwner);
      setRepo(newRepo);
      loadRepositoryData(newOwner, newRepo);
    }
  };

  const navigateToPath = async (newPath: string) => {
    setLoading(true);
    const data = await fetchRepoContents(owner, repo, newPath);
    setContents(data);
    setCurrentPath(newPath);
    setLoading(false);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header & Repo Selector */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white tracking-tight">Repository Explorer</h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-900 px-2.5 py-0.5 text-[11px] font-medium text-neutral-300 border border-neutral-800">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
              Live Sync
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">Inspect live code, branches, commits, issues, and PRs from GitHub.</p>
        </div>

        <div className="flex flex-col md:items-end gap-2">
          <form onSubmit={handleConnectRepo} className="flex gap-2">
            <div className="relative">
              <input 
                type="text"
                value={repoInput}
                onChange={(e) => setRepoInput(e.target.value)}
                placeholder="owner/repository or URL"
                className="w-64 rounded-lg border border-neutral-800 bg-neutral-900/80 px-3.5 py-2 text-xs text-white placeholder-neutral-500 focus:border-neutral-600 focus:outline-none transition-colors"
              />
            </div>
            <button 
              type="submit"
              className="rounded-lg bg-white px-3.5 py-2 text-xs font-semibold text-black hover:bg-neutral-200 transition-colors shadow-sm flex items-center gap-1.5"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
              Load
            </button>
          </form>
          <div className="flex items-center gap-2 text-[11px] text-neutral-400">
            <span>Presets:</span>
            <button 
              type="button" 
              onClick={() => { setRepoInput("ktilak12/Ai-developers-OS"); setOwner("ktilak12"); setRepo("Ai-developers-OS"); loadRepositoryData("ktilak12", "Ai-developers-OS"); }}
              className="text-neutral-300 hover:text-white underline font-mono"
            >
              ktilak12/Ai-developers-OS
            </button>
            <span>•</span>
            <button 
              type="button" 
              onClick={() => { setRepoInput("vercel/next.js"); setOwner("vercel"); setRepo("next.js"); loadRepositoryData("vercel", "next.js"); }}
              className="text-neutral-400 hover:text-white underline font-mono"
            >
              vercel/next.js
            </button>
          </div>
        </div>
      </div>

      {/* Repository Card Header */}
      {repoInfo && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="h-10 w-10 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-neutral-300">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
              </div>
              <div>
                <a href={repoInfo.html_url} target="_blank" rel="noreferrer" className="text-base font-semibold text-white hover:text-neutral-300 transition-colors flex items-center gap-2">
                  {repoInfo.full_name}
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-500"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
                <p className="text-xs text-neutral-400 mt-0.5">{repoInfo.description || "No description provided."}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs text-neutral-400 font-mono">
              <div className="flex items-center gap-1.5 bg-neutral-900 px-2.5 py-1 rounded-md border border-neutral-800">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                <span>{repoInfo.stargazers_count?.toLocaleString()} Stars</span>
              </div>
              <div className="flex items-center gap-1.5 bg-neutral-900 px-2.5 py-1 rounded-md border border-neutral-800">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v1a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9"/><path d="M12 12v3"/></svg>
                <span>{repoInfo.forks_count?.toLocaleString()} Forks</span>
              </div>
              <div className="flex items-center gap-1.5 bg-neutral-900 px-2.5 py-1 rounded-md border border-neutral-800">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span>{repoInfo.open_issues_count?.toLocaleString()} Issues</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs & Branch Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-neutral-800 pb-3">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <button 
            onClick={() => setActiveTab("files")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "files" ? "bg-white text-black font-semibold shadow-sm" : "text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
            Files
          </button>
          <button 
            onClick={() => setActiveTab("issues")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "issues" ? "bg-white text-black font-semibold shadow-sm" : "text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            Issues ({issues.length})
          </button>
          <button 
            onClick={() => setActiveTab("commits")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "commits" ? "bg-white text-black font-semibold shadow-sm" : "text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4"/><line x1="1.05" y1="12" x2="8" y2="12"/><line x1="16" y1="12" x2="22.95" y2="12"/></svg>
            Commits ({commits.length})
          </button>
          <button 
            onClick={() => setActiveTab("pulls")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "pulls" ? "bg-white text-black font-semibold shadow-sm" : "text-neutral-400 hover:text-white hover:bg-neutral-900"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
            Pull Requests ({pulls.length})
          </button>
        </div>

        {/* Branch dropdown */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-neutral-500">Branch:</span>
          <select 
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            className="rounded-lg border border-neutral-800 bg-neutral-900 px-2.5 py-1 text-xs font-mono text-neutral-200 focus:border-neutral-600 focus:outline-none"
          >
            {branches.map(b => (
              <option key={b.name} value={b.name}>{b.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tab Content */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 min-h-[360px]">
        {loading ? (
          <div className="flex items-center justify-center h-48 text-neutral-400 gap-2.5 text-xs">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-400 border-t-transparent" />
            <span>Fetching data from GitHub API...</span>
          </div>
        ) : (
          <>
            {/* FILES TAB */}
            {activeTab === "files" && (
              <div>
                {/* Breadcrumbs */}
                <div className="mb-3.5 flex items-center gap-2 text-xs text-neutral-400 bg-neutral-900/60 px-3.5 py-2 rounded-lg border border-neutral-800">
                  <button onClick={() => navigateToPath("")} className="hover:text-white font-mono">root</button>
                  {currentPath.split("/").filter(Boolean).map((part, idx, arr) => {
                    const subPath = arr.slice(0, idx + 1).join("/");
                    return (
                      <span key={subPath} className="flex items-center gap-2">
                        <span>/</span>
                        <button onClick={() => navigateToPath(subPath)} className="hover:text-white font-mono">{part}</button>
                      </span>
                    );
                  })}
                </div>

                {/* File Table */}
                <div className="divide-y divide-neutral-850 rounded-lg border border-neutral-800 bg-neutral-900/30 overflow-hidden">
                  {Array.isArray(contents) && contents.map((item) => (
                    <div 
                      key={item.path}
                      onClick={() => item.type === "dir" ? navigateToPath(item.path) : null}
                      className={`flex items-center justify-between px-3.5 py-2.5 text-xs transition-colors ${
                        item.type === "dir" ? "cursor-pointer hover:bg-neutral-900" : "hover:bg-neutral-900/50"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        {item.type === "dir" ? (
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-500"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                        )}
                        <span className={`font-mono ${item.type === "dir" ? "font-medium text-white" : "text-neutral-300"}`}>
                          {item.name}
                        </span>
                      </div>
                      {item.size && (
                        <span className="text-[11px] text-neutral-500 font-mono">{(item.size / 1024).toFixed(1)} KB</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ISSUES TAB */}
            {activeTab === "issues" && (
              <div className="space-y-2.5">
                {issues.map((issue) => (
                  <div key={issue.id} className="flex items-start justify-between rounded-lg border border-neutral-800 bg-neutral-900/40 p-3.5 hover:border-neutral-700 transition-colors">
                    <div className="flex gap-2.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 mt-2 shrink-0"></span>
                      <div>
                        <h4 className="text-xs font-semibold text-white">{issue.title}</h4>
                        <div className="flex items-center gap-2.5 text-[11px] text-neutral-500 mt-1">
                          <span>#{issue.number} opened by {issue.user?.login}</span>
                          <span>•</span>
                          <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <span className="text-[11px] text-neutral-500 flex items-center gap-1 font-mono">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                      {issue.comments || 0}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* COMMITS TAB */}
            {activeTab === "commits" && (
              <div className="space-y-2.5">
                {commits.map((c) => (
                  <div key={c.sha} className="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-900/40 p-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="h-1.5 w-1.5 rounded-full bg-neutral-400"></div>
                      <div>
                        <p className="text-xs font-mono text-white">{c.commit.message}</p>
                        <p className="text-[11px] text-neutral-500 mt-0.5">{c.commit.author.name} committed on {new Date(c.commit.author.date).toLocaleString()}</p>
                      </div>
                    </div>
                    <span className="font-mono text-[11px] text-neutral-300 bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">{c.sha.substring(0, 7)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* PULL REQUESTS TAB */}
            {activeTab === "pulls" && (
              <div className="space-y-2.5">
                {pulls.map((pr) => (
                  <div key={pr.id} className="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-900/40 p-3.5">
                    <div className="flex items-center gap-2.5">
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
                      <div>
                        <h4 className="text-xs font-semibold text-white">{pr.title}</h4>
                        <p className="text-[11px] text-neutral-500 mt-0.5">#{pr.number} by {pr.user.login}</p>
                      </div>
                    </div>
                    <span className="text-[11px] px-2 py-0.5 rounded-full font-medium bg-neutral-900 text-neutral-300 border border-neutral-800">
                      {pr.state}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
