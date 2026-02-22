from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from chunker import chunk_file
from embedder import EMBEDDING_BATCH_SIZE, embed_batch, get_openai_client
from ingest import cleanup_path, copy_filtered_files
from store import get_or_create_repo_collection, get_persistent_client

REPOS_DIR = Path("./repos")
JOBS_DIR = Path("./jobs")
TMP_DIR = Path("./tmp")
CHROMA_DIR = Path("./chroma_db")
DEMO_SOURCE_DIR = Path("./demo_repo_seed")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(path)


def write_job(job_id: str, repo_id: str, status: str, chunk_count: int, error: str | None) -> None:
    write_json(
        JOBS_DIR / f"{job_id}.json",
        {
            "job_id": job_id,
            "repo_id": repo_id,
            "status": status,
            "chunk_count": chunk_count,
            "error": error,
        },
    )


def main() -> None:
    for directory in (REPOS_DIR, JOBS_DIR, TMP_DIR, CHROMA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    client = get_persistent_client(path=str(CHROMA_DIR))

    try:
        existing = client.get_collection(name="repo_demo_repo")
        if int(existing.count()) > 0:
            print("demo seed skipped: repo_demo_repo already has items")
            return
    except Exception:
        pass

    if not DEMO_SOURCE_DIR.exists():
        raise RuntimeError("demo_repo_seed directory is missing")

    repo_id = "demo_repo"
    repo_dir = REPOS_DIR / repo_id
    marker = repo_dir / ".indexing"
    job_id = f"seed-{uuid.uuid4()}"

    cleanup_path(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)
    copy_filtered_files(DEMO_SOURCE_DIR, repo_dir)

    marker.touch()
    write_job(job_id, repo_id, "indexing", 0, None)

    chunk_count = 0
    try:
        openai_client = get_openai_client()
        collection = get_or_create_repo_collection(client, repo_id)

        all_chunks: List[Dict[str, Any]] = []
        for file_path in sorted(repo_dir.rglob("*")):
            if not file_path.is_file() or file_path.name in {"repo_meta.json", ".indexing"}:
                continue
            rel_path = file_path.relative_to(repo_dir).as_posix()
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            all_chunks.extend(chunk_file(repo_id=repo_id, file_path=rel_path, text=text))

        for i in range(0, len(all_chunks), EMBEDDING_BATCH_SIZE):
            batch = all_chunks[i : i + EMBEDDING_BATCH_SIZE]
            embeddings = embed_batch([str(c["text"]) for c in batch], client=openai_client)
            collection.upsert(
                ids=[str(c["id"]) for c in batch],
                documents=[str(c["text"]) for c in batch],
                metadatas=[
                    {
                        "repo_id": c["repo_id"],
                        "file_path": c["file_path"],
                        "start_line": int(c["start_line"]),
                        "end_line": int(c["end_line"]),
                        "chunk_index": int(c["chunk_index"]),
                    }
                    for c in batch
                ],
                embeddings=[list(vec) for vec in embeddings],
            )
            chunk_count += len(batch)
            write_job(job_id, repo_id, "indexing", chunk_count, None)

        marker.unlink(missing_ok=True)
        write_json(
            repo_dir / "repo_meta.json",
            {
                "repo_id": repo_id,
                "name": "demo_repo.zip",
                "indexed_at": utc_now_iso(),
                "chunk_count": chunk_count,
            },
        )
        write_job(job_id, repo_id, "complete", chunk_count, None)
    except Exception as exc:
        marker.unlink(missing_ok=True)
        write_job(job_id, repo_id, "failed", chunk_count, f"{exc.__class__.__name__}: {exc}")
        raise

    verify = client.get_collection(name="repo_demo_repo")
    if int(verify.count()) <= 0:
        raise RuntimeError("demo seed verification failed: repo_demo_repo is empty")

    print(f"demo seed complete: repo_demo_repo count={verify.count()}")


if __name__ == "__main__":
    main()
