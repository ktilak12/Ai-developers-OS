from typing import List, Dict, Any

class TextChunker:
    """
    Splits source code files into semantic chunks (functions, classes, or fixed-line windows)
    to prevent prompt saturation and optimize vector retrieval.
    """

    def __init__(self, chunk_size: int = 50, overlap: int = 10):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        chunks = []

        if len(lines) <= self.chunk_size:
            chunks.append({
                "file_path": file_path,
                "start_line": 1,
                "end_line": len(lines),
                "text": content
            })
            return chunks

        i = 0
        chunk_id = 1
        while i < len(lines):
            chunk_lines = lines[i : i + self.chunk_size]
            chunk_text = "\n".join(chunk_lines)
            
            chunks.append({
                "chunk_id": f"{file_path}#chunk-{chunk_id}",
                "file_path": file_path,
                "start_line": i + 1,
                "end_line": i + len(chunk_lines),
                "text": chunk_text
            })
            
            i += self.chunk_size - self.overlap
            chunk_id += 1

        return chunks
