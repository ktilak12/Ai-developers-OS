import re
from typing import List, Dict, Any
from intelligence.embeddings.embeddings import EmbeddingEngine

class VectorStore:
    """
    In-memory vector database storing text chunks and their embeddings
    for fast similarity search.
    Includes security guards against unbounded capacity growth and oversized queries.
    """

    MAX_STORE_CAPACITY = 10000
    MAX_QUERY_LENGTH = 500

    def __init__(self):
        self.engine = EmbeddingEngine()
        self.store: List[Dict[str, Any]] = []

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks or not isinstance(chunks, list):
            return

        for chunk in chunks:
            if len(self.store) >= self.MAX_STORE_CAPACITY:
                break
            if not isinstance(chunk, dict):
                continue
            text = str(chunk.get("text", ""))
            vector = self.engine.generate_embedding(text)
            self.store.append({
                "chunk": chunk,
                "vector": vector
            })

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.store or not query or not isinstance(query, str):
            return []

        # Sanitize and truncate query
        clean_query = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", query).strip()[:self.MAX_QUERY_LENGTH]
        if not clean_query:
            return []

        effective_top_k = max(1, min(int(top_k), 100))
        query_vector = self.engine.generate_embedding(clean_query)
        scored_results = []

        for item in self.store:
            sim = EmbeddingEngine.cosine_similarity(query_vector, item["vector"])
            scored_results.append({
                "score": round(sim, 4),
                "chunk": item["chunk"]
            })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:effective_top_k]

    def clear(self):
        self.store.clear()

