from typing import List, Dict, Any

class Reranker:
    """
    Reranks candidate vector store results using exact symbol matching,
    filename relevance, and query term frequency scoring.
    """

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        reranked = []

        for candidate in candidate_chunks:
            chunk = candidate["chunk"]
            base_score = candidate["score"]
            text = chunk.get("text", "").lower()
            file_path = chunk.get("file_path", "").lower()

            bonus = 0.0
            for term in query_terms:
                if term in file_path:
                    bonus += 0.2
                if term in text:
                    bonus += 0.1

            final_score = round(base_score + bonus, 4)
            reranked.append({
                "final_score": final_score,
                "vector_score": base_score,
                "chunk": chunk
            })

        reranked.sort(key=lambda x: x["final_score"], reverse=True)
        return reranked
