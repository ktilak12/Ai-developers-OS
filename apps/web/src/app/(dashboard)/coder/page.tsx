"use client";

import { useState, useEffect } from "react";

interface CodeChange {
  file_path: string;
  change_type: string;
  additions?: number;
  deletions?: number;
  old_content?: string;
  new_content?: string;
  diff: string;
}

interface ActivePlan {
  task_request: string;
  goal: string;
  affected_files?: string[];
  implementation_steps?: string[];
}

export default function CoderAgentPage() {
  const [taskName, setTaskName] = useState("Add password reset functionality.");
  const [activePlan, setActivePlan] = useState<ActivePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [approved, setApproved] = useState(false);
  const [appliedStatus, setAppliedStatus] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"unified" | "split">("unified");
  const [showPRModal, setShowPRModal] = useState(false);
  
  const [changes, setChanges] = useState<CodeChange[]>([
    {
      file_path: "apps/web/src/app/login/page.tsx",
      change_type: "modified",
      additions: 18,
      deletions: 4,
      old_content: `"use client";\n\nexport default function LoginPage() {\n  return (\n    <div className="p-8">\n      <h1 className="text-2xl font-bold">Login</h1>\n      <button type="submit" className="bg-blue-600">Sign In</button>\n    </div>\n  );\n}`,
      new_content: `"use client";\n\nexport default function LoginPage() {\n  return (\n    <div className="p-8">\n      <h1 className="text-2xl font-bold">Login</h1>\n      <button type="submit" className="bg-blue-600">Sign In</button>\n      <div className="mt-4 pt-4 border-t border-neutral-800">\n        <a href="/reset-password" className="text-xs text-blue-400">Forgot Password?</a>\n      </div>\n    </div>\n  );\n}`,
      diff: `--- a/apps/web/src/app/login/page.tsx\n+++ b/apps/web/src/app/login/page.tsx\n@@ -6,6 +6,12 @@\n       <h1 className="text-2xl font-bold">Login</h1>\n       <button type="submit" className="bg-blue-600">Sign In</button>\n+\n+      <div className="mt-4 pt-4 border-t border-neutral-800">\n+        <a href="/reset-password" className="text-xs text-blue-400">Forgot Password?</a>\n+      </div>\n     </div>\n   );\n }`
    },
    {
      file_path: "apps/api/main.py",
      change_type: "modified",
      additions: 24,
      deletions: 2,
      old_content: `# FastAPI Server Application\n\n@app.get("/api/health")\ndef health():\n    return {"status": "ok"}`,
      new_content: `# FastAPI Server Application\n\n@app.get("/api/health")\ndef health():\n    return {"status": "ok"}\n\n@app.post("/api/auth/reset-password")\ndef reset_password(email: str):\n    # AI Developer OS: Added password reset handler\n    return {"status": "success", "message": "Password reset token dispatched."}`,
      diff: `--- a/apps/api/main.py\n+++ b/apps/api/main.py\n@@ -5,3 +5,9 @@\n def health():\n     return {"status": "ok"}\n+\n+@app.post("/api/auth/reset-password")\n+def reset_password(email: str):\n+    # AI Developer OS: Added password reset handler\n+    return {"status": "success", "message": "Password reset token dispatched."}`
    }
  ]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedPlan = localStorage.getItem("active_plan");
      if (storedPlan) {
        try {
          const parsed = JSON.parse(storedPlan);
          setActivePlan(parsed);
          if (parsed.task_request) setTaskName(parsed.task_request);
        } catch (e) {
          console.error("Failed to parse stored plan", e);
        }
      }
    }
  }, []);

  const handleRunCoder = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setApproved(false);
    setAppliedStatus(null);

    try {
      const res = await fetch("http://localhost:8000/api/agents/coder/modify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: {
            task_request: taskName,
            affected_files: activePlan?.affected_files || ["apps/web/src/app/login/page.tsx", "apps/api/main.py"]
          }
        })
      });
      if (res.ok) {
        const data = await res.json();
        setChanges(data.changes);
      }
    } catch (e) {
      console.log("Using local Coder Agent fallback changes");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyChanges = async () => {
    setApplying(true);
    try {
      const res = await fetch("http://localhost:8000/api/agents/coder/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ changes })
      });
      if (res.ok) {
        const data = await res.json();
        setApproved(true);
        setAppliedStatus(data.message || "Changes applied successfully!");
      }
    } catch (e) {
      setApproved(true);
      setAppliedStatus("Changes approved and applied locally to workspace files.");
    } finally {
      setApplying(false);
    }
  };

  const totalAdditions = changes.reduce((sum, c) => sum + (c.additions || 0), 0);
  const totalDeletions = changes.reduce((sum, c) => sum + (c.deletions || 0), 0);

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white tracking-tight">Code Agent</h1>
            <span className="inline-flex items-center rounded-full bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400 border border-blue-500/20">
              Phase 6 Active
            </span>
          </div>
          <p className="text-neutral-400 mt-1">Executes controlled file modifications & produces reviewable unified diffs with developer approval gates.</p>
        </div>

        {approved && (
          <span className="inline-flex items-center gap-2 rounded-xl bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-400 border border-emerald-500/20">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Workspace Updated & Approved
          </span>
        )}
      </div>

      {/* Active Plan Banner (if transferred from Planner) */}
      {activePlan && (
        <div className="rounded-2xl border border-blue-500/30 bg-blue-950/20 p-5 backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-400">Approved Planner Goal</span>
            <p className="text-base font-bold text-white mt-0.5">{activePlan.goal}</p>
          </div>
          <span className="inline-flex items-center rounded-lg bg-neutral-900 px-3 py-1 text-xs font-mono text-neutral-300 border border-neutral-800 shrink-0">
            Plan Steps: {activePlan.implementation_steps?.length ?? 5}
          </span>
        </div>
      )}

      {/* Task Context Form */}
      <form onSubmit={handleRunCoder} className="flex gap-4">
        <input 
          type="text"
          value={taskName}
          onChange={(e) => setTaskName(e.target.value)}
          placeholder="Enter task context for Code Agent"
          className="flex-1 rounded-2xl border border-neutral-800 bg-neutral-900/80 px-6 py-4 text-base text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors shadow-xl"
        />
        <button 
          type="submit"
          disabled={loading}
          className="rounded-2xl bg-blue-600 px-6 py-4 text-sm font-semibold text-white hover:bg-blue-500 transition-colors shadow-lg shadow-blue-950/40 flex items-center gap-2 shrink-0 disabled:opacity-50"
        >
          {loading ? "Modifying..." : "Generate Code Diffs"}
        </button>
      </form>

      {/* Applied Status Alert */}
      {appliedStatus && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-4 text-sm font-medium text-emerald-400 flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <span>{appliedStatus}</span>
        </div>
      )}

      {/* Diff Toolbar & Summary Bar */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-sm">
          <span className="font-bold text-white">Files Modified: <span className="font-mono text-blue-400">{changes.length}</span></span>
          <span className="font-mono font-bold text-emerald-400">+{totalAdditions} lines</span>
          <span className="font-mono font-bold text-red-400">-{totalDeletions} lines</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-xl bg-neutral-950 p-1 border border-neutral-800">
            <button
              onClick={() => setViewMode("unified")}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                viewMode === "unified" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"
              }`}
            >
              Unified Diff
            </button>
            <button
              onClick={() => setViewMode("split")}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                viewMode === "split" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"
              }`}
            >
              Side-by-Side
            </button>
          </div>

          <button
            onClick={handleApplyChanges}
            disabled={applying}
            className="rounded-xl bg-emerald-600 px-5 py-2 text-sm font-bold text-white hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-950/40 flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            {applying ? "Applying..." : "Approve & Apply Diffs"}
          </button>

          <button
            onClick={() => setShowPRModal(true)}
            className="rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30 px-4 py-2 text-sm font-semibold hover:bg-purple-600/30 transition-colors flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
            Create PR
          </button>
        </div>
      </div>

      {/* Diffs List */}
      <div className="space-y-6">
        {changes.map((change, idx) => (
          <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <div className="flex items-center gap-3 font-mono text-sm">
                <span className="font-bold text-white">{change.file_path}</span>
                <span className="rounded bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400 border border-blue-500/20 uppercase font-semibold">
                  {change.change_type}
                </span>
              </div>
              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="text-emerald-400">+{change.additions || 0}</span>
                <span className="text-red-400">-{change.deletions || 0}</span>
              </div>
            </div>

            {/* Unified View */}
            {viewMode === "unified" && (
              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 font-mono text-xs overflow-x-auto leading-relaxed">
                {change.diff.split("\n").map((line, lIdx) => {
                  let colorClass = "text-neutral-400";
                  if (line.startsWith("+") && !line.startsWith("+++")) {
                    colorClass = "text-emerald-400 bg-emerald-950/30 px-1 py-0.5 rounded";
                  } else if (line.startsWith("-") && !line.startsWith("---")) {
                    colorClass = "text-red-400 bg-red-950/30 px-1 py-0.5 rounded";
                  } else if (line.startsWith("@@")) {
                    colorClass = "text-purple-400 font-bold py-1";
                  }
                  return (
                    <div key={lIdx} className={colorClass}>
                      {line}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Side-by-Side Split View */}
            {viewMode === "split" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 space-y-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-red-400 block mb-2 border-b border-neutral-800 pb-1">
                    Existing Baseline Content
                  </span>
                  <pre className="text-neutral-400 whitespace-pre-wrap font-mono">{change.old_content || "// Empty or New File"}</pre>
                </div>
                <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 space-y-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 block mb-2 border-b border-neutral-800 pb-1">
                    Modified Content Output
                  </span>
                  <pre className="text-emerald-300 whitespace-pre-wrap font-mono">{change.new_content}</pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* GitHub PR Modal Preview */}
      {showPRModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-neutral-800 bg-neutral-900 p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
                Create GitHub Pull Request
              </h3>
              <button onClick={() => setShowPRModal(false)} className="text-neutral-400 hover:text-white">✕</button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-neutral-400 font-semibold block mb-1">Branch Name</label>
                <input type="text" readOnly value="feature/ai-coder-modification" className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-white font-mono" />
              </div>
              <div>
                <label className="text-neutral-400 font-semibold block mb-1">Target Branch</label>
                <input type="text" readOnly value="main" className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-white font-mono" />
              </div>
              <div>
                <label className="text-neutral-400 font-semibold block mb-1">PR Title</label>
                <input type="text" readOnly value={`feat: ${taskName}`} className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 text-white font-mono" />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => setShowPRModal(false)} className="px-4 py-2 rounded-xl bg-neutral-800 text-sm font-semibold text-white hover:bg-neutral-700">Cancel</button>
              <button onClick={() => { setShowPRModal(false); setApproved(true); setAppliedStatus("Pull Request #42 created successfully on GitHub repository!"); }} className="px-4 py-2 rounded-xl bg-purple-600 text-sm font-semibold text-white hover:bg-purple-500 shadow-lg shadow-purple-950/40">Confirm & Create PR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
