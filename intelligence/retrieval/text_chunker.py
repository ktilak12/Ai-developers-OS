from typing import List, Dict, Any

class TextChunker:
    """
    Splits source code files into semantic chunks (functions, classes, or fixed-line windows)
    to prevent prompt saturation and optimize vector retrieval.
    Includes security guards against infinite loop strides and memory exhaustion.
    """

    MAX_CHUNKS_PER_FILE = 500
    MAX_LINES_PER_FILE = 10000

    def __init__(self, chunk_size: int = 50, overlap: int = 10):
        # Validate and bound parameters to prevent zero-stride infinite loops
        self.chunk_size = max(5, min(int(chunk_size), 500))
        self.overlap = max(0, min(int(overlap), self.chunk_size - 1))

    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        if not content or not isinstance(content, str):
            return []

        lines = content.splitlines()[:self.MAX_LINES_PER_FILE]
        chunks: List[Dict[str, Any]] = []

        if not lines:
            return []

        if len(lines) <= self.chunk_size:
            chunks.append({
                "file_path": file_path,
                "start_line": 1,
                "end_line": len(lines),
                "text": content[:10000]
            })
            return chunks

        stride = max(1, self.chunk_size - self.overlap)
        i = 0
        chunk_id = 1

        while i < len(lines) and len(chunks) < self.MAX_CHUNKS_PER_FILE:
            chunk_lines = lines[i : i + self.chunk_size]
            chunk_text = "\n".join(chunk_lines)
            
            chunks.append({
                "chunk_id": f"{file_path}#chunk-{chunk_id}",
                "file_path": file_path,
                "start_line": i + 1,
                "end_line": i + len(chunk_lines),
                "text": chunk_text
            })
            
            i += stride
            chunk_id += 1

        return chunks

