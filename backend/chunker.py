from __future__ import annotations

import hashlib
from typing import Dict, List


CHUNK_SIZE_LINES = 100
CHUNK_OVERLAP_LINES = 20
CHUNK_STEP_LINES = CHUNK_SIZE_LINES - CHUNK_OVERLAP_LINES


def chunk_file(repo_id: str, file_path: str, text: str) -> List[Dict[str, object]]:
    """Split a source file into 100-line chunks with 20-line overlap."""
    lines = text.splitlines()
    if not lines:
        return []

    chunks: List[Dict[str, object]] = []
    chunk_index = 0

    for start_line in range(0, len(lines), CHUNK_STEP_LINES):
        end_exclusive = min(len(lines), start_line + CHUNK_SIZE_LINES)
        chunk_lines = lines[start_line:end_exclusive]
        if not chunk_lines:
            continue

        chunk_text = "\n".join(chunk_lines)
        sha8 = hashlib.sha1(chunk_text.encode("utf-8", errors="ignore")).hexdigest()[:8]
        chunk_id = f"{file_path}:{chunk_index}:{sha8}"

        chunks.append(
            {
                "id": chunk_id,
                "repo_id": repo_id,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_exclusive - 1,
                "chunk_index": chunk_index,
                "sha1": sha8,
                "text": chunk_text,
            }
        )

        if end_exclusive >= len(lines):
            break
        chunk_index += 1

    return chunks
