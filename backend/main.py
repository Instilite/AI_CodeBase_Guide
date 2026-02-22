from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import BackgroundTasks, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from chunker import chunk_file
from embedder import EMBEDDING_BATCH_SIZE, EmbeddingError, embed_batch, get_openai_client
from grep import build_grep_chunks, find_definition_file, find_matching_files
from ingest import (
    cleanup_path,
    copy_filtered_files,
    enforce_compressed_limit,
    move_filtered_files,
    parse_content_length,
    sanitize_repo_id,
    validate_and_extract_zip,
    ZipValidationError,
)
from llm import generate_ask_claims, generate_impact_summary
from retriever import (
    assign_evidence_labels,
    compute_confidence,
    is_overview_query,
    merge_impact_chunks,
    select_ask_rows,
    select_impact_vector_rows,
)
from store import (
    delete_collection_if_exists,
    get_or_create_repo_collection,
    get_persistent_client,
    get_repo_collection,
    query_collection,
    upsert_batch,
)

from dotenv import load_dotenv
load_dotenv()


BASE_DIR = Path(".")
REPOS_DIR = BASE_DIR / "repos"
JOBS_DIR = BASE_DIR / "jobs"
TMP_DIR = BASE_DIR / "tmp"
CHROMA_DIR = BASE_DIR / "chroma_db"
DEMO_SOURCE_DIR = BASE_DIR / "demo_repo_seed"

INDEXING_STALE_SECONDS = 1800
JOB_RETENTION_SECONDS = 86400


class ErrorResponse(BaseModel):
    error: str
    message: str
    repo_id: str | None = None
    details: Dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]


class RepoListItem(BaseModel):
    repo_id: str
    name: str
    chunk_count: int
    indexed_at: str


class UploadResponse(BaseModel):
    job_id: str
    repo_id: str
    status: Literal["indexing"]


class JobStatusResponse(BaseModel):
    job_id: str
    repo_id: str
    status: Literal["indexing", "complete", "failed"]
    chunk_count: int
    error: str | None


class AskRequest(BaseModel):
    repo_id: str
    question: str
    mode: str = "auto"


class ImpactRequest(BaseModel):
    repo_id: str
    function_name: str


class Claim(BaseModel):
    claim: str
    evidence: List[str]


class EvidenceChunk(BaseModel):
    evidence_id: str
    file_path: str
    start_line: int
    end_line: int
    text: str
    similarity: float | None
    source: Literal["vector", "grep"]


class AskResponse(BaseModel):
    repo_id: str
    retrieval_mode: Literal["standard", "overview"]
    confidence_score: float
    confidence_label: Literal["High", "Medium", "Low"]
    claims: List[Claim]
    chunks: List[EvidenceChunk]
    llm_fallback_used: bool


class ImpactResponse(BaseModel):
    repo_id: str
    function_name: str
    risk_level: Literal["Low", "Medium", "High"]
    file_count: int
    files_referencing: List[str]
    what_it_does: str
    message: str | None
    chunks: List[EvidenceChunk]
    llm_fallback_used: bool


class DeleteResponse(BaseModel):
    deleted: bool
    repo_id: str


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        *,
        repo_id: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.repo_id = repo_id
        self.details = details


app = FastAPI(title="AI Codebase Guide Backend")

allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.chroma_client = get_persistent_client(path=str(CHROMA_DIR))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    repo_id: str | None = None,
    details: Dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(error=error_code, message=message, repo_id=repo_id, details=details).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _repo_dir(repo_id: str) -> Path:
    return REPOS_DIR / repo_id


def _repo_meta_path(repo_id: str) -> Path:
    return _repo_dir(repo_id) / "repo_meta.json"


def _marker_path(repo_id: str) -> Path:
    return _repo_dir(repo_id) / ".indexing"


