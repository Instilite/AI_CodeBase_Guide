from pathlib import Path
from typing import List, Dict, Any

CHUNK_SIZE = 100   # lines per chunk
OVERLAP    = 20    # lines shared between consecutive chunks


def chunk_file(file_path: Path, repo_id: str) -> List[Dict[str, Any]]:
    """
    Split a single file into overlapping chunks.

    Returns a list of chunk dicts, each with:
        - text       : the raw lines joined as a string
        - file_path  : relative path string (for metadata)
        - start_line : 1-indexed line number where chunk starts
        - end_line   : 1-indexed line number where chunk ends
        - repo_id    : passed through for ChromaDB metadata later
    """
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []  # skip unreadable files silently

    if not lines:
        return []

    chunks = []
    start  = 0  # 0-indexed

    while start < len(lines):
        end        = min(start + CHUNK_SIZE, len(lines))
        chunk_lines = lines[start:end]
        chunk_text  = "\n".join(chunk_lines)

        chunks.append({
            "text"      : chunk_text,
            "file_path" : str(file_path),
            "start_line": start + 1,        # convert to 1-indexed
            "end_line"  : end,
            "repo_id"   : repo_id,
        })

        # If we've reached the end of the file, stop
        if end == len(lines):
            break

        # Move forward by (CHUNK_SIZE - OVERLAP) so next chunk
        # shares the last 20 lines with this one
        start += CHUNK_SIZE - OVERLAP

    return chunks


def chunk_repo(repo_path: Path, repo_id: str) -> List[Dict[str, Any]]:
    """
    Walk the entire repo directory and chunk every file.

    Returns a flat list of all chunks across all files.
    """
    all_chunks = []

    for file_path in sorted(repo_path.rglob("*")):
        if not file_path.is_file():
            continue
        file_chunks = chunk_file(file_path, repo_id)
        all_chunks.extend(file_chunks)

    return all_chunks