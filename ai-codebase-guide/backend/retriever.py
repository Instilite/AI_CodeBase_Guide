import math
from typing import Any

from constants import OVERVIEW_KEYWORDS


def determine_retrieval_mode(mode_flag: str | None, question: str) -> str:
    if mode_flag == "overview":
        return "overview"

    lowered_question = question.lower()
    for keyword in OVERVIEW_KEYWORDS:
        if keyword in lowered_question:
            return "overview"

    return "standard"


def compute_confidence(raw_distances: list[float]) -> tuple[float, str]:
    finite_distances = [distance for distance in raw_distances if isinstance(distance, float) and math.isfinite(distance)]
    if not finite_distances:
        return 0.0, "low"

    similarities = [1.0 - distance for distance in finite_distances]
    average = sum(similarities) / len(similarities)
    if average < 0.0:
        average = 0.0
    if average > 1.0:
        average = 1.0
    average = round(average, 4)

    if average >= 0.55:
        return average, "high"
    if average >= 0.35:
        return average, "medium"
    return average, "low"


def _coerce_line_number(value: Any, default: int) -> int:
    try:
        parsed = int(value)
        if parsed < 1:
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def _extract_raw_chunks(query_result: dict) -> tuple[list[dict[str, Any]], list[float]]:
    raw_chunks: list[dict[str, Any]] = []
    raw_distances: list[float] = []

    documents = query_result.get("documents", [[]])
    metadatas = query_result.get("metadatas", [[]])
    distances = query_result.get("distances", [[]])
    ids = query_result.get("ids", [[]])

    if not documents or not documents[0]:
        return [], []

    for i in range(len(documents[0])):
        doc = documents[0][i]
        meta = metadatas[0][i] if metadatas and metadatas[0] else {}
        dist = distances[0][i] if distances and distances[0] else None
        chunk_id = ids[0][i] if ids and ids[0] else meta.get("chunk_id", "")

        raw_chunks.append(
            {
                "chunk_id": chunk_id,
                "file_path": meta.get("file_path", ""),
                "start_line": meta.get("start_line", 1),
                "end_line": meta.get("end_line", 1),
                "text": doc,
            }
        )

        if dist is not None:
            raw_distances.append(dist)

    return raw_chunks, raw_distances


def retrieve_vector_chunks(
    collection: Any,
    repo_id: str,
    query_embedding: list[float],
    target_results: int,
) -> tuple[list[dict[str, Any]], list[float]]:
    try:
        total_count = int(collection.count())
    except Exception:
        return [], []

    n_results = min(target_results, total_count)
    if n_results <= 0:
        return [], []

    try:
        query_result = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],  # FIX: remove "ids"
        )
    except Exception as e:
        print("CHROMA QUERY FAILED:", type(e).__name__, e)  # TEMP DEBUG (leave for now)
        return [], []

    return _extract_raw_chunks(query_result)


def _apply_diversity_cap(raw_chunks: list[dict[str, Any]], retrieval_mode: str) -> list[dict[str, Any]]:
    if not raw_chunks:
        return []

    distinct_files = {chunk["file_path"] for chunk in raw_chunks}
    should_cap = retrieval_mode == "overview" or (
        retrieval_mode == "standard" and len(distinct_files) >= 3
    )

    if not should_cap:
        return raw_chunks

    by_file: dict[str, list[tuple[int, float]]] = {}
    for idx, chunk in enumerate(raw_chunks):
        by_file.setdefault(chunk["file_path"], []).append((idx, float(chunk["distance"])))

    selected_indices: dict[int, bool] = {}
    for entries in by_file.values():
        entries.sort(key=lambda item: item[1])
        for idx, _distance in entries[:2]:
            selected_indices[idx] = True

    filtered: list[dict[str, Any]] = []
    for idx, chunk in enumerate(raw_chunks):
        if selected_indices.get(idx, False):
            filtered.append(chunk)
    return filtered


def _distance_to_similarity(distance: float | None) -> float:
    if distance is None:
        return 0.0
    try:
        d = float(distance)
    except Exception:
        return 0.0
    if not math.isfinite(d):
        return 0.0
    sim = 1.0 - d
    if sim < 0.0:
        sim = 0.0
    if sim > 1.0:
        sim = 1.0
    return round(sim, 4)


def build_ask_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    response_chunks: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks, start=1):
        start_line = _coerce_line_number(chunk.get("start_line"), 1)
        end_line = _coerce_line_number(chunk.get("end_line"), start_line)
        if end_line < start_line:
            end_line = start_line

        try:
            distance = float(chunk.get("distance", 1.0))
        except (TypeError, ValueError):
            distance = 1.0

        response_chunks.append(
            {
                "evidence_id": f"E{idx}",
                "chunk_id": str(chunk.get("chunk_id", "")),
                "file_path": str(chunk.get("file_path", "")),
                "start_line": start_line,
                "end_line": end_line,
                "text": str(chunk.get("text", "")),
                "similarity": _distance_to_similarity(distance),
            }
        )
    return response_chunks


def build_impact_vector_chunks(
    raw_chunks: list[dict[str, Any]], start_index: int = 1
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    next_idx = start_index

    for raw_chunk in raw_chunks:
        start_line = _coerce_line_number(raw_chunk.get("start_line"), 1)
        end_line = _coerce_line_number(raw_chunk.get("end_line"), start_line)
        if end_line < start_line:
            end_line = start_line

        try:
            distance = float(raw_chunk.get("distance", 1.0))
        except (TypeError, ValueError):
            distance = 1.0

        chunk = {
            "evidence_id": f"E{next_idx}",
            "chunk_id": str(raw_chunk.get("chunk_id", "")),
            "file_path": str(raw_chunk.get("file_path", "")),
            "start_line": start_line,
            "end_line": end_line,
            "text": str(raw_chunk.get("text", "")),
            "similarity": float(_distance_to_similarity(distance)),
        }
        chunks.append(chunk)
        next_idx += 1

    return chunks


def run_ask_retrieval(
    collection: Any,
    repo_id: str,
    question: str,
    mode_flag: str | None,
    query_embedding: list[float],
) -> dict[str, Any]:
    retrieval_mode = determine_retrieval_mode(mode_flag, question)
    target_results = 20 if retrieval_mode == "overview" else 8

    raw_chunks, raw_distances = retrieve_vector_chunks(
        collection=collection,
        repo_id=repo_id,
        query_embedding=query_embedding,
        target_results=target_results,
    )

    confidence_score, confidence_label = compute_confidence(raw_distances)
    capped_chunks = _apply_diversity_cap(raw_chunks, retrieval_mode)
    response_chunks = build_ask_chunks(capped_chunks)

    return {
        "retrieval_mode": retrieval_mode,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "chunks": response_chunks,
    }
