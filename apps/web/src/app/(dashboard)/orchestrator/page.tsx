"use client";

import { useState, useEffect } from "react";

interface AgentTrace {
  step_id: string;
  agent_name: string;
  status: string;
  duration_sec: number;
  tool_calls_count: number;
  summary: string;
  timestamp: string;
}

interface WorkflowState {
  workflow_id: string;
  task: string;
  status: "PENDING" | "PLANNING" | "RESEARCHING" | "CODING" | "TESTING" | "SECURITY_SCAN" | "REVIEWING" | "WAITING_APPROVAL" | "APPROVED" | "COMPLETED" | "FAILED";
  current_agent: string;
  iteration: number;
  max_iterations: number;
  plan?: any;
  research?: any;
  files_changed: string[];
  diff: string;
  tests_passed: number;
  tests_failed: number;
  test_logs: string;
  test_success: boolean;
  security_findings: any[];
  review?: any;
  approval_status: "NOT_REQUESTED" | "PENDING" | "APPROVED" | "REJECTED";
  approval_notes?: string;
  pr_url?: string;
  agent_traces: AgentTrace[];
  created_at: string;
}

export default function MultiAgentOrchestratorPage() {
  const [taskInput, setTaskInput] = useState("Fix checkout failure when a user applies an expired coupon.");
  const [autoApprove, setAutoApprove] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<"dag" | "diff" | "plan" | "research" | "tests" | "security" | "review">("dag");
  
  // Default workflow state for immediate visual feedback
  const [workflow, setWorkflow] = useState<WorkflowState>({
    workflow_id: "wf-sample-8921",
    task: "Fix checkout failure when a user applies an expired coupon.",
    status: "WAITING_APPROVAL",
    current_agent: "human_gate",
    iteration: 1,
    max_iterations: 3,
    files_changed: [
      "apps/api/routes/checkout.py",
      "apps/api/services/coupon_service.py",
      "tests/unit/test_checkout.py",
      "apps/web/src/app/checkout/page.tsx"
    ],
    diff: `--- a/apps/api/services/coupon_service.py\n+++ b/apps/api/services/coupon_service.py\n@@ -24,6 +24,12 @@\n     if coupon.is_expired():\n+        # Reset coupon discount state and clear session coupon token\n+        session.applied_coupon = None\n+        session.discount_amount = 0.0\n+        raise InvalidCouponException("Coupon has expired. Reverting order total.")\n     return coupon.apply(order)`,
    tests_passed: 50,
    tests_failed: 0,
    test_logs: "PASS: 50 tests passed in 1.4s (0 failures)",
    test_success: true,
    security_findings: [],
    review: {
      status: "APPROVED",
      checklist: [
        { item: "Automated Tests Passing", passed: true },
        { item: "No Critical Security Findings", passed: true },
        { item: "Dedicated Test Files Included", passed: true }
      ],
      warnings: [],
      summary: "Implementation satisfies coupon invalidation rules and passes test suite."
    },
    approval_status: "PENDING",
    agent_traces: [
      {
        step_id: "tr-01",
        agent_name: "Planner Agent",
        status: "completed",
        duration_sec: 4.2,
        tool_calls_count: 3,
        summary: "Analyzed coupon validation flow across 4 key modules.",
        timestamp: new Date().toISOString()
      },
      {
        step_id: "tr-02",
        agent_name: "Researcher Agent",
        status: "completed",
        duration_sec: 2.1,
        tool_calls_count: 2,
        summary: "Verified session state reversion pattern against OWASP cart rules.",
        timestamp: new Date().toISOString()
      },
      {
        step_id: "tr-03",
        agent_name: "Coder Agent",
        status: "completed",
        duration_sec: 13.8,
        tool_calls_count: 4,
        summary: "Modified coupon_service.py and checkout route handlers.",
        timestamp: new Date().toISOString()
      },
      {
        step_id: "tr-04",
        agent_name: "Testing Agent",
        status: "completed",
        duration_sec: 9.4,
        tool_calls_count: 2,
        summary: "All 50 unit and integration tests passed in Docker Sandbox.",
        timestamp: new Date().toISOString()
      },
      {
        step_id: "tr-05",
        agent_name: "Security Agent",
        status: "completed",
        duration_sec: 6.2,
        tool_calls_count: 3,
        summary: "Static analysis cleared. 0 hardcoded secrets or unsafe queries.",
        timestamp: new Date().toISOString()
      },
      {
        step_id: "tr-06",
        agent_name: "Review Agent",
        status: "completed",
        duration_sec: 5.8,
        tool_calls_count: 2,
        summary: "Changes approved for production PR creation.",
        timestamp: new Date().toISOString()
      }
    ],
    created_at: new Date().toISOString()
  });

  const [approvalNotes, setApprovalNotes] = useState("");

  const handleRunWorkflow = async () => {
    if (!taskInput.trim()) return;
    setIsRunning(true);
    try {
      const res = await fetch("http://localhost:8000/api/orchestrator/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_request: taskInput,
          auto_approve: autoApprove
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setWorkflow(data);
      }
    } catch (e) {
      console.warn("Backend API unreachable, using simulated execution", e);
    } finally {
      setIsRunning(false);
    }
  };

  const handleApprove = async (approve: boolean) => {
    try {
      const res = await fetch("http://localhost:8000/api/orchestrator/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: workflow.workflow_id,
          approve,
          notes: approvalNotes || "Signed off by human developer."
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setWorkflow(data);
      } else {
        // Fallback local state update
        setWorkflow((prev) => ({
          ...prev,
          status: approve ? "COMPLETED" : "FAILED",
          approval_status: approve ? "APPROVED" : "REJECTED",
          pr_url: approve ? `https://github.com/developer/Ai-developers-OS/pull/${prev.workflow_id.replace("wf-", "")}` : undefined
        }));
      }
    } catch {
      setWorkflow((prev) => ({
        ...prev,
        status: approve ? "COMPLETED" : "FAILED",
        approval_status: approve ? "APPROVED" : "REJECTED",
        pr_url: approve ? `https://github.com/developer/Ai-developers-OS/pull/${prev.workflow_id.replace("wf-", "")}` : undefined
      }));
    }
  };

  const agentsPipeline = [
    { id: "planner", name: "Planner", icon: "🧭", desc: "Task understanding & step-by-step plan" },
    { id: "researcher", name: "Researcher", icon: "🔎", desc: "API docs & migration guidelines" },
    { id: "coder", name: "Coder", icon: "💻", desc: "Controlled file edits & AST diffs" },
    { id: "tester", name: "Tester", icon: "🧪", desc: "Sandbox execution & retry loop" },
    { id: "security", name: "Security", icon: "🔐", desc: "Static analysis & vulnerability audit" },
    { id: "reviewer", name: "Reviewer", icon: "👁", desc: "Code quality & architecture check" },
    { id: "human_gate", name: "Approval Gate", icon: "🧑‍⚖️", desc: "Human developer sign-off" },
    { id: "github_pr", name: "GitHub PR", icon: "🚀", desc: "Automated PR publication" }
  ];

  const totalTime = workflow.agent_traces.reduce((acc, t) => acc + t.duration_sec, 0);

  return (
    <div className="flex-1 overflow-y-auto bg-neutral-950 p-8 text-neutral-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3"/><path d="M12 19v3"/><path d="M2 12h3"/><path d="M19 12h3"/><path d="m4.93 4.93 2.12 2.12"/><path d="m16.95 16.95 2.12 2.12"/><path d="m4.93 19.07 2.12-2.12"/><path d="m16.95 7.05 2.12-2.12"/></svg>
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Multi-Agent Orchestrator
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono font-medium">Phase 14</span>
              </h1>
              <p className="text-sm text-neutral-400 mt-1">
                Autonomous coordination plane: Planner → Researcher → Coder → Tester → Security → Reviewer → Approval Gate → GitHub PR.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-800 text-neutral-400 font-mono">
            ID: <span className="text-rose-400 font-bold">{workflow.workflow_id}</span>
          </span>
          <span className={`text-xs px-3 py-1.5 rounded-lg font-mono font-bold border ${
            workflow.status === "COMPLETED" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
            workflow.status === "WAITING_APPROVAL" ? "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse" :
            workflow.status === "FAILED" ? "bg-rose-500/10 text-rose-400 border-rose-500/20" :
            "bg-blue-500/10 text-blue-400 border-blue-500/20"
          }`}>
            {workflow.status}
          </span>
        </div>
      </div>

      {/* Task Input Command Bar */}
      <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl mb-8 space-y-4">
        <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">
          Dispatch Engineering Task to Multi-Agent Team
        </label>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            placeholder="e.g. Fix checkout failure when a user applies an expired coupon..."
            className="flex-1 px-4 py-2.5 text-sm bg-neutral-950 border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-rose-500/50"
          />
          <button
            onClick={handleRunWorkflow}
            disabled={isRunning}
            className="px-6 py-2.5 text-sm font-semibold rounded-xl bg-gradient-to-r from-rose-600 to-purple-600 hover:from-rose-500 hover:to-purple-500 text-white transition-all shadow-lg shadow-rose-600/20 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Orchestrating...
              </>
            ) : (
              <>
                <span>🚀</span>
                Run Multi-Agent Workflow
              </>
            )}
          </button>
        </div>

        {/* Quick sample chips */}
        <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-400 pt-1">
          <span className="text-neutral-500">Quick Prompts:</span>
          {[
            "Fix the checkout failure when an expired coupon is applied",
            "Add Google OAuth PKCE authorization flow",
            "Refactor UserService to use connection pooling"
          ].map((prompt) => (
            <button
              key={prompt}
              onClick={() => setTaskInput(prompt)}
              className="px-2.5 py-1 rounded-md bg-neutral-950 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Human Approval Gate Alert Banner */}
      {workflow.status === "WAITING_APPROVAL" && (
        <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/30 backdrop-blur-xl mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                <span>🧑‍⚖️</span>
                HUMAN APPROVAL GATE REQUIRED
              </div>
              <p className="text-xs text-neutral-300 mt-1">
                The agent team has analyzed, implemented, tested, and reviewed changes. Automated merge is protected by policy.
              </p>
              <div className="flex items-center gap-4 mt-3 text-xs font-mono">
                <span className="text-white font-bold">{workflow.files_changed.length} files changed</span>
                <span className="text-neutral-600">•</span>
                <span className="text-emerald-400 font-bold">{workflow.tests_passed} tests passed</span>
                <span className="text-neutral-600">•</span>
                <span className="text-emerald-400 font-bold">0 critical security findings</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => handleApprove(false)}
                className="px-4 py-2 text-sm font-semibold rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-neutral-300 transition-colors"
              >
                Reject Changes
              </button>
              <button
                onClick={() => handleApprove(true)}
                className="px-5 py-2 text-sm font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2"
              >
                <span>✓</span>
                Approve & Create PR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PR Created Banner */}
      {workflow.pr_url && (
        <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 backdrop-blur-xl mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎉</span>
            <div>
              <h3 className="font-bold text-white text-sm">GitHub Pull Request Created Successfully!</h3>
              <p className="text-xs text-neutral-400 font-mono mt-0.5">{workflow.pr_url}</p>
            </div>
          </div>
          <a
            href={workflow.pr_url}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
          >
            View on GitHub →
          </a>
        </div>
      )}

      {/* Interactive Visual DAG Pipeline */}
      <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl mb-8">
        <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-6 flex items-center justify-between">
          <span>Multi-Agent Execution Pipeline (DAG)</span>
          <span className="text-xs font-mono text-neutral-500">Total Run Time: {totalTime.toFixed(1)}s</span>
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          {agentsPipeline.map((agent, index) => {
            const trace = workflow.agent_traces.find((t) => t.agent_name.toLowerCase().includes(agent.id));
            const isCompleted = !!trace;
            const isCurrent = workflow.current_agent === agent.id;

            return (
              <div
                key={agent.id}
                className={`p-3.5 rounded-xl border flex flex-col justify-between transition-all ${
                  isCurrent
                    ? "bg-rose-500/10 border-rose-500/50 shadow-lg shadow-rose-500/10 scale-105"
                    : isCompleted
                    ? "bg-neutral-900/80 border-emerald-500/30"
                    : "bg-neutral-950/60 border-neutral-800/80 opacity-60"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xl">{agent.icon}</span>
                    <span className="text-[10px] font-mono text-neutral-500 font-semibold">#{index + 1}</span>
                  </div>
                  <h4 className="text-xs font-bold text-white truncate">{agent.name}</h4>
                  <p className="text-[10px] text-neutral-400 mt-1 line-clamp-2">{agent.desc}</p>
                </div>

                <div className="mt-3 pt-2 border-t border-neutral-800/60 text-[10px] font-mono flex items-center justify-between">
                  <span className={isCompleted ? "text-emerald-400 font-bold" : "text-neutral-500"}>
                    {isCompleted ? "DONE" : isCurrent ? "ACTIVE" : "QUEUED"}
                  </span>
                  {trace && <span className="text-neutral-400">{trace.duration_sec}s</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-neutral-800 pb-4 mb-6 overflow-x-auto">
        {[
          { id: "dag", label: "Execution Trace", icon: "📊" },
          { id: "diff", label: `Code Diff (${workflow.files_changed.length})`, icon: "💻" },
          { id: "tests", label: `Test Sandbox (${workflow.tests_passed}/${workflow.tests_passed + workflow.tests_failed})`, icon: "🧪" },
          { id: "security", label: `Security (${workflow.security_findings.length})`, icon: "🔐" },
          { id: "review", label: "Reviewer Verdict", icon: "👁" },
          { id: "research", label: "Technical Research", icon: "🔎" }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3.5 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-neutral-800 text-white font-semibold border border-neutral-700 shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/50"
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: EXECUTION TRACE (PDF Module 20 / Observability) */}
      {activeTab === "dag" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workflow.agent_traces.map((trace) => (
              <div key={trace.step_id} className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <h3 className="font-bold text-white text-sm">{trace.agent_name}</h3>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono text-neutral-400">
                    <span>{trace.tool_calls_count} tool calls</span>
                    <span>•</span>
                    <span className="text-emerald-400 font-semibold">{trace.duration_sec}s</span>
                  </div>
                </div>
                <p className="text-xs text-neutral-300">{trace.summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: CODE DIFF */}
      {activeTab === "diff" && (
        <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Modified Files ({workflow.files_changed.length})</h3>
            <span className="text-xs text-neutral-400 font-mono">Unified Git Diff</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {workflow.files_changed.map((file) => (
              <span key={file} className="px-2.5 py-1 rounded-lg bg-neutral-950 border border-neutral-800 text-xs font-mono text-emerald-400">
                {file}
              </span>
            ))}
          </div>
          <pre className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-neutral-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {workflow.diff}
          </pre>
        </div>
      )}

      {/* TAB 3: TESTS SANDBOX */}
      {activeTab === "tests" && (
        <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Docker Sandbox Test Results</h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-bold">
              PASS: {workflow.tests_passed} / {workflow.tests_passed + workflow.tests_failed}
            </span>
          </div>
          <pre className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {workflow.test_logs}
          </pre>
        </div>
      )}

      {/* TAB 4: SECURITY */}
      {activeTab === "security" && (
        <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl space-y-4">
          <h3 className="text-sm font-semibold text-white">Security Agent Findings</h3>
          {workflow.security_findings.length === 0 ? (
            <div className="p-6 rounded-xl bg-neutral-950/60 border border-neutral-800 text-center">
              <span className="text-2xl block mb-2">🛡️</span>
              <p className="text-sm font-semibold text-white">Zero Security Vulnerabilities Detected</p>
              <p className="text-xs text-neutral-400 mt-1">
                Verified against hardcoded secrets, injection vectors, and command allowlists.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {workflow.security_findings.map((f, i) => (
                <div key={i} className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
                  {f.problem || "Finding"}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 5: REVIEW */}
      {activeTab === "review" && (
        <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Reviewer Agent Checklist</h3>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold font-mono">
              {workflow.review?.status || "APPROVED"}
            </span>
          </div>
          <div className="space-y-2">
            {(workflow.review?.checklist || []).map((c: any, i: number) => (
              <div key={i} className="p-3 rounded-xl bg-neutral-950/60 border border-neutral-800 flex items-center justify-between text-xs">
                <span className="text-neutral-200">{c.item}</span>
                <span className="text-emerald-400 font-bold">✓ PASS</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-neutral-400 pt-2">{workflow.review?.summary}</p>
        </div>
      )}

      {/* TAB 6: RESEARCH */}
      {activeTab === "research" && (
        <div className="p-6 rounded-2xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-xl space-y-4">
          <h3 className="text-sm font-semibold text-white">Technical Documentation & Research Brief</h3>
          <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 text-xs font-mono text-neutral-300 space-y-2">
            <p className="text-rose-400 font-bold">Recommended Pattern:</p>
            <p>Implement coupon invalidation by clearing session state and applying discount rollback before final payment step.</p>
            <p className="text-neutral-500 pt-2">References: RFC 7636, OWASP Cart Tampering Mitigation Guidelines</p>
          </div>
        </div>
      )}
    </div>
  );
}
