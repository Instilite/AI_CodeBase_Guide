import logging
import os
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI

from constants import get_collection_name
from embedder import EmbeddingServiceError, create_query_embedding
from grep import build_grep_chunks, find_definition_file, grep_function_references
from llm import LLMServiceError, generate_ask_claims, generate_impact_description
from retriever import build_impact_vector_chunks, retrieve_vector_chunks, run_ask_retrieval
from schemas import (
    AskSuccessResponse,
    ErrorResponse,
    ImpactSuccessResponse,
)
from validator import (
    ContractError,
    validate_ask_input,
    validate_impact_input,
    validate_repo_path,
)

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

app = FastAPI(title="AI Codebase Guide API")
logger = logging.getLogger("ai_codebase_guide")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

CHROMA_DB_PATH = str(Path(__file__).resolve().parent / "chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEXING_STUB = "A"

NOT_INDEXED_ERROR = "Repository not indexed. Call GET /status/{job_id} first."
INDEXING_ERROR = "Repository is still indexing. Retry after status is complete."
EMBEDDING_ERROR = "Embedding service unavailable. Retry in a moment."
ASK_LLM_FALLBACK_CLAIM = {"claim": "Analysis unavailable. Please retry.", "evidence": ["?"]}
IMPACT_ZERO_MATCH_MESSAGE = "Function not found via grep. Vector results shown only."
IMPACT_LLM_FALLBACK_MESSAGE = "LLM output unavailable."
IMPACT_NO_EVIDENCE_MESSAGE = "Insufficient evidence to describe this function."

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
print("MAIN SEES KEY:", os.getenv("OPENAI_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

def _background_job(task_name: str) -> None:
    # Placeholder for future background task logic.
    _ = task_name


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "chroma_path": CHROMA_DB_PATH,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }

@app.post("/tasks/demo")
def run_demo_task(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_background_job, "demo")
    return {"message": "Demo background task queued"}


def _error_response(status: int, message: str) -> JSONResponse:
    body = ErrorResponse(error=message, status=status).model_dump()
    return JSONResponse(status_code=status, content=body)


@app.exception_handler(Exception)
def _unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception type=%s message=%s", type(_exc).__name__, str(_exc))
    # Contract-safe fallback to avoid HTTP 500 responses and stack-trace leakage.
    return _error_response(503, EMBEDDING_ERROR)


def _get_collection(repo_id: str) -> Any | None:
    collection_name = get_collection_name(repo_id)
    try:
        return chroma_client.get_collection(name=collection_name)
    except Exception:
        return None


def _compute_risk_level(file_count: int) -> str:
    if file_count <= 1:
        return "Low"
    if file_count <= 3:
        return "Medium"
    return "High"


def _merge_impact_chunks(
    vector_chunks: list[dict[str, Any]], grep_chunks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_file_paths: set[str] = set()

    for chunk in vector_chunks:
        merged_chunk = {
            "evidence_id": f"E{len(merged) + 1}",
            "chunk_id": str(chunk.get("chunk_id", "")),
            "file_path": str(chunk.get("file_path", "")),
            "start_line": int(chunk.get("start_line", 1)),
            "end_line": int(chunk.get("end_line", chunk.get("start_line", 1))),
            "text": str(chunk.get("text", "")),
            "similarity": chunk.get("similarity"),
        }
        merged.append(merged_chunk)
        seen_file_paths.add(merged_chunk["file_path"])

    for chunk in grep_chunks:
        file_path = str(chunk.get("file_path", ""))
        if file_path in seen_file_paths:
            continue

        merged_chunk = {
            "evidence_id": f"E{len(merged) + 1}",
            "chunk_id": str(chunk.get("chunk_id", "")),
            "file_path": file_path,
            "start_line": int(chunk.get("start_line", 1)),
            "end_line": int(chunk.get("end_line", chunk.get("start_line", 1))),
            "text": str(chunk.get("text", "")),
            "similarity": None,
        }
        merged.append(merged_chunk)
        seen_file_paths.add(file_path)

    for chunk in merged:
        if "evidence_id" not in chunk:
            chunk["evidence_id"] = "?"

    return merged


@app.post("/ask", response_model=AskSuccessResponse)
def ask(payload: dict[str, Any]) -> JSONResponse:
    try:
        validated = validate_ask_input(payload)
    except ContractError as exc:
        return _error_response(exc.status, exc.message)

    repo_id = str(validated["repo_id"])
    try:
        repo_path = validate_repo_path(repo_id)
    except ContractError as exc:
        return _error_response(exc.status, exc.message)

    if not repo_path.exists() or not repo_path.is_dir():
        return _error_response(404, NOT_INDEXED_ERROR)

    if INDEXING_STUB == "A" and (repo_path / ".indexing").exists():
        return _error_response(409, INDEXING_ERROR)

    collection = _get_collection(repo_id)
    if collection is None:
        return _error_response(404, NOT_INDEXED_ERROR)

    try:
        query_embedding = create_query_embedding(openai_client, str(validated["question"]))
    except EmbeddingServiceError:
        return _error_response(503, EMBEDDING_ERROR)

    retrieval = run_ask_retrieval(
        collection=collection,
        repo_id=repo_id,
        question=str(validated["question"]),
        mode_flag=validated["mode"],
        query_embedding=query_embedding,
    )

    claims: list[dict[str, Any]] = []
    llm_fallback_used = False

    chunks = list(retrieval["chunks"])
    logger.info(
        "ask retrieval_mode=%s chunks=%d",
        str(retrieval["retrieval_mode"]),
        len(chunks),
    )
    if chunks:
        try:
            claims = generate_ask_claims(
                openai_client=openai_client,
                question=str(validated["question"]),
                chunks=chunks,
            )
        except LLMServiceError:
            claims = [ASK_LLM_FALLBACK_CLAIM]
            llm_fallback_used = True
            logger.warning("ask fallback triggered: LLMServiceError")
        except Exception:
            claims = [ASK_LLM_FALLBACK_CLAIM]
            llm_fallback_used = True
            logger.warning("ask fallback triggered: unexpected LLM exception")

    response_body = AskSuccessResponse(
        repo_id=repo_id,
        retrieval_mode=str(retrieval["retrieval_mode"]),
        confidence_score=float(retrieval["confidence_score"]),
        confidence_label=str(retrieval["confidence_label"]),
        claims=claims,
        chunks=chunks,
        llm_fallback_used=llm_fallback_used,
    )
    return JSONResponse(status_code=200, content=response_body.model_dump())


@app.post("/impact", response_model=ImpactSuccessResponse)
def impact(payload: dict[str, Any]) -> JSONResponse:
    try:
        validated = validate_impact_input(payload)
    except ContractError as exc:
        return _error_response(exc.status, exc.message)

    repo_id = validated["repo_id"]
    try:
        repo_path = validate_repo_path(repo_id)
    except ContractError as exc:
        return _error_response(exc.status, exc.message)

    if not repo_path.exists() or not repo_path.is_dir():
        return _error_response(404, NOT_INDEXED_ERROR)

    if INDEXING_STUB == "A" and (repo_path / ".indexing").exists():
        return _error_response(409, INDEXING_ERROR)

    collection = _get_collection(repo_id)
    if collection is None:
        return _error_response(404, NOT_INDEXED_ERROR)

    function_name = validated["function_name"]
    all_matches = grep_function_references(repo_path=repo_path, function_name=function_name)

    definition_file = None
    if all_matches:
        definition_file = find_definition_file(
            repo_path=repo_path,
            all_matches=all_matches,
            function_name=function_name,
        )

    files_referencing = sorted(
        [path for path in all_matches.keys() if definition_file is None or path != definition_file]
    )
    # MUST be list not set.
    files_referencing = list(files_referencing)

    file_count = len(files_referencing)
    risk_level = _compute_risk_level(file_count)
    logger.info("impact risk_level=%s files_referencing_count=%d", risk_level, file_count)

    try:
        query_embedding = create_query_embedding(openai_client, function_name)
    except EmbeddingServiceError:
        return _error_response(503, EMBEDDING_ERROR)

    raw_vector_chunks, _raw_distances = retrieve_vector_chunks(
        collection=collection,
        repo_id=repo_id,
        query_embedding=query_embedding,
        target_results=6,
    )
    vector_chunks = build_impact_vector_chunks(raw_vector_chunks, start_index=1)

    if not all_matches:
        evidence_pack = [chunk.get("evidence_id", "?") for chunk in vector_chunks]
        logger.info("impact zero_match=true vector_chunks=%d", len(vector_chunks))
        zero_match_response = ImpactSuccessResponse(
            repo_id=repo_id,
            function_name=function_name,
            file_count=0,
            risk_level="Low",
            files_referencing=[],
            what_it_does=IMPACT_ZERO_MATCH_MESSAGE,
            evidence_pack=evidence_pack,
            chunks=vector_chunks,
            llm_fallback_used=False,
        )
        return JSONResponse(status_code=200, content=zero_match_response.model_dump())

    grep_chunks = build_grep_chunks(
        all_matches=all_matches,
        files_referencing=files_referencing,
        function_name=function_name,
    )

    merged_chunks = _merge_impact_chunks(vector_chunks=vector_chunks, grep_chunks=grep_chunks)
    evidence_pack = [chunk.get("evidence_id", "?") for chunk in merged_chunks]

    if not merged_chunks:
        logger.info("impact merged_chunks=0 llm_skipped=true")
        no_evidence_response = ImpactSuccessResponse(
            repo_id=repo_id,
            function_name=function_name,
            file_count=file_count,
            risk_level=risk_level,
            files_referencing=files_referencing,
            what_it_does=IMPACT_NO_EVIDENCE_MESSAGE,
            evidence_pack=evidence_pack,
            chunks=merged_chunks,
            llm_fallback_used=False,
        )
        return JSONResponse(status_code=200, content=no_evidence_response.model_dump())

    llm_fallback_used = False
    try:
        what_it_does = generate_impact_description(
            openai_client=openai_client,
            function_name=function_name,
            chunks=merged_chunks,
        )
    except LLMServiceError:
        what_it_does = IMPACT_LLM_FALLBACK_MESSAGE
        llm_fallback_used = True
        logger.warning("impact fallback triggered: LLMServiceError")
    except Exception:
        what_it_does = IMPACT_LLM_FALLBACK_MESSAGE
        llm_fallback_used = True
        logger.warning("impact fallback triggered: unexpected LLM exception")

    impact_response = ImpactSuccessResponse(
        repo_id=repo_id,
        function_name=function_name,
        file_count=file_count,
        risk_level=risk_level,
        files_referencing=files_referencing,
        what_it_does=what_it_does,
        evidence_pack=evidence_pack,
        chunks=merged_chunks,
        llm_fallback_used=llm_fallback_used,
    )
    return JSONResponse(status_code=200, content=impact_response.model_dump())