def _create_directories() -> None:
    for directory in (REPOS_DIR, JOBS_DIR, TMP_DIR, CHROMA_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _job_payload(
    *,
    job_id: str,
    repo_id: str,
    status: str,
    chunk_count: int,
    error: str | None,
) -> Dict[str, Any]:
    return {
        "job_id": job_id,
        "repo_id": repo_id,
        "status": status,
        "chunk_count": chunk_count,
        "error": error,
    }


def _write_job_status(
    *,
    job_id: str,
    repo_id: str,
    status: str,
    chunk_count: int,
    error: str | None,
) -> None:
    _write_json(
        _job_path(job_id),
        _job_payload(
            job_id=job_id,
            repo_id=repo_id,
            status=status,
            chunk_count=chunk_count,
            error=error,
        ),
    )


def _cleanup_stale_marker(marker_path: Path) -> bool:
    if not marker_path.exists():
        return False
    age = datetime.now(timezone.utc).timestamp() - marker_path.stat().st_mtime
    if age > INDEXING_STALE_SECONDS:
        marker_path.unlink(missing_ok=True)
        return True
    return False


def _cleanup_stale_markers_for_repo(repo_id: str) -> None:
    _cleanup_stale_marker(_marker_path(repo_id))


def _cleanup_stale_markers_global() -> None:
    for marker in REPOS_DIR.glob("*/.indexing"):
        _cleanup_stale_marker(marker)


def _has_active_indexing(repo_id: str) -> bool:
    return _marker_path(repo_id).exists()


def _has_any_active_indexing() -> bool:
    return any(REPOS_DIR.glob("*/.indexing"))


def _repo_exists(repo_id: str) -> bool:
    return _repo_meta_path(repo_id).exists()


def _cleanup_old_job_files() -> None:
    now_ts = datetime.now(timezone.utc).timestamp()
    for job_file in JOBS_DIR.glob("*.json"):
        try:
            payload = _read_json(job_file)
        except Exception:
            continue

        status = str(payload.get("status", ""))
        age = now_ts - job_file.stat().st_mtime
        if status in {"complete", "failed"} and age > JOB_RETENTION_SECONDS:
            job_file.unlink(missing_ok=True)


def _format_failure_error(exc: Exception) -> str:
    if isinstance(exc, EmbeddingError):
        return str(exc)
    return f"{exc.__class__.__name__}: {exc}"


def _iter_repo_source_files(repo_id: str) -> List[Path]:
    repo_dir = _repo_dir(repo_id)
    files: List[Path] = []
    for file_path in sorted(repo_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name in {"repo_meta.json", ".indexing"}:
            continue
        files.append(file_path)
    return files


def _index_repo_contents(job_id: str, repo_id: str, upload_name: str) -> None:
    marker = _marker_path(repo_id)
    chunk_count = 0

    try:
        collection = get_or_create_repo_collection(app.state.chroma_client, repo_id)

        all_chunks: List[Dict[str, Any]] = []
        for file_path in _iter_repo_source_files(repo_id):
            rel_path = file_path.relative_to(_repo_dir(repo_id)).as_posix()
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            all_chunks.extend(chunk_file(repo_id=repo_id, file_path=rel_path, text=text))

        if all_chunks:
            openai_client = get_openai_client()
            for i in range(0, len(all_chunks), EMBEDDING_BATCH_SIZE):
                batch = all_chunks[i : i + EMBEDDING_BATCH_SIZE]
                texts = [str(chunk["text"]) for chunk in batch]
                embeddings = embed_batch(texts, client=openai_client)
                upsert_batch(collection, batch, embeddings)

                chunk_count += len(batch)
                _write_job_status(
                    job_id=job_id,
                    repo_id=repo_id,
                    status="indexing",
                    chunk_count=chunk_count,
                    error=None,
                )

        marker.unlink(missing_ok=True)

        _write_json(
            _repo_meta_path(repo_id),
            {
                "repo_id": repo_id,
                "name": upload_name,
                "indexed_at": _utc_now_iso(),
                "chunk_count": chunk_count,
            },
        )

        _write_job_status(
            job_id=job_id,
            repo_id=repo_id,
            status="complete",
            chunk_count=chunk_count,
            error=None,
        )

    except Exception as exc:
        marker.unlink(missing_ok=True)
        _write_job_status(
            job_id=job_id,
            repo_id=repo_id,
            status="failed",
            chunk_count=chunk_count,
            error=_format_failure_error(exc),
        )


def _risk_level_from_file_count(file_count: int) -> str:
    if file_count <= 1:
        return "Low"
    if file_count <= 3:
        return "Medium"
    return "High"


def _seed_demo_repo_if_needed() -> None:
    try:
        existing_collection = app.state.chroma_client.get_collection(name="repo_demo_repo")
        if int(existing_collection.count()) > 0:
            return
    except Exception:
        pass

    if not DEMO_SOURCE_DIR.exists():
        raise RuntimeError("demo_repo_seed directory is missing")

    repo_id = "demo_repo"
    repo_dir = _repo_dir(repo_id)

    if repo_dir.exists():
        shutil.rmtree(repo_dir, ignore_errors=True)
    repo_dir.mkdir(parents=True, exist_ok=True)

    copy_filtered_files(DEMO_SOURCE_DIR, repo_dir)

    temp_job = f"seed-{uuid.uuid4()}"
    marker = _marker_path(repo_id)
    marker.touch()
    _write_job_status(
        job_id=temp_job,
        repo_id=repo_id,
        status="indexing",
        chunk_count=0,
        error=None,
    )
    _index_repo_contents(temp_job, repo_id, "demo_repo.zip")

    verify_collection = app.state.chroma_client.get_collection(name="repo_demo_repo")
    if int(verify_collection.count()) <= 0:
        raise RuntimeError("demo seed produced empty collection")


@app.exception_handler(APIError)
async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        repo_id=exc.repo_id,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        status_code=422,
        error_code="validation_error",
        message="Request validation failed.",
        details={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return _error_response(
        status_code=500,
        error_code="internal_error",
        message=str(exc) or "Internal server error.",
    )


@app.on_event("startup")
def on_startup() -> None:
    _create_directories()
    app.state.chroma_client = get_persistent_client(path=str(CHROMA_DIR))
    _cleanup_old_job_files()
    _seed_demo_repo_if_needed()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_repo(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(default=None),
) -> UploadResponse:
    if file is None:
        raise APIError(
            422,
            "validation_error",
            "No file provided.",
            details={"errors": [{"loc": ["body", "file"], "msg": "field required", "type": "missing"}]},
        )

    filename = file.filename or ""
    if not filename:
        raise APIError(
            422,
            "validation_error",
            "No file provided.",
            details={"errors": [{"loc": ["body", "file"], "msg": "filename missing", "type": "value_error"}]},
        )

    content_length_header = parse_content_length(request.headers.get("content-length"))
    blob = await file.read()

    job_id = str(uuid.uuid4())
    repo_id = sanitize_repo_id(filename, REPOS_DIR)

    tmp_extract_dir = TMP_DIR / job_id
    repo_dir = _repo_dir(repo_id)

    try:
        enforce_compressed_limit(content_length_header, len(blob))
        validate_and_extract_zip(blob, tmp_extract_dir)
        move_filtered_files(tmp_extract_dir, repo_dir)
    except ZipValidationError as exc:
        cleanup_path(tmp_extract_dir)
        cleanup_path(repo_dir)
        raise APIError(exc.status_code, exc.error_code, exc.message, details=exc.details) from exc
    except Exception as exc:
        cleanup_path(tmp_extract_dir)
        cleanup_path(repo_dir)
        raise APIError(500, "internal_error", str(exc) or "Internal server error.") from exc
    finally:
        cleanup_path(tmp_extract_dir)

    marker = _marker_path(repo_id)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()

    _write_job_status(job_id=job_id, repo_id=repo_id, status="indexing", chunk_count=0, error=None)
    background_tasks.add_task(_index_repo_contents, job_id, repo_id, filename)

    return UploadResponse(job_id=job_id, repo_id=repo_id, status="indexing")


@app.get("/status/{job_id}", response_model=JobStatusResponse)
def status(job_id: str) -> JobStatusResponse:
    path = _job_path(job_id)
    if not path.exists():
        raise APIError(404, "job_not_found", "No job found with the given ID.")

    payload = _read_json(path)
    return JobStatusResponse(**payload)


@app.get("/repos", response_model=List[RepoListItem])
def list_repos() -> List[RepoListItem]:
    _cleanup_stale_markers_global()

    if _has_any_active_indexing():
        raise APIError(409, "indexing_in_progress", "Indexing in progress. Try again soon.")

    repos: List[RepoListItem] = []
    for meta_path in sorted(REPOS_DIR.glob("*/repo_meta.json")):
        payload = _read_json(meta_path)
        repos.append(RepoListItem(**payload))

    return repos


@app.delete("/repos/{repo_id}", response_model=DeleteResponse)
def delete_repo(repo_id: str) -> DeleteResponse:
    if not _repo_exists(repo_id):
        raise APIError(404, "repo_not_found", "Repository not found.", repo_id=repo_id)

    cleanup_path(_repo_dir(repo_id))
    delete_collection_if_exists(app.state.chroma_client, repo_id)

    for job_file in JOBS_DIR.glob("*.json"):
        try:
            payload = _read_json(job_file)
            if payload.get("repo_id") == repo_id:
                job_file.unlink(missing_ok=True)
        except Exception:
            continue

    return DeleteResponse(deleted=True, repo_id=repo_id)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    repo_id = req.repo_id

    _cleanup_stale_markers_for_repo(repo_id)

    if _has_active_indexing(repo_id):
        raise APIError(
            409,
            "indexing_in_progress",
            "Repo is still indexing. Try again soon.",
            repo_id=repo_id,
        )

    if not _repo_exists(repo_id):
        raise APIError(404, "repo_not_found", "Repository not found.", repo_id=repo_id)

    overview_mode = is_overview_query(req.question)
    retrieval_mode: Literal["standard", "overview"] = "overview" if overview_mode else "standard"
    n_results = 60 if overview_mode else 12

    try:
        query_embedding = embed_batch([req.question])[0]
    except Exception as exc:
        raise APIError(500, "internal_error", str(exc) or "Internal server error.", repo_id=repo_id) from exc

    try:
        collection = get_repo_collection(app.state.chroma_client, repo_id)
        raw_rows = query_collection(collection, query_embedding, n_results=n_results)
    except Exception as exc:
        raise APIError(
            500,
            "internal_error",
            "Vector store query failed. Repository index may be corrupt.",
            repo_id=repo_id,
        ) from exc

    selected_chunks = select_ask_rows(raw_rows, overview_mode=overview_mode)
    confidence_score, confidence_label = compute_confidence(selected_chunks)

    frozen_chunks = assign_evidence_labels(selected_chunks)
    claims, llm_fallback_used = generate_ask_claims(question=req.question, chunks=frozen_chunks)

    return AskResponse(
        repo_id=repo_id,
        retrieval_mode=retrieval_mode,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
        claims=claims,
        chunks=frozen_chunks,
        llm_fallback_used=llm_fallback_used,
    )


@app.post("/impact", response_model=ImpactResponse)
def impact(req: ImpactRequest) -> ImpactResponse:
    repo_id = req.repo_id

    _cleanup_stale_markers_for_repo(repo_id)

    if _has_active_indexing(repo_id):
        raise APIError(
            409,
            "indexing_in_progress",
            "Repo is still indexing. Try again soon.",
            repo_id=repo_id,
        )

    if not _repo_exists(repo_id):
        raise APIError(404, "repo_not_found", "Repository not found.", repo_id=repo_id)

    repo_root = _repo_dir(repo_id)

    _, matches_by_file = find_matching_files(repo_root, req.function_name)
    matching_files = set(matches_by_file.keys())

    definition_file = find_definition_file(repo_root, matching_files, req.function_name) if matching_files else None

    files_referencing_set = set(matching_files)
    if definition_file:
        files_referencing_set.discard(definition_file)
    files_referencing = sorted(files_referencing_set)

    file_count = len(files_referencing)
    risk_level = _risk_level_from_file_count(file_count)

    message: str | None
    if not matching_files:
        message = "No exact word-boundary grep matches found. Showing semantic evidence only."
    else:
        message = None

    grep_chunks = build_grep_chunks(repo_root, matches_by_file, files_referencing)

    try:
        function_embedding = embed_batch([req.function_name])[0]
    except Exception as exc:
        raise APIError(500, "internal_error", str(exc) or "Internal server error.", repo_id=repo_id) from exc

    try:
        collection = get_repo_collection(app.state.chroma_client, repo_id)
        vector_rows = query_collection(collection, function_embedding, n_results=6)
    except Exception as exc:
        raise APIError(
            500,
            "internal_error",
            "Vector store query failed. Repository index may be corrupt.",
            repo_id=repo_id,
        ) from exc

    vector_chunks = select_impact_vector_rows(vector_rows)
    merged_chunks = merge_impact_chunks(grep_chunks, vector_chunks)

    frozen_chunks = assign_evidence_labels(merged_chunks)
    what_it_does, llm_fallback_used = generate_impact_summary(
        function_name=req.function_name,
        chunks=frozen_chunks,
    )

    return ImpactResponse(
        repo_id=repo_id,
        function_name=req.function_name,
        risk_level=risk_level,  # Mechanical from file_count only.
        file_count=file_count,
        files_referencing=files_referencing,
        what_it_does=what_it_does,
        message=message,
        chunks=frozen_chunks,
        llm_fallback_used=llm_fallback_used,
    )
