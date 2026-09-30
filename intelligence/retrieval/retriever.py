import os
from typing import List, Dict, Any
from intelligence.retrieval.text_chunker import TextChunker
from intelligence.retrieval.vector_store import VectorStore
from intelligence.reranking.reranker import Reranker

class ProjectRAGPipeline:
    """
    End-to-End Project RAG Pipeline.
    Indexes a codebase into semantic chunks, computes vector embeddings, and performs
    hybrid vector retrieval + reranking.
    """

    EXCLUDE_DIRS = {"node_modules", ".next", ".git", "__pycache__", "venv", ".venv", "dist", "build"}

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.chunker = TextChunker(chunk_size=40, overlap=10)
        self.vector_store = VectorStore()
        self.reranker = Reranker()
        self.is_indexed = False

    def build_index(self) -> int:
        self.vector_store.clear()
        total_chunks = 0

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")

                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        chunks = self.chunker.chunk_file(rel_path, content)
                        self.vector_store.add_chunks(chunks)
                        total_chunks += len(chunks)
                    except Exception as e:
                        print(f"Error reading file {rel_path} for RAG: {e}")

        self.is_indexed = True
        return total_chunks

    def query(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        if not self.is_indexed:
            self.build_index()

        candidates = self.vector_store.search(question, top_k=top_k * 2)
        reranked_results = self.reranker.rerank(question, candidates)[:top_k]

        context_blocks = []
        retrieved_files = set()

        for item in reranked_results:
            chunk = item["chunk"]
            retrieved_files.add(chunk["file_path"])
            context_blocks.append(
                f"--- File: {chunk['file_path']} (Lines {chunk.get('start_line', 1)}-{chunk.get('end_line', 1)}) ---\n"
                f"{chunk['text']}"
            )

        context_prompt = "\n\n".join(context_blocks)

        return {
            "question": question,
            "retrieved_files": list(retrieved_files),
            "context_prompt": context_prompt,
            "results": reranked_results
        }
