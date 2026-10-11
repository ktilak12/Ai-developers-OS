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
    return (
      <span className="rounded-md bg-neutral-900 px-2 py-0.5 text-[11px] font-mono font-medium text-neutral-300 border border-neutral-800">
        {action}
      </span>
    );
  };

  const getSeverityBadge = (sev: string) => {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-md bg-neutral-900 px-2 py-0.5 text-[11px] font-mono text-neutral-300 border border-neutral-800">
        <span className={`h-1.5 w-1.5 rounded-full ${sev === "HIGH" ? "bg-red-500" : sev === "MEDIUM" ? "bg-neutral-400" : "bg-neutral-600"}`}></span>
        {sev} RISK
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2.5">
          <h1 className="text-2xl font-bold text-white tracking-tight">Planner Agent</h1>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-900 px-2.5 py-0.5 text-[11px] font-medium text-neutral-300 border border-neutral-800 font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
            DAG Planner
          </span>
        </div>
        <p className="text-xs text-neutral-400 mt-1">
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
              className="w-full rounded-xl border border-neutral-800 bg-neutral-900/80 px-4 py-3 pl-10 pr-32 text-xs text-white placeholder-neutral-500 focus:border-neutral-600 focus:outline-none shadow-sm transition-colors"
            />
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400">
              <circle cx="12" cy="12" r="10"/>
              <polygon points="12 8 8 16 16 16 12 8"/>
            </svg>
            <button 
              type="submit"
              disabled={loading}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg bg-white px-3.5 py-1.5 text-xs font-semibold text-black hover:bg-neutral-200 transition-all shadow-sm disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Generate Plan"}
            </button>
          </div>
        </form>

        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-neutral-500 text-[11px]">Quick Tasks:</span>
          {samplePrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => setTaskRequest(prompt)}
              className="rounded-md border border-neutral-800 bg-neutral-900 px-2.5 py-1 text-[11px] text-neutral-300 hover:text-white hover:bg-neutral-800 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Main Plan Breakdown Card */}
      {plan && (
        <div className="space-y-5">
          {/* Goal & Requirements Banner */}
          <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 space-y-3.5 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-800/80 pb-3.5">
              <div>
                <span className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">Implementation Goal</span>
                <h2 className="text-base font-semibold text-white mt-0.5">{plan.goal}</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center rounded-md bg-neutral-900 px-2.5 py-1 text-xs font-mono text-neutral-300 border border-neutral-800">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-2"></span>
                  RAG Chunks: {plan.retrieved_context_summary?.rag_chunks_found ?? 0}
                </span>
                <span className="inline-flex items-center rounded-md bg-neutral-900 px-2.5 py-1 text-xs font-mono text-neutral-300 border border-neutral-800">
                  <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 mr-2"></span>
                  AST Symbols: {plan.retrieved_context_summary?.ast_symbols_matched ?? 0}
                </span>
              </div>
            </div>

            <div>
              <h4 className="text-[11px] font-medium uppercase tracking-wider text-neutral-400 mb-2">Technical Requirements</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {plan.requirements.map((req, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-neutral-300 bg-neutral-900/50 p-2.5 rounded-lg border border-neutral-800">
                    <span className="text-neutral-500 mt-0.5">&bull;</span>
                    <span>{req}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1.5 border-b border-neutral-800 pb-2.5">
            <button
              onClick={() => setActiveTab("steps")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "steps"
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`}
            >
              Ordered Steps ({plan.structured_steps?.length ?? plan.implementation_steps.length})
            </button>
            <button
              onClick={() => setActiveTab("files")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "files"
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`}
            >
              Affected Files ({plan.affected_files_detailed?.length ?? plan.affected_files.length})
            </button>
            <button
              onClick={() => setActiveTab("risks")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "risks"
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`}
            >
              Risk Assessment ({plan.risk_matrix?.length ?? plan.potential_risks.length})
            </button>
            <button
              onClick={() => setActiveTab("context")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "context"
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`}
            >
              RAG Context Inspector
            </button>
          </div>

          {/* Tab Contents */}
          {activeTab === "steps" && (
            <div className="space-y-2.5">
              {(plan.structured_steps || []).map((step, idx) => (
                <div key={idx} className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 hover:border-neutral-700 transition-colors">
                  <div className="flex items-center justify-between gap-4 mb-1.5">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-neutral-900 text-[11px] font-mono text-neutral-300 border border-neutral-800">
                        {step.step}
                      </span>
                      <h3 className="text-xs font-semibold text-white">{step.title}</h3>
                    </div>
                    {getActionBadge(step.action)}
                  </div>
                  <p className="text-xs text-neutral-300 mb-2.5">{step.description}</p>
                  <div className="flex items-center gap-2 text-[11px] font-mono text-neutral-400 bg-neutral-900/60 px-2.5 py-1 rounded-md border border-neutral-800 w-fit">
                    <span className="text-neutral-500">Target:</span>
                    <span className="text-neutral-200">{step.target_file}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "files" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(plan.affected_files_detailed || []).map((file, idx) => (
                <div key={idx} className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    {getActionBadge(file.action)}
                    <span className="text-[11px] font-mono text-neutral-300">{file.est_changes}</span>
                  </div>
                  <div className="font-mono text-xs text-neutral-200 break-all bg-neutral-900/80 p-2 rounded-lg border border-neutral-800">
                    {file.path}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-400 pt-0.5">
                    <span>Lines: {file.line_count}</span>
                    <span>Verified</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "risks" && (
            <div className="space-y-3">
              {(plan.risk_matrix || []).map((risk, idx) => (
                <div key={idx} className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white">{risk.risk}</span>
                    {getSeverityBadge(risk.severity)}
                  </div>
                  <div className="rounded-lg bg-neutral-900/70 p-2.5 border border-neutral-800 text-xs text-neutral-300">
                    <span className="font-medium text-neutral-400 uppercase tracking-wider block mb-0.5 text-[10px]">Mitigation</span>
                    {risk.mitigation}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "context" && (
            <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 space-y-5">
              <div>
                <h3 className="text-xs font-semibold text-white mb-2 flex items-center gap-2">
                  Top RAG Vector Context Files
                </h3>
                <div className="space-y-1.5 font-mono text-xs">
                  {plan.retrieved_context_summary?.top_retrieved_files.map((f, i) => (
                    <div key={i} className="rounded-lg bg-neutral-900/70 px-3 py-1.5 text-neutral-300 border border-neutral-800">
                      {f}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-semibold text-white mb-2 flex items-center gap-2">
                  Matched AST Code Intelligence Symbols
                </h3>
                <div className="flex flex-wrap gap-1.5 font-mono text-xs">
                  {plan.retrieved_context_summary?.top_matched_symbols.map((sym, i) => (
                    <span key={i} className="rounded-md bg-neutral-900 px-2.5 py-1 text-neutral-300 border border-neutral-800">
                      {sym}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Developer Approval Footer Bar */}
          <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
            <div>
              <div className="flex items-center gap-2 text-neutral-200 font-semibold text-xs uppercase tracking-wider">
                <span className="h-2 w-2 rounded-full bg-white"></span>
                Developer Approval Gate
              </div>
              <p className="text-xs text-neutral-400 mt-1">
                Plan generated safely. Approve this implementation plan to transfer context directly to the Code Agent.
              </p>
            </div>
            <button
              onClick={handleApprovePlan}
              className="rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black hover:bg-neutral-200 transition-all shadow-sm shrink-0 flex items-center justify-center gap-2"
            >
              Approve & Send to Coder Agent
              <span>&rarr;</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
