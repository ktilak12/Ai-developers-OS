"use client";

import { useState } from "react";

interface RAGResult {
  question: string;
  retrieved_files: string[];
  context_prompt: string;
  results: Array<{
    final_score: number;
    vector_score: number;
    chunk: {
      file_path: string;
      start_line: number;
      end_line: number;
      text: string;
    };
  }>;
}

export default function ProjectRAGPage() {
  const [question, setQuestion] = useState("How does checkout work?");
  const [loading, setLoading] = useState(false);
  const [ragData, setRagData] = useState<RAGResult | null>({
    question: "How does checkout work?",
    retrieved_files: [
      "apps/web/src/app/(dashboard)/projects/[id]/page.tsx",
      "apps/api/main.py"
    ],
    context_prompt: "--- File: apps/web/src/app/(dashboard)/projects/[id]/page.tsx (Lines 1-40) ---\nconst tasks = [\n  { id: 'T-124', title: 'Fix checkout failure when applying expired coupon', status: 'In Progress' }\n];",
    results: [
      {
        final_score: 0.925,
        vector_score: 0.825,
        chunk: {
          file_path: "apps/web/src/app/(dashboard)/projects/[id]/page.tsx",
          start_line: 1,
          end_line: 40,
          text: `// Quick Task Handler\nconst tasks = [\n  { id: 'T-124', title: 'Fix checkout failure when applying expired coupon', status: 'In Progress', agent: 'Testing Agent' }\n];`
        }
      },
      {
        final_score: 0.810,
        vector_score: 0.710,
        chunk: {
          file_path: "apps/api/main.py",
          start_line: 25,
          end_line: 60,
          text: `@app.get("/api/github/issues")\nasync def get_issues(owner: str, repo: str):\n    # Fetches issues including checkout bug reports`
        }
      }
    ]
  });

  const handleRAGQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/rag/query?question=${encodeURIComponent(question)}`);
      if (res.ok) {
        const data = await res.json();
        setRagData(data);
      }
    } catch (e) {
      console.log("Using local RAG retrieval mock result");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8 border-b border-neutral-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-500" />
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Project RAG Retrieval</h1>
          <span className="inline-flex items-center rounded-md bg-neutral-900 px-2.5 py-0.5 text-[11px] font-mono text-neutral-300 border border-neutral-800">
            Phase 4 Active
          </span>
        </div>
        <p className="text-sm text-neutral-400 mt-2">Chunking, L2 vector embeddings, vector store retrieval & cross-encoder reranking.</p>
      </div>

      {/* Query Bar */}
      <form onSubmit={handleRAGQuery} className="mb-8">
        <div className="relative">
          <input 
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question (e.g. 'How does checkout work?')"
            className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-6 py-3.5 pl-12 text-sm text-white placeholder-neutral-500 focus:border-neutral-500 focus:outline-none shadow-sm transition-colors"
          />
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <button 
            type="submit"
            disabled={loading}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black hover:bg-neutral-200 transition-colors shadow-sm disabled:opacity-50"
          >
            {loading ? "Searching Vectors..." : "Retrieve RAG Context"}
          </button>
        </div>
      </form>

      {/* RAG Results View */}
      {ragData && (
        <div className="space-y-8">
          {/* Retrieved Context Summary */}
          <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Retrieved Files Context</h3>
            <div className="flex flex-wrap gap-2 mb-4">
              {ragData.retrieved_files.map((file) => (
                <span key={file} className="rounded-md bg-neutral-900 px-3 py-1 font-mono text-xs text-neutral-300 border border-neutral-800">
                  {file}
                </span>
              ))}
            </div>
            <p className="text-sm text-neutral-400">RAG pipeline extracted {ragData.results.length} highly relevant code windows without saturating LLM context.</p>
          </div>

          {/* Candidate Code Chunks */}
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
              Ranked Vector Candidates ({ragData.results.length})
            </h3>

            {ragData.results.map((res, idx) => (
              <div key={idx} className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-semibold text-white">{res.chunk.file_path}</span>
                    <span className="text-xs text-neutral-500 font-mono">Lines {res.chunk.start_line}-{res.chunk.end_line}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-neutral-300 bg-neutral-900 px-2.5 py-0.5 rounded-md font-mono font-medium border border-neutral-800">
                      Relevance Score: {res.final_score}
                    </span>
                  </div>
                </div>

                <pre className="rounded-lg border border-neutral-850 bg-neutral-900 p-4 text-xs font-mono text-neutral-300 overflow-x-auto">
                  <code>{res.chunk.text}</code>
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
