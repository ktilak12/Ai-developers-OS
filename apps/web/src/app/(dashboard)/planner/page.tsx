"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface AffectedFileDetail {
  path: string;
  action: "CREATE" | "MODIFY" | string;
  line_count: number;
  est_changes: string;
}

interface StructuredStep {
  step: number;
  title: string;
  target_file: string;
  action: "READ" | "MODIFY" | "CREATE" | "EXECUTE" | "REVIEW" | string;
  description: string;
}

interface RiskItem {
  risk: string;
  severity: "HIGH" | "MEDIUM" | "LOW" | string;
  mitigation: string;
}

interface ContextSummary {
  rag_chunks_found: number;
  ast_symbols_matched: number;
  top_retrieved_files: string[];
  top_matched_symbols: string[];
}

interface RichPlanOutput {
  task_request: string;
  goal: string;
  requirements: string[];
  affected_files: string[];
  affected_files_detailed?: AffectedFileDetail[];
  implementation_steps: string[];
  structured_steps?: StructuredStep[];
  potential_risks: string[];
  risk_matrix?: RiskItem[];
  testing_requirements: string[];
  retrieved_context_summary?: ContextSummary;
  developer_approval_required?: boolean;
}

export default function PlannerAgentPage() {
  const router = useRouter();
  const [taskRequest, setTaskRequest] = useState("Add password reset functionality.");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"steps" | "files" | "risks" | "context">("steps");
  
  const [plan, setPlan] = useState<RichPlanOutput | null>({
    task_request: "Add password reset functionality.",
    goal: "Execute software update for: 'Add password reset functionality.'",
    requirements: [
      "Verify requirements for 'Add password reset functionality.' against codebase architecture.",
      "Ensure zero breaking changes to active endpoints or component states.",
      "Maintain dark theme design system styling (neutral-950 background, tailored glows).",
      "Require explicit developer approval gate before code merging or PR creation."
    ],
    affected_files: [
      "apps/web/src/app/login/page.tsx",
      "apps/api/main.py",
      "database/models/user.py"
    ],
    affected_files_detailed: [
      { path: "apps/web/src/app/login/page.tsx", action: "MODIFY", line_count: 142, est_changes: "+18 / -4" },
      { path: "apps/api/main.py", action: "MODIFY", line_count: 163, est_changes: "+24 / -6" },
      { path: "database/models/user.py", action: "CREATE", line_count: 0, est_changes: "+42 / -0" }
    ],
    implementation_steps: [
      "1. [READ] Inspect & Verify Dependencies: Analyze existing auth exports in apps/web/src/app/login/page.tsx.",
      "2. [MODIFY] Backend API Endpoint: Add POST /api/auth/reset-password in apps/api/main.py.",
      "3. [MODIFY] Frontend Integration: Add reset modal flow to apps/web/src/app/login/page.tsx.",
      "4. [EXECUTE] Docker Sandbox Verification: Execute unit test suite and TypeScript build check.",
      "5. [REVIEW] Developer Approval Gate: Generate unified diff for review before code application."
    ],
    structured_steps: [
      { step: 1, title: "Inspect & Verify Dependencies", target_file: "apps/web/src/app/login/page.tsx", action: "READ", description: "Analyze existing auth exports and AST symbols matching 'password reset' to establish baseline constraints." },
      { step: 2, title: "Backend API Endpoint Implementation", target_file: "apps/api/main.py", action: "MODIFY", description: "Add POST /api/auth/reset-password endpoint with token generation and email dispatch logic." },
      { step: 3, title: "Frontend State & Component Integration", target_file: "apps/web/src/app/login/page.tsx", action: "MODIFY", description: "Update login page with 'Forgot Password?' modal, token entry, and API call handlers." },
      { step: 4, title: "Docker Sandbox Test Execution", target_file: "tests/unit/test_agent.py", action: "EXECUTE", description: "Execute build verification (`npm run build`) and unit test suite inside isolated Docker container." },
      { step: 5, title: "Diff Generation & Developer Approval", target_file: "git / workspace", action: "REVIEW", description: "Generate clean unified diff output and pause workflow at developer approval gate before PR creation." }
    ],
    potential_risks: [
      "[HIGH] Token expiry window race conditions.",
      "[MEDIUM] Rate limiting password reset emails to prevent spam.",
      "[LOW] UI modal z-index clipping on small mobile viewports."
    ],
    risk_matrix: [
      { risk: "Token expiry window race conditions under concurrent requests.", severity: "HIGH", mitigation: "Use atomic database updates with indexed timestamp TTL validation." },
      { risk: "Rate limiting password reset emails to prevent enumeration attacks.", severity: "MEDIUM", mitigation: "Enforce IP rate limiters (max 3 reset attempts per hour per account)." },
      { risk: "UI modal z-index clipping on small mobile viewports.", severity: "LOW", mitigation: "Use absolute backdrop blur overlay with fixed inset z-50." }
    ],
    testing_requirements: [
      "Run `npm run build` to verify Next.js TypeScript strict compliance.",
      "Run `pytest` test suite to validate backend route contracts.",
      "Execute Docker Sandbox container run with resource limits."
    ],
    retrieved_context_summary: {
      rag_chunks_found: 8,
      ast_symbols_matched: 5,
      top_retrieved_files: ["apps/web/src/app/login/page.tsx", "apps/api/main.py"],
      top_matched_symbols: ["login_user", "verify_token", "create_planner_plan"]
    },
    developer_approval_required: true
  });

  const samplePrompts = [
    "Add password reset functionality.",
    "Refactor GitHub API rate limiting middleware.",
    "Integrate Docker Sandbox container runner."
  ];

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

  const handleApprovePlan = () => {
    if (plan) {
      if (typeof window !== "undefined") {
        localStorage.setItem("active_plan", JSON.stringify(plan));
      }
      router.push("/coder");
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case "READ":
        return <span className="rounded bg-blue-500/10 px-2 py-0.5 text-xs font-mono font-bold text-blue-400 border border-blue-500/20">READ</span>;
      case "MODIFY":
        return <span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs font-mono font-bold text-amber-400 border border-amber-500/20">MODIFY</span>;
      case "CREATE":
        return <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-xs font-mono font-bold text-emerald-400 border border-emerald-500/20">CREATE</span>;
      case "EXECUTE":
        return <span className="rounded bg-purple-500/10 px-2 py-0.5 text-xs font-mono font-bold text-purple-400 border border-purple-500/20">EXECUTE</span>;
      case "REVIEW":
        return <span className="rounded bg-cyan-500/10 px-2 py-0.5 text-xs font-mono font-bold text-cyan-400 border border-cyan-500/20">REVIEW</span>;
      default:
        return <span className="rounded bg-neutral-800 px-2 py-0.5 text-xs font-mono font-bold text-neutral-400">{action}</span>;
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "HIGH":
        return <span className="rounded bg-red-500/20 px-2.5 py-0.5 text-xs font-bold text-red-400 border border-red-500/30">HIGH RISK</span>;
      case "MEDIUM":
        return <span className="rounded bg-amber-500/20 px-2.5 py-0.5 text-xs font-bold text-amber-400 border border-amber-500/30">MEDIUM RISK</span>;
      case "LOW":
        return <span className="rounded bg-blue-500/20 px-2.5 py-0.5 text-xs font-bold text-blue-400 border border-blue-500/30">LOW RISK</span>;
      default:
        return <span className="rounded bg-neutral-800 px-2 py-0.5 text-xs font-bold text-neutral-300">{sev}</span>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-white tracking-tight">Planner Agent</h1>
          <span className="inline-flex items-center rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-400 border border-amber-500/20">
            Phase 5 Enhanced
          </span>
        </div>
        <p className="text-neutral-400 mt-1">
          Analyzes software requirements, queries RAG vector indexes & AST code intelligence, and generates safe, structured implementation plans.
        </p>
      </div>

      {/* Task Request Form & Sample Chips */}
      <div className="space-y-3">
        <form onSubmit={handleGeneratePlan}>
          <div className="relative">
            <input 
              type="text"
              value={taskRequest}
              onChange={(e) => setTaskRequest(e.target.value)}
              placeholder="Enter software task (e.g. 'Add password reset functionality.')"
              className="w-full rounded-2xl border border-neutral-800 bg-neutral-900/80 px-6 py-4 pl-12 pr-36 text-base text-white placeholder-neutral-500 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-2xl transition-colors"
            />
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-4 top-1/2 -translate-y-1/2 text-amber-400">
              <circle cx="12" cy="12" r="10"/>
              <polygon points="12 8 8 16 16 16 12 8"/>
            </svg>
            <button 
              type="submit"
              disabled={loading}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-amber-500 transition-all shadow-lg shadow-amber-950/40 disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Generate Plan"}
            </button>
          </div>
        </form>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-neutral-500 font-medium">Quick Tasks:</span>
          {samplePrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => setTaskRequest(prompt)}
              className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-1 text-neutral-400 hover:text-amber-400 hover:border-amber-500/40 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Main Plan Breakdown Card */}
      {plan && (
        <div className="space-y-6">
          {/* Goal & Requirements Banner */}
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/70 p-6 backdrop-blur-xl space-y-4 shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-800 pb-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">Implementation Goal</span>
                <h2 className="text-xl font-bold text-white mt-1">{plan.goal}</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center rounded-lg bg-neutral-950 px-3 py-1.5 text-xs font-mono text-neutral-300 border border-neutral-800">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 mr-2"></span>
                  RAG Chunks: {plan.retrieved_context_summary?.rag_chunks_found ?? 0}
                </span>
                <span className="inline-flex items-center rounded-lg bg-neutral-950 px-3 py-1.5 text-xs font-mono text-neutral-300 border border-neutral-800">
                  <span className="h-2 w-2 rounded-full bg-blue-400 mr-2"></span>
                  AST Symbols: {plan.retrieved_context_summary?.ast_symbols_matched ?? 0}
                </span>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Technical Requirements</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {plan.requirements.map((req, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs text-neutral-300 bg-neutral-950/60 p-2.5 rounded-lg border border-neutral-800/80">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400 shrink-0 mt-0.5"><polyline points="20 6 9 17 4 12"/></svg>
                    <span>{req}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-2 border-b border-neutral-800 pb-2">
            <button
              onClick={() => setActiveTab("steps")}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                activeTab === "steps"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Ordered Steps ({plan.structured_steps?.length ?? plan.implementation_steps.length})
            </button>
            <button
              onClick={() => setActiveTab("files")}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                activeTab === "files"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Affected Files ({plan.affected_files_detailed?.length ?? plan.affected_files.length})
            </button>
            <button
              onClick={() => setActiveTab("risks")}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                activeTab === "risks"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              Risk Assessment ({plan.risk_matrix?.length ?? plan.potential_risks.length})
            </button>
            <button
              onClick={() => setActiveTab("context")}
              className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
                activeTab === "context"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              RAG Context Inspector
            </button>
          </div>

          {/* Tab Contents */}
          {activeTab === "steps" && (
            <div className="space-y-3">
              {(plan.structured_steps || []).map((step, idx) => (
                <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 hover:border-neutral-700 transition-colors">
                  <div className="flex items-center justify-between gap-4 mb-2">
                    <div className="flex items-center gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/10 text-xs font-bold font-mono text-amber-400 border border-amber-500/20">
                        Step {step.step}
                      </span>
                      <h3 className="text-base font-bold text-white">{step.title}</h3>
                    </div>
                    {getActionBadge(step.action)}
                  </div>
                  <p className="text-sm text-neutral-300 mb-3">{step.description}</p>
                  <div className="flex items-center gap-2 text-xs font-mono text-neutral-400 bg-neutral-950 px-3 py-1.5 rounded-lg border border-neutral-800 w-fit">
                    <span className="text-neutral-500">Target File:</span>
                    <span className="text-amber-400">{step.target_file}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "files" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(plan.affected_files_detailed || []).map((file, idx) => (
                <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    {getActionBadge(file.action)}
                    <span className="text-xs font-mono text-emerald-400 font-medium">{file.est_changes}</span>
                  </div>
                  <div className="font-mono text-xs text-white break-all font-semibold bg-neutral-950 p-2.5 rounded-xl border border-neutral-800">
                    {file.path}
                  </div>
                  <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
                    <span>Baseline Lines: {file.line_count}</span>
                    <span>Status: Verified</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "risks" && (
            <div className="space-y-4">
              {(plan.risk_matrix || []).map((risk, idx) => (
                <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">{risk.risk}</span>
                    {getSeverityBadge(risk.severity)}
                  </div>
                  <div className="rounded-xl bg-neutral-950 p-3 border border-neutral-800/80 text-xs text-neutral-300">
                    <span className="font-semibold text-amber-400 uppercase tracking-wider block mb-1">Mitigation Strategy</span>
                    {risk.mitigation}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "context" && (
            <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6">
              <div>
                <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
                  Top RAG Vector Context Files
                </h3>
                <div className="space-y-1.5 font-mono text-xs">
                  {plan.retrieved_context_summary?.top_retrieved_files.map((f, i) => (
                    <div key={i} className="rounded-lg bg-neutral-950 px-3 py-2 text-neutral-300 border border-neutral-800">
                      {f}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                  Matched AST Code Intelligence Symbols
                </h3>
                <div className="flex flex-wrap gap-2 font-mono text-xs">
                  {plan.retrieved_context_summary?.top_matched_symbols.map((sym, i) => (
                    <span key={i} className="rounded-lg bg-blue-500/10 px-3 py-1 text-blue-400 border border-blue-500/20">
                      {sym}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Developer Approval Footer Bar */}
          <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-950/40 via-neutral-900 to-amber-950/40 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-2xl backdrop-blur-xl">
            <div>
              <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
                Developer Approval Gate Active
              </div>
              <p className="text-xs text-neutral-300 mt-1">
                Plan generated safely. Approve this implementation plan to transfer context directly to the Code Agent for execution.
              </p>
            </div>
            <button
              onClick={handleApprovePlan}
              className="rounded-xl bg-amber-500 px-6 py-3 text-sm font-bold text-neutral-950 hover:bg-amber-400 transition-all shadow-xl shadow-amber-950/60 shrink-0 flex items-center justify-center gap-2"
            >
              Approve Plan & Send to Coder Agent
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
