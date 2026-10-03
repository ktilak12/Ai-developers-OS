"use client";

import { useState } from "react";

interface SecurityFinding {
  file: string;
  line: number;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
  rule_id: string;
  rule_name: string;
  description: string;
  recommendation: string;
}

interface SeveritySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface SecurityReport {
  status: "PASSED" | "BLOCKED_BY_POLICY" | string;
  passed: boolean;
  security_score: number;
  grade: string;
  scanned_files_count: number;
  scanned_files: string[];
  total_findings_count: number;
  severity_summary: SeveritySummary;
  findings: SecurityFinding[];
  approval_gate: {
    merge_allowed: boolean;
    reason: string;
  };
}

export default function SecurityAgentPage() {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"findings" | "pipeline" | "rules">("findings");

  const [report, setReport] = useState<SecurityReport | null>({
    status: "PASSED",
    passed: true,
    security_score: 96,
    grade: "A",
    scanned_files_count: 8,
    scanned_files: [
      "apps/web/src/app/login/page.tsx",
      "apps/api/main.py",
      "agents/coder/agent.py",
      "sandbox/runner/container_runner.py"
    ],
    total_findings_count: 1,
    severity_summary: {
      critical: 0,
      high: 0,
      medium: 1,
      low: 0
    },
    findings: [
      {
        file: "apps/api/main.py",
        line: 22,
        severity: "MEDIUM",
        rule_id: "SEC-CONFIG-004",
        rule_name: "Wildcard CORS with Credentials",
        description: "Insecure configuration pattern: Wildcard CORS with Credentials.",
        recommendation: "Replace allow_origins=['*'] with explicit trusted client domains in production."
      }
    ],
    approval_gate: {
      merge_allowed: true,
      reason: "Clean security scan. Zero critical or high-severity vulnerabilities detected."
    }
  });

  const handleRunScan = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/agents/security/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_paths: [
            "apps/web/src/app/login/page.tsx",
            "apps/api/main.py",
            "agents/coder/agent.py",
            "sandbox/runner/container_runner.py"
          ]
        })
      });
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (e) {
      console.log("Using local Security Agent simulated fallback");
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return <span className="rounded-lg bg-red-500/20 px-2.5 py-1 text-xs font-bold text-red-400 border border-red-500/30">CRITICAL</span>;
      case "HIGH":
        return <span className="rounded-lg bg-orange-500/20 px-2.5 py-1 text-xs font-bold text-orange-400 border border-orange-500/30">HIGH</span>;
      case "MEDIUM":
        return <span className="rounded-lg bg-amber-500/20 px-2.5 py-1 text-xs font-bold text-amber-400 border border-amber-500/30">MEDIUM</span>;
      case "LOW":
        return <span className="rounded-lg bg-blue-500/20 px-2.5 py-1 text-xs font-bold text-blue-400 border border-blue-500/30">LOW</span>;
      default:
        return <span className="rounded-lg bg-neutral-800 px-2.5 py-1 text-xs font-bold text-neutral-400">{sev}</span>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white tracking-tight">Security Agent</h1>
            <span className="inline-flex items-center rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-400 border border-rose-500/20">
              Phase 9 Active
            </span>
          </div>
          <p className="text-neutral-400 mt-1">
            Automated static security analysis, secret detection, and code injection auditing before developer approval and PR merging.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunScan}
            disabled={loading}
            className="rounded-xl bg-rose-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-rose-500 transition-colors shadow-lg shadow-rose-950/40 flex items-center gap-2 disabled:opacity-50"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            {loading ? "Scanning Code..." : "Run Security Audit"}
          </button>
        </div>
      </div>

      {/* Security Health Score & Severity Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Security Score</span>
          <p className="text-2xl font-black text-white flex items-baseline gap-1">
            <span>{report?.security_score ?? 100}</span>
            <span className="text-xs text-neutral-500 font-normal">/ 100</span>
          </p>
          <span className="text-xs text-emerald-400 font-semibold">Grade {report?.grade ?? "A"} Status</span>
        </div>
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Critical Risks</span>
          <p className={`text-2xl font-black ${(report?.severity_summary.critical ?? 0) > 0 ? "text-red-400" : "text-neutral-400"}`}>
            {report?.severity_summary.critical ?? 0}
          </p>
          <span className="text-xs text-neutral-500">Zero Tolerance</span>
        </div>
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">High Risks</span>
          <p className={`text-2xl font-black ${(report?.severity_summary.high ?? 0) > 0 ? "text-orange-400" : "text-neutral-400"}`}>
            {report?.severity_summary.high ?? 0}
          </p>
          <span className="text-xs text-neutral-500">Merge Blockers</span>
        </div>
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Medium Risks</span>
          <p className="text-2xl font-black text-amber-400">
            {report?.severity_summary.medium ?? 0}
          </p>
          <span className="text-xs text-neutral-500">Review Required</span>
        </div>
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Low / Info</span>
          <p className="text-2xl font-black text-blue-400">
            {report?.severity_summary.low ?? 0}
          </p>
          <span className="text-xs text-neutral-500">Advisory Items</span>
        </div>
      </div>

      {/* Security Approval Gate Banner */}
      <div className={`rounded-2xl border p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-xl ${
        report?.passed 
          ? "border-emerald-500/30 bg-emerald-950/20" 
          : "border-red-500/30 bg-red-950/20"
      }`}>
        <div className="flex items-center gap-3">
          <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-bold shrink-0 ${
            report?.passed ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
          }`}>
            {report?.passed ? "✓" : "✕"}
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              {report?.passed ? "Security Approval Gate: Merge Allowed" : "Security Approval Gate: Merge Blocked"}
            </h3>
            <p className="text-xs text-neutral-300 mt-0.5">{report?.approval_gate.reason}</p>
          </div>
        </div>

        <span className={`inline-flex items-center rounded-xl px-3 py-1.5 text-xs font-mono font-bold shrink-0 ${
          report?.passed ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30"
        }`}>
          Status: {report?.status}
        </span>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-800 pb-2">
        <button
          onClick={() => setActiveTab("findings")}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
            activeTab === "findings"
              ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          Security Findings ({report?.findings.length ?? 0})
        </button>
        <button
          onClick={() => setActiveTab("pipeline")}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
            activeTab === "pipeline"
              ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          Security Pipeline Architecture
        </button>
        <button
          onClick={() => setActiveTab("rules")}
          className={`px-4 py-2 rounded-xl text-sm font-semibold transition-colors ${
            activeTab === "rules"
              ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          Active Detection Rules
        </button>
      </div>

      {/* Tab: Findings List */}
      {activeTab === "findings" && (
        <div className="space-y-4">
          {report && report.findings.length > 0 ? (
            report.findings.map((finding, idx) => (
              <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-3 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-neutral-800 pb-3">
                  <div className="flex items-center gap-3">
                    {getSeverityBadge(finding.severity)}
                    <span className="text-base font-bold text-white">{finding.rule_name}</span>
                  </div>
                  <div className="flex items-center gap-2 font-mono text-xs text-neutral-400">
                    <span className="bg-neutral-950 px-2.5 py-1 rounded border border-neutral-800 text-neutral-300">
                      {finding.file}:{finding.line}
                    </span>
                    <span className="text-neutral-500">{finding.rule_id}</span>
                  </div>
                </div>

                <p className="text-sm text-neutral-300">{finding.description}</p>

                <div className="rounded-xl bg-neutral-950 p-3.5 border border-neutral-800/80 space-y-1">
                  <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 block">
                    Remediation Recommendation
                  </span>
                  <p className="text-xs text-neutral-300 font-mono">{finding.recommendation}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 rounded-2xl border border-neutral-800 bg-neutral-900/40 space-y-2">
              <div className="h-12 w-12 mx-auto rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xl">✓</div>
              <h3 className="text-base font-bold text-white">No Vulnerabilities Found</h3>
              <p className="text-xs text-neutral-400">Zero exposed secrets or dangerous code execution vectors detected.</p>
            </div>
          )}
        </div>
      )}

      {/* Tab: Pipeline Architecture */}
      {activeTab === "pipeline" && (
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Automated Security Inspection Pipeline</h3>
            <p className="text-xs text-neutral-400">
              The Security Agent executes a multi-tiered pipeline grounded in static analysis and secret pattern matchers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-6 gap-3 text-center">
            {[
              { step: 1, title: "Code Changes", desc: "Diffs from Coder Agent" },
              { step: 2, title: "Static Analysis", desc: "AST syntax checks" },
              { step: 3, title: "Dependency Check", desc: "Known vulnerable packages" },
              { step: 4, title: "Secret Detection", desc: "Regex regex scanners" },
              { step: 5, title: "AI Security Agent", desc: "Prioritizes & explains" },
              { step: 6, title: "Security Report", desc: "Merge approval gate" }
            ].map((p, i) => (
              <div key={i} className="rounded-xl border border-neutral-800 bg-neutral-950 p-3.5 space-y-1">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-rose-500/10 text-xs font-bold font-mono text-rose-400 mx-auto">
                  {p.step}
                </span>
                <h4 className="text-xs font-bold text-white pt-1">{p.title}</h4>
                <p className="text-[11px] text-neutral-500">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Active Rules */}
      {activeTab === "rules" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider text-rose-400">Secret & Credential Rules</h3>
            <ul className="space-y-2 text-xs font-mono text-neutral-300">
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ AWS Access Keys (AKIA...)</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ GitHub Personal Access Tokens (ghp_...)</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Hardcoded Database Passwords & DSNs</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Private RSA / PEM Certificate Keys</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Raw JWT Secret Tokens</li>
            </ul>
          </div>
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5 space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider text-orange-400">Code Injection & Safety Rules</h3>
            <ul className="space-y-2 text-xs font-mono text-neutral-300">
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Arbitrary Code Execution via eval()</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Shell Injection via subprocess(shell=True)</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Unsanitized os.system() & child_process</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ SQL Injection via F-strings / String Concat</li>
              <li className="bg-neutral-950 p-2.5 rounded-lg border border-neutral-800">✓ Wildcard CORS with Credentials Enabled</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
