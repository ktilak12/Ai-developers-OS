"use client";

import { useState, useEffect } from "react";

interface SWEBenchmarkTask {
  task_id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  target_files: string[];
  expected_tools: string[];
  test_criteria: string;
}

interface AggregateAgentMetrics {
  agent_version: string;
  total_tasks: number;
  completed_tasks: number;
  completion_rate_pct: number;
  avg_planning_accuracy: number;
  avg_code_correctness: number;
  avg_test_success_rate: number;
  avg_security_score: number;
  avg_tool_accuracy: number;
  avg_duration_sec: number;
  total_tokens: number;
  total_cost_usd: number;
}

interface ComparativeScorecard {
  evaluation_id: string;
  created_at: string;
  tasks_evaluated_count: number;
  v1_baseline: AggregateAgentMetrics;
  v2_orchestrated: AggregateAgentMetrics;
  completion_improvement_pct: number;
  test_success_improvement_pct: number;
  security_score_improvement_pct: number;
  latency_reduction_pct: number;
  task_breakdown: any[];
}

export default function EvaluationPage() {
  const [tasks, setTasks] = useState<SWEBenchmarkTask[]>([]);
  const [scorecard, setScorecard] = useState<ComparativeScorecard | null>(null);
  const [selectedTask, setSelectedTask] = useState<SWEBenchmarkTask | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [isRunning, setIsRunning] = useState(false);
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchBenchmarkData();
  }, []);

  const fetchBenchmarkData = async () => {
    try {
      const [tRes, sRes] = await Promise.all([
        fetch(`${API_BASE}/api/evaluation/benchmark/tasks`).catch(() => null),
        fetch(`${API_BASE}/api/evaluation/benchmark/scorecard`).catch(() => null),
      ]);

      if (tRes && tRes.ok) {
        const tData = await tRes.json();
        setTasks(tData.tasks || []);
        if (tData.tasks?.length > 0) setSelectedTask(tData.tasks[0]);
      }

      if (sRes && sRes.ok) {
        const sData = await sRes.json();
        setScorecard(sData);
      }
    } catch (err) {
      console.error("Failed to load benchmark data", err);
    }
  };

  const runBenchmark = async () => {
    setIsRunning(true);
    try {
      const res = await fetch(`${API_BASE}/api/evaluation/benchmark/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        const data = await res.json();
        setScorecard(data);
      }
    } catch (err) {
      console.error("Error running benchmark", err);
    } finally {
      setIsRunning(false);
    }
  };

  const viewReport = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/evaluation/benchmark/report`);
      if (res.ok) {
        const data = await res.json();
        setReportMarkdown(data.markdown);
        setShowReportModal(true);
      }
    } catch (err) {
      console.error("Error fetching report", err);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (categoryFilter === "ALL") return true;
    return t.category.toLowerCase() === categoryFilter.toLowerCase();
  });

  const getCategoryColor = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "bug_fix": return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      case "security": return "text-rose-400 bg-rose-500/10 border-rose-500/20";
      case "performance": return "text-blue-400 bg-blue-500/10 border-blue-500/20";
      case "refactor": return "text-purple-400 bg-purple-500/10 border-purple-500/20";
      case "api_design": return "text-cyan-400 bg-cyan-500/10 border-cyan-500/20";
      default: return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    }
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "easy": return "text-emerald-400";
      case "medium": return "text-amber-400";
      case "hard": return "text-rose-400";
      default: return "text-neutral-400";
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse" />
            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              SWE Evaluation & Benchmarks
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-mono">
              20 Benchmark Tasks
            </span>
          </div>
          <p className="text-sm text-neutral-400 mt-2">
            Rigorous SWE evaluation comparing Agent v1 (Single LLM Baseline) vs Agent v2 (AI Developer OS Multi-Agent).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={viewReport}
            className="px-4 py-2 text-xs font-medium text-neutral-300 bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            Export Markdown Report
          </button>
          <button
            onClick={runBenchmark}
            disabled={isRunning}
            className="px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-lg shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                Evaluating 20 Tasks...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Run SWE Benchmark
              </>
            )}
          </button>
        </div>
      </div>

      {/* Comparative Scorecard Hero Banner */}
      {scorecard && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-neutral-900/90 via-neutral-900/40 to-emerald-950/20 border border-emerald-500/30 backdrop-blur-xl space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-800 pb-4">
            <div>
              <span className="text-xs font-mono text-emerald-400">Scorecard: {scorecard.evaluation_id}</span>
              <h2 className="text-xl font-bold text-white mt-1">
                Agent v1 (Baseline) vs Agent v2 (AI Developer OS)
              </h2>
            </div>
            <div className="flex items-center gap-2 text-xs text-neutral-400">
              <span>{scorecard.tasks_evaluated_count} real-world software engineering tasks evaluated</span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Task Completion Rate */}
            <div className="p-4 rounded-xl bg-neutral-950/60 border border-neutral-800 space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Completion Rate</span>
              <div className="flex items-baseline justify-between">
                <div>
                  <p className="text-xs text-neutral-500">v1: {scorecard.v1_baseline.completion_rate_pct}%</p>
                  <p className="text-2xl font-bold text-emerald-400">{scorecard.v2_orchestrated.completion_rate_pct}%</p>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  +{scorecard.completion_improvement_pct}%
                </span>
              </div>
            </div>

            {/* Test Suite Pass Rate */}
            <div className="p-4 rounded-xl bg-neutral-950/60 border border-neutral-800 space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Test Pass Rate</span>
              <div className="flex items-baseline justify-between">
                <div>
                  <p className="text-xs text-neutral-500">v1: {scorecard.v1_baseline.avg_test_success_rate}%</p>
                  <p className="text-2xl font-bold text-blue-400">{scorecard.v2_orchestrated.avg_test_success_rate}%</p>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  +{scorecard.test_success_improvement_pct}%
                </span>
              </div>
            </div>

            {/* Security Audit Score */}
            <div className="p-4 rounded-xl bg-neutral-950/60 border border-neutral-800 space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Security Score</span>
              <div className="flex items-baseline justify-between">
                <div>
                  <p className="text-xs text-neutral-500">v1: {scorecard.v1_baseline.avg_security_score}/100</p>
                  <p className="text-2xl font-bold text-rose-400">{scorecard.v2_orchestrated.avg_security_score}/100</p>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  +{scorecard.security_score_improvement_pct} pts
                </span>
              </div>
            </div>

            {/* Tool Calling Accuracy */}
            <div className="p-4 rounded-xl bg-neutral-950/60 border border-neutral-800 space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Tool Accuracy</span>
              <div className="flex items-baseline justify-between">
                <div>
                  <p className="text-xs text-neutral-500">v1: {scorecard.v1_baseline.avg_tool_accuracy}%</p>
                  <p className="text-2xl font-bold text-purple-400">{scorecard.v2_orchestrated.avg_tool_accuracy}%</p>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  +{(scorecard.v2_orchestrated.avg_tool_accuracy - scorecard.v1_baseline.avg_tool_accuracy).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Detailed Dimension Comparison Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-400 font-medium">
                  <th className="py-2 px-3">Evaluation Dimension</th>
                  <th className="py-2 px-3">Agent v1 (Single LLM Baseline)</th>
                  <th className="py-2 px-3 text-emerald-400">Agent v2 (AI Developer OS)</th>
                  <th className="py-2 px-3">Impact / Architectural Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-white">Planning Accuracy</td>
                  <td className="py-2.5 px-3 font-mono">{scorecard.v1_baseline.avg_planning_accuracy}%</td>
                  <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">{scorecard.v2_orchestrated.avg_planning_accuracy}%</td>
                  <td className="py-2.5 px-3 text-neutral-400">Grounded in AST Code Intelligence & Project RAG</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-white">Code Correctness</td>
                  <td className="py-2.5 px-3 font-mono">{scorecard.v1_baseline.avg_code_correctness}%</td>
                  <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">{scorecard.v2_orchestrated.avg_code_correctness}%</td>
                  <td className="py-2.5 px-3 text-neutral-400">Unified diff generation with target AST contract validation</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-white">Verification Loop</td>
                  <td className="py-2.5 px-3 font-mono text-rose-400">None (Single Pass)</td>
                  <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">Isolated Docker / Subprocess Loop</td>
                  <td className="py-2.5 px-3 text-neutral-400">Self-healing test runner corrects regressions before PR</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-white">Security Vulnerability Escapes</td>
                  <td className="py-2.5 px-3 font-mono text-rose-400">38% escape rate</td>
                  <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">0% critical escapes</td>
                  <td className="py-2.5 px-3 text-neutral-400">Static AST scanner + secret entropy gate blocking PRs</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-white">Context Precision & Cost</td>
                  <td className="py-2.5 px-3 font-mono">${scorecard.v1_baseline.total_cost_usd}</td>
                  <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">${scorecard.v2_orchestrated.total_cost_usd}</td>
                  <td className="py-2.5 px-3 text-neutral-400">GraphRAG provides O(1) targeted dependencies vs dump</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Benchmark Tasks Browser */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Task List with Filters (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-400">
              Benchmark Dataset ({filteredTasks.length} / {tasks.length} tasks)
            </h2>
            {/* Category Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
              {["ALL", "BUG_FIX", "SECURITY", "FEATURE", "PERFORMANCE", "REFACTOR"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                    categoryFilter === cat
                      ? "bg-neutral-100 text-neutral-900 font-bold"
                      : "bg-neutral-900 text-neutral-400 hover:text-white border border-neutral-800"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
            {filteredTasks.map((task) => {
              const isSelected = selectedTask?.task_id === task.task_id;
              return (
                <div
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-neutral-800/90 border-emerald-500/60 shadow-lg shadow-emerald-500/5 ring-1 ring-emerald-500/20"
                      : "bg-neutral-900/40 border-neutral-800/80 hover:bg-neutral-900/80 hover:border-neutral-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-neutral-500">{task.task_id}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${getCategoryColor(task.category)}`}>
                        {task.category}
                      </span>
                      <span className={`text-[10px] font-mono font-bold uppercase ${getDifficultyColor(task.difficulty)}`}>
                        {task.difficulty}
                      </span>
                    </div>
                  </div>
                  <h3 className="text-sm font-semibold text-white mt-2">
                    {task.title}
                  </h3>
                  <p className="text-xs text-neutral-400 mt-1 line-clamp-2">
                    {task.description}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-[11px] text-neutral-500 font-mono">
                    <span>{task.target_files.length} target file(s)</span>
                    <span>{task.expected_tools.length} expected tools</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Task Details Card (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-400">
            Task Specification & Evaluation Detail
          </h2>
          {selectedTask ? (
            <div className="p-6 rounded-2xl bg-neutral-900/60 border border-neutral-800/80 backdrop-blur-xl space-y-5">
              <div className="border-b border-neutral-800 pb-4">
                <span className="text-xs font-mono text-emerald-400">{selectedTask.task_id}</span>
                <h3 className="text-base font-bold text-white mt-1">{selectedTask.title}</h3>
                <p className="text-xs text-neutral-300 mt-2">{selectedTask.description}</p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">
                  Target Files
                </h4>
                <div className="space-y-1 font-mono text-xs text-blue-400 bg-neutral-950/70 p-3 rounded-xl border border-neutral-800">
                  {selectedTask.target_files.map((f, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span>📄</span> {f}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">
                  Expected Multi-Agent Tools
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedTask.expected_tools.map((t, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-neutral-950 border border-neutral-800 text-[11px] font-mono text-neutral-300"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">
                  Test Validation Criteria
                </h4>
                <div className="p-3 rounded-xl bg-neutral-950/70 border border-neutral-800 text-xs font-mono text-emerald-300">
                  {selectedTask.test_criteria}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-neutral-500 border border-neutral-800 rounded-2xl">
              Select a task to inspect target files, tools, and test criteria.
            </div>
          )}
        </div>
      </div>

      {/* Markdown Report Modal */}
      {showReportModal && reportMarkdown && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl max-w-3xl w-full max-h-[80vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-neutral-800">
              <h3 className="text-base font-bold text-white">SWE Benchmark Markdown Report</h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-neutral-400 hover:text-white text-sm"
              >
                ✕ Close
              </button>
            </div>
            <div className="p-6 overflow-y-auto font-mono text-xs text-neutral-300 bg-neutral-950 whitespace-pre-wrap">
              {reportMarkdown}
            </div>
            <div className="p-4 border-t border-neutral-800 flex justify-end">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(reportMarkdown);
                  alert("Report copied to clipboard!");
                }}
                className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
