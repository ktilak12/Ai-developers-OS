import os
import re
from typing import List, Dict, Any
from intelligence.retrieval.text_chunker import TextChunker
from intelligence.retrieval.vector_store import VectorStore
from intelligence.reranking.reranker import Reranker

class ProjectRAGPipeline:
    """
    End-to-End Project RAG Pipeline.
    Indexes a codebase into semantic chunks, computes vector embeddings, and performs
    hybrid vector retrieval + reranking.
    Includes security protections: directory jailing, sensitive secrets shielding,
    and file size / count limits to prevent resource exhaustion.
    """

    EXCLUDE_DIRS = {
        "node_modules", ".next", ".git", "__pycache__", "venv", ".venv",
        "dist", "build", ".memory", ".observability", ".evaluation"
    }

    SENSITIVE_PATTERNS = {
        ".env", ".env.local", ".env.production", ".env.development",
        "id_rsa", "id_ed25519", "credentials.json", "service_account.json",
        "secret.key", "private.key", ".pem", ".pfx", ".pkcs12"
    }

    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB limit
    MAX_FILES_LIMIT = 2500

    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))
        self.chunker = TextChunker(chunk_size=40, overlap=10)
        self.vector_store = VectorStore()
        self.reranker = Reranker()
        self.is_indexed = False

    def _is_safe_file(self, full_path: str, filename: str) -> bool:
        """Verifies that the target file is inside the root directory and safe to index."""
        lower_name = filename.lower()
        if any(pat in lower_name for pat in self.SENSITIVE_PATTERNS):
            return False

        try:
            real_path = os.path.realpath(full_path)
            if os.path.commonpath([self.root_dir, real_path]) != self.root_dir:
                return False
        except Exception:
            return False

        try:
            if os.path.getsize(full_path) > self.MAX_FILE_SIZE_BYTES:
                return False
        except Exception:
            return False

        return True

    def build_index(self) -> int:
        self.vector_store.clear()
        total_chunks = 0
        files_indexed = 0

        for root, dirs, files in os.walk(self.root_dir, followlinks=False):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for file in files:
                if files_indexed >= self.MAX_FILES_LIMIT:
                    break

                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json")):
                    full_path = os.path.join(root, file)
                    if not self._is_safe_file(full_path, file):
                        continue

                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")

                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read(self.MAX_FILE_SIZE_BYTES)

                        chunks = self.chunker.chunk_file(rel_path, content)
                        self.vector_store.add_chunks(chunks)
                        total_chunks += len(chunks)
                        files_indexed += 1
                    except Exception as e:
                        print(f"Error reading file {rel_path} for RAG: {e}")

        self.is_indexed = True
        return total_chunks

    def query(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        clean_question = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(question or "")).strip()[:500]
        effective_top_k = max(1, min(int(top_k), 20))

        if not self.is_indexed:
            self.build_index()

        candidates = self.vector_store.search(clean_question, top_k=effective_top_k * 2)
        reranked_results = self.reranker.rerank(clean_question, candidates)[:effective_top_k]

        context_blocks = []
        retrieved_files = set()

        for item in reranked_results:
            chunk = item.get("chunk", {})
            file_path = chunk.get("file_path", "")
            if file_path:
                retrieved_files.add(file_path)
            context_blocks.append(
                f"--- File: {file_path} (Lines {chunk.get('start_line', 1)}-{chunk.get('end_line', 1)}) ---\n"
                f"{chunk.get('text', '')}"
            )

        context_prompt = "\n\n".join(context_blocks)

        return {
            "question": clean_question,
            "retrieved_files": list(retrieved_files),
            "context_prompt": context_prompt,
            "results": reranked_results
        }

