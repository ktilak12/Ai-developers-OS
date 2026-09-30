"use client";

import { useState } from "react";

interface PlanOutput {
  task_request: str;
  goal: str;
  requirements: string[];
  affected_files: string[];
  implementation_steps: string[];
  potential_risks: string[];
  testing_requirements: string[];
}

export default function PlannerAgentPage() {
  const [taskRequest, setTaskRequest] = useState("Add password reset functionality.");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<PlanOutput | null>({
    task_request: "Add password reset functionality.",
    goal: "Implement changes required for: Add password reset functionality.",
    requirements: [
      "Inspect auth configuration in apps/web/src/app/login/page.tsx.",
      "Ensure zero breaking changes to existing endpoints.",
      "Maintain dark theme design system conventions."
    ],
    affected_files: [
      "apps/web/src/app/login/page.tsx",
      "apps/api/main.py",
      "database/models/user.py"
    ],
    implementation_steps: [
      "Inspect authentication system and current login flow.",
      "Identify current user password hashing service.",
      "Add password reset token generation & email verification provider.",
      "Create POST /api/auth/reset-password endpoint.",
      "Update user database model with reset_token and token_expires_at.",
      "Update frontend login screen with 'Forgot password?' flow.",
      "Add unit and integration tests for password reset.",
      "Update documentation in docs/architecture.md."
    ],
    potential_risks: [
      "Token expiry window race conditions.",
      "Rate limiting password reset emails to prevent spam."
    ],
    testing_requirements: [
      "Run `npm run build` to verify TypeScript type checking.",
      "Run pytest test suite for password reset token API."
    ]
  });

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskRequest.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/agents/planner/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_request: taskRequest })
      });
      if (res.ok) {
        const data = await res.json();
        setPlan(data);
      }
    } catch (e) {
      console.log("Using local Planner Agent fallback output");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-white tracking-tight">Planner Agent</h1>
          <span className="inline-flex items-center rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-400 border border-amber-500/20">
            Phase 5 Active
          </span>
        </div>
        <p className="text-neutral-400 mt-1">Analyzes software tasks, inspects codebase context, and generates safe implementation plans before code execution.</p>
      </div>

      {/* Task Request Form */}
      <form onSubmit={handleGeneratePlan} className="mb-8">
        <div className="relative">
          <input 
            type="text"
            value={taskRequest}
            onChange={(e) => setTaskRequest(e.target.value)}
            placeholder="Enter software task (e.g. 'Add password reset functionality.')"
            className="w-full rounded-2xl border border-neutral-800 bg-neutral-900/80 px-6 py-4 pl-12 text-base text-white placeholder-neutral-500 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-2xl transition-colors"
          />
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-4 top-1/2 -translate-y-1/2 text-amber-400"><circle cx="12" cy="12" r="10"/><polygon points="12 8 8 16 16 16 12 8"/></svg>
          <button 
            type="submit"
            disabled={loading}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl bg-amber-600 px-5 py-2 text-sm font-semibold text-white hover:bg-amber-700 transition-colors shadow-lg shadow-amber-900/30"
          >
            {loading ? "Planning..." : "Generate Plan"}
          </button>
        </div>
      </form>

      {/* Structured Implementation Plan Card */}
      {plan && (
        <div className="space-y-8">
          {/* Goal & Requirements Banner */}
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6 backdrop-blur-xl">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-2">Implementation Goal</h3>
            <p className="text-xl font-bold text-white mb-4">{plan.goal}</p>

            <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Technical Requirements</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-neutral-300">
              {plan.requirements.map((req, i) => (
                <li key={i}>{req}</li>
              ))}
            </ul>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Implementation Steps */}
            <div className="lg:col-span-2 rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400"><line x1="10" y1="6" x2="21" y2="6"/><line x1="10" y1="12" x2="21" y2="12"/><line x1="10" y1="18" x2="21" y2="18"/><polyline points="3 6 4 7 6 5"/><polyline points="3 12 4 13 6 11"/><polyline points="3 18 4 19 6 17"/></svg>
                Ordered Implementation Steps ({plan.implementation_steps.length})
              </h3>
              <div className="space-y-3">
                {plan.implementation_steps.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-3 rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-xs font-bold font-mono text-amber-400 border border-amber-500/20">
                      {idx + 1}
                    </span>
                    <p className="text-sm text-neutral-300 pt-0.5">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Side Column: Affected Files, Risks & Testing */}
            <div className="space-y-6">
              {/* Affected Files */}
              <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>
                  Affected Files ({plan.affected_files.length})
                </h3>
                <div className="space-y-2 font-mono text-xs">
                  {plan.affected_files.map((file, i) => (
                    <div key={i} className="rounded-lg bg-neutral-950 px-3 py-2 text-neutral-300 border border-neutral-800 truncate">
                      {file}
                    </div>
                  ))}
                </div>
              </div>

              {/* Potential Risks */}
              <div className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2 text-amber-400">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  Potential Risks
                </h3>
                <ul className="list-disc list-inside space-y-1.5 text-xs text-neutral-400">
                  {plan.potential_risks.map((risk, i) => (
                    <li key={i}>{risk}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
