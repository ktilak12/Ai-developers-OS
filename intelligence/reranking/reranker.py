import re
from typing import List, Dict, Any

class Reranker:
    """
    Reranks candidate vector store results using exact symbol matching,
    filename relevance, and query term frequency scoring.
    Includes security protections against malformed inputs and term explosion.
    """

    MAX_QUERY_TERMS = 10
    MAX_TERM_LENGTH = 50

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidate_chunks or not isinstance(candidate_chunks, list):
            return []

        clean_query = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(query or "")).strip()
        query_terms = [
            t.lower()[:self.MAX_TERM_LENGTH]
            for t in clean_query.split()
            if len(t) > 2
        ][:self.MAX_QUERY_TERMS]

        reranked = []

        for candidate in candidate_chunks:
            if not isinstance(candidate, dict):
                continue
            chunk = candidate.get("chunk")
            if not isinstance(chunk, dict):
                continue

            try:
                base_score = float(candidate.get("score", 0.0))
            except (ValueError, TypeError):
                base_score = 0.0

            text = str(chunk.get("text", "")).lower()
            file_path = str(chunk.get("file_path", "")).lower()

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

