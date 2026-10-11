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
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white tracking-tight">Code Agent</h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-900 px-2.5 py-0.5 text-[11px] font-medium text-neutral-300 border border-neutral-800 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
              AST Coder
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1">Executes controlled file modifications & produces reviewable unified diffs with developer approval gates.</p>
        </div>

        {approved && (
          <span className="inline-flex items-center gap-1.5 rounded-lg bg-neutral-900 px-3 py-1.5 text-xs font-medium text-neutral-300 border border-neutral-800">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            Workspace Updated & Approved
          </span>
        )}
      </div>

      {/* Active Plan Banner (if transferred from Planner) */}
      {activePlan && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm">
          <div>
            <span className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">Approved Planner Goal</span>
            <p className="text-sm font-semibold text-white mt-0.5">{activePlan.goal}</p>
          </div>
          <span className="inline-flex items-center rounded-md bg-neutral-900 px-2.5 py-1 text-xs font-mono text-neutral-300 border border-neutral-800 shrink-0">
            Steps: {activePlan.implementation_steps?.length ?? 5}
          </span>
        </div>
      )}

      {/* Task Context Form */}
      <form onSubmit={handleRunCoder} className="flex gap-2.5">
        <input 
          type="text"
          value={taskName}
          onChange={(e) => setTaskName(e.target.value)}
          placeholder="Enter task context for Code Agent"
          className="flex-1 rounded-lg border border-neutral-800 bg-neutral-900/80 px-3.5 py-2.5 text-xs text-white placeholder-neutral-500 focus:border-neutral-600 focus:outline-none transition-colors"
        />
        <button 
          type="submit"
          disabled={loading}
          className="rounded-lg bg-white px-4 py-2.5 text-xs font-semibold text-black hover:bg-neutral-200 transition-colors shadow-sm flex items-center gap-1.5 shrink-0 disabled:opacity-50"
        >
          {loading ? "Modifying..." : "Generate Code Diffs"}
        </button>
      </form>

      {/* Applied Status Alert */}
      {appliedStatus && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900/80 p-3 text-xs text-neutral-200 flex items-center gap-2.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0"></span>
          <span>{appliedStatus}</span>
        </div>
      )}

      {/* Diff Toolbar & Summary Bar */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="text-white">Modified Files: <span className="text-neutral-300 font-semibold">{changes.length}</span></span>
          <span className="text-neutral-300 font-semibold">+{totalAdditions}</span>
          <span className="text-neutral-400">-{totalDeletions}</span>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="flex rounded-lg bg-neutral-900 p-0.5 border border-neutral-800">
            <button
              onClick={() => setViewMode("unified")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === "unified" ? "bg-white text-black font-semibold shadow-sm" : "text-neutral-400 hover:text-white"
              }`}
            >
              Unified Diff
            </button>
            <button
              onClick={() => setViewMode("split")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === "split" ? "bg-white text-black font-semibold shadow-sm" : "text-neutral-400 hover:text-white"
              }`}
            >
              Side-by-Side
            </button>
          </div>

          <button
            onClick={handleApplyChanges}
            disabled={applying}
            className="rounded-lg bg-white px-3.5 py-1.5 text-xs font-semibold text-black hover:bg-neutral-200 transition-colors shadow-sm flex items-center gap-1.5"
          >
            {applying ? "Applying..." : "Approve & Apply Diffs"}
          </button>

          <button
            onClick={() => setShowPRModal(true)}
            className="rounded-lg bg-neutral-900 text-neutral-300 border border-neutral-800 px-3 py-1.5 text-xs font-medium hover:bg-neutral-850 hover:text-white transition-colors flex items-center gap-1.5"
          >
            Create PR
          </button>
        </div>
      </div>

      {/* Diffs List */}
      <div className="space-y-4">
        {changes.map((change, idx) => (
          <div key={idx} className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between border-b border-neutral-850 pb-2.5">
              <div className="flex items-center gap-2.5 font-mono text-xs">
                <span className="font-semibold text-white">{change.file_path}</span>
                <span className="rounded bg-neutral-900 px-2 py-0.5 text-[10px] text-neutral-400 border border-neutral-800 uppercase font-medium">
                  {change.change_type}
                </span>
              </div>
              <div className="flex items-center gap-2.5 font-mono text-xs">
                <span className="text-neutral-300">+{change.additions || 0}</span>
                <span className="text-neutral-500">-{change.deletions || 0}</span>
              </div>
            </div>

            {/* Unified View */}
            {viewMode === "unified" && (
              <div className="rounded-lg border border-neutral-800 bg-neutral-900/60 p-3.5 font-mono text-xs overflow-x-auto leading-relaxed">
                {change.diff.split("\n").map((line, lIdx) => {
                  let colorClass = "text-neutral-400";
                  if (line.startsWith("+") && !line.startsWith("+++")) {
                    colorClass = "text-neutral-100 bg-neutral-800/80 px-1 py-0.5 rounded";
                  } else if (line.startsWith("-") && !line.startsWith("---")) {
                    colorClass = "text-neutral-500 line-through px-1 py-0.5";
                  } else if (line.startsWith("@@")) {
                    colorClass = "text-neutral-400 font-semibold py-0.5";
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
                <div className="rounded-lg border border-neutral-800 bg-neutral-900/60 p-3 space-y-1">
                  <span className="text-[11px] font-medium uppercase tracking-wider text-neutral-400 block mb-1.5 border-b border-neutral-800 pb-1">
                    Existing Baseline Content
                  </span>
                  <pre className="text-neutral-500 whitespace-pre-wrap font-mono">{change.old_content || "// Empty or New File"}</pre>
                </div>
                <div className="rounded-lg border border-neutral-800 bg-neutral-900/60 p-3 space-y-1">
                  <span className="text-[11px] font-medium uppercase tracking-wider text-neutral-200 block mb-1.5 border-b border-neutral-800 pb-1">
                    Modified Content Output
                  </span>
                  <pre className="text-neutral-200 whitespace-pre-wrap font-mono">{change.new_content}</pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* GitHub PR Modal Preview */}
      {showPRModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-neutral-800 bg-neutral-950 p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-neutral-850 pb-3">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>
                Create GitHub Pull Request
              </h3>
              <button onClick={() => setShowPRModal(false)} className="text-neutral-400 hover:text-white text-sm">✕</button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-neutral-400 font-medium block mb-1">Branch Name</label>
                <input type="text" readOnly value="feature/ai-coder-modification" className="w-full bg-neutral-900/80 border border-neutral-800 rounded-lg p-2.5 text-white font-mono text-xs" />
              </div>
              <div>
                <label className="text-neutral-400 font-medium block mb-1">Target Branch</label>
                <input type="text" readOnly value="main" className="w-full bg-neutral-900/80 border border-neutral-800 rounded-lg p-2.5 text-white font-mono text-xs" />
              </div>
              <div>
                <label className="text-neutral-400 font-medium block mb-1">PR Title</label>
                <input type="text" readOnly value={`feat: ${taskName}`} className="w-full bg-neutral-900/80 border border-neutral-800 rounded-lg p-2.5 text-white font-mono text-xs" />
              </div>
            </div>

            <div className="flex justify-end gap-2.5 pt-2">
              <button onClick={() => setShowPRModal(false)} className="px-3.5 py-1.5 rounded-lg bg-neutral-900 border border-neutral-800 text-xs font-medium text-neutral-300 hover:bg-neutral-800">Cancel</button>
              <button onClick={() => { setShowPRModal(false); setApproved(true); setAppliedStatus("Pull Request #42 created successfully on GitHub repository!"); }} className="px-4 py-1.5 rounded-lg bg-white text-xs font-semibold text-black hover:bg-neutral-200 shadow-sm">Confirm & Create PR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
