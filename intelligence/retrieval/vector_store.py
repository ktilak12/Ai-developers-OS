from typing import List, Dict, Any
from intelligence.embeddings.embeddings import EmbeddingEngine

class VectorStore:
    """
    In-memory vector database storing text chunks and their embeddings
    for fast similarity search.
    """

    def __init__(self):
        self.engine = EmbeddingEngine()
        self.store: List[Dict[str, Any]] = []

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        for chunk in chunks:
            text = chunk.get("text", "")
            vector = self.engine.generate_embedding(text)
            self.store.append({
                "chunk": chunk,
                "vector": vector
            })

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.store:
            return []

        query_vector = self.engine.generate_embedding(query)
        scored_results = []

        for item in self.store:
            sim = EmbeddingEngine.cosine_similarity(query_vector, item["vector"])
            scored_results.append({
                "score": round(sim, 4),
                "chunk": item["chunk"]
            })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def clear(self):
        self.store.clear()
