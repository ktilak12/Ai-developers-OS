"use client";

import { useState } from "react";

interface CodeChange {
  file_path: string;
  change_type: string;
  diff: string;
}

export default function CoderAgentPage() {
  const [taskName, setTaskName] = useState("Add password reset functionality.");
  const [loading, setLoading] = useState(false);
  const [approved, setApproved] = useState(false);
  
  const [changes, setChanges] = useState<CodeChange[]>([
    {
      file_path: "apps/web/src/app/login/page.tsx",
      change_type: "modified",
      diff: `--- a/apps/web/src/app/login/page.tsx\n+++ b/apps/web/src/app/login/page.tsx\n@@ -38,6 +38,12 @@\n           </div>\n           <div className="pt-2">\n             <button type="submit" className="w-full bg-blue-600">Sign In</button>\n           </div>\n         </form>\n+\n+        <div className="mt-4 border-t border-neutral-800 pt-4">\n+          <a href="/reset-password" className="text-xs text-blue-400 hover:underline">\n+            Forgot your password? Reset here.\n+          </a>\n+        </div>`
    },
    {
      file_path: "apps/api/main.py",
      change_type: "modified",
      diff: `--- a/apps/api/main.py\n+++ b/apps/api/main.py\n@@ -88,3 +88,9 @@\n @app.post("/api/auth/reset-password")\n async def reset_password(email: str):\n+    # AI Developer OS: Added password reset handler\n+    return {"status": "success", "message": "Password reset token dispatched."}`
    }
  ]);

  const handleRunCoder = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setApproved(false);

    try {
      const res = await fetch("http://localhost:8000/api/agents/coder/modify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: {
            task_request: taskName,
            affected_files: ["apps/web/src/app/login/page.tsx", "apps/api/main.py"]
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

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white tracking-tight">Code Agent</h1>
            <span className="inline-flex items-center rounded-full bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400 border border-blue-500/20">
              Phase 6 Active
            </span>
          </div>
          <p className="text-neutral-400 mt-1">Executes controlled file modifications & generates unified git diffs for human developer approval.</p>
        </div>

        {approved && (
          <span className="inline-flex items-center gap-2 rounded-xl bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-400 border border-emerald-500/20">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            Changes Approved by Developer
          </span>
        )}
      </div>

      {/* Trigger Form */}
      <form onSubmit={handleRunCoder} className="mb-8 flex gap-4">
        <input 
          type="text"
          value={taskName}
          onChange={(e) => setTaskName(e.target.value)}
          placeholder="Task context for Coder Agent"
          className="flex-1 rounded-2xl border border-neutral-800 bg-neutral-900/80 px-6 py-4 text-base text-white placeholder-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
        />
        <button 
          type="submit"
          disabled={loading}
          className="rounded-2xl bg-blue-600 px-6 py-4 text-sm font-semibold text-white hover:bg-blue-700 transition-colors shadow-lg shadow-blue-900/30 flex items-center gap-2"
        >
          {loading ? "Modifying Code..." : "Execute Coder Agent"}
        </button>
      </form>

      {/* Diffs List */}
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Generated Unified Diffs ({changes.length} files)</h2>
          {!approved && (
            <button 
              onClick={() => setApproved(true)}
              className="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-900/30 flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              Approve Changes
            </button>
          )}
        </div>

        {changes.map((change, idx) => (
          <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-semibold text-white">{change.file_path}</span>
                <span className="text-xs text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20 font-mono">
                  {change.change_type}
                </span>
              </div>
            </div>

            {/* Styled Diff Container */}
            <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 font-mono text-xs overflow-x-auto leading-relaxed">
              {change.diff.split("\n").map((line, lIdx) => {
                let colorClass = "text-neutral-400";
                if (line.startsWith("+") && !line.startsWith("+++")) {
                  colorClass = "text-emerald-400 bg-emerald-950/30 px-1 py-0.5 rounded";
                } else if (line.startsWith("-") && !line.startsWith("---")) {
                  colorClass = "text-red-400 bg-red-950/30 px-1 py-0.5 rounded";
                } else if (line.startsWith("@@")) {
                  colorClass = "text-purple-400 font-bold";
                }
                return (
                  <div key={lIdx} className={colorClass}>
                    {line}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
