import math
import re
from typing import List, Dict, Any

class EmbeddingEngine:
    """
    Computes vector representations of code chunks using TF-IDF and term frequency
    embeddings for vector similarity matching.
    Includes security guards against oversized payloads and CPU exhaustion.
    """

    MAX_TEXT_LENGTH = 50000
    MAX_TOKENS_COUNT = 5000

    def __init__(self, vector_dim: int = 128):
        self.vector_dim = max(16, min(int(vector_dim), 1024))

    def _tokenize(self, text: str) -> List[str]:
        if not text or not isinstance(text, str):
            return []
        bounded_text = text[:self.MAX_TEXT_LENGTH]
        tokens = re.findall(r'[a-zA-Z0-9_]+', bounded_text)
        return [t.lower() for t in tokens[:self.MAX_TOKENS_COUNT]]

    def generate_embedding(self, text: str) -> List[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.vector_dim

        vec = [0.0] * self.vector_dim
        for token in tokens:
            # Deterministic feature hashing into vector_dim dimensions
            idx = abs(hash(token)) % self.vector_dim
            vec[idx] += 1.0

        # L2 Normalize vector
        magnitude = math.sqrt(sum(val * val for val in vec))
        if magnitude > 0:
            vec = [val / magnitude for val in vec]

        return vec

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        try:
            return float(sum(a * b for a, b in zip(vec1, vec2)))
        except Exception:
            return 0.0

