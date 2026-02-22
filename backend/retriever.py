from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Dict, Iterable, List, Tuple

OVERVIEW_KEYWORDS = [
    "overview",
    "summarize",
    "summary",
    "explain the codebase",
    "what does this repo",
    "high level",
    "high-level",
    "architecture",
    "walkthrough",
    "overall structure",
]


def is_overview_query(question: str) -> bool:
    normalized = question.strip().lower()
    return any(keyword in normalized for keyword in OVERVIEW_KEYWORDS)


def similarity_from_distance(distance: float) -> float:
    similarity = 1.0 - float(distance)
    similarity = max(0.0, min(1.0, similarity))
    return round(similarity, 4)


def dedup_by_file_start(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    seen: set[Tuple[str, int]] = set()
    deduped: List[Dict[str, object]] = []

    for row in rows:
        key = (str(row.get("file_path", "")), int(row.get("start_line", 0)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    return deduped


def _select_with_cap(rows: List[Dict[str, object]], target: int, cap: int | None) -> List[Dict[str, object]]:
    selected: List[Dict[str, object]] = []
    per_file = defaultdict(int)

    for row in rows:
        file_path = str(row.get("file_path", ""))
        if cap is not None and per_file[file_path] >= cap:
            continue
        selected.append(row)
        per_file[file_path] += 1
        if len(selected) >= target:
            break

    return selected


def select_ask_rows(rows: List[Dict[str, object]], overview_mode: bool) -> List[Dict[str, object]]:
    deduped = dedup_by_file_start(rows)

    if overview_mode:
        selected = _select_with_cap(deduped, target=20, cap=2)
    else:
        selected = _select_with_cap(deduped, target=8, cap=4)
        if len(selected) < 8:
            selected = _select_with_cap(deduped, target=8, cap=5)
        if len(selected) < 8:
            selected = _select_with_cap(deduped, target=8, cap=None)

    selected_sorted = sorted(
        selected,
        key=lambda row: (
            -similarity_from_distance(float(row.get("distance", 1.0))),
            str(row.get("file_path", "")),
            int(row.get("start_line", 0)),
            int(row.get("end_line", 0)),
        ),
    )

    out: List[Dict[str, object]] = []
    for row in selected_sorted:
        out.append(
            {
                "file_path": str(row.get("file_path", "")),
                "start_line": int(row.get("start_line", 0)),
                "end_line": int(row.get("end_line", 0)),
                "text": str(row.get("text", "")),
                "similarity": similarity_from_distance(float(row.get("distance", 1.0))),
                "source": "vector",
            }
        )

    return out


def compute_confidence(chunks: List[Dict[str, object]]) -> Tuple[float, str]:
    if not chunks:
        return 0.0, "Low"

    similarities = [float(chunk.get("similarity", 0.0)) for chunk in chunks]
    confidence_score = round(float(mean(similarities)), 2)

    if confidence_score >= 0.55:
        label = "High"
    elif confidence_score >= 0.35:
        label = "Medium"
    else:
        label = "Low"

    return confidence_score, label


def assign_evidence_labels(chunks: List[Dict[str, object]]) -> List[Dict[str, object]]:
    labeled: List[Dict[str, object]] = []
    for i, chunk in enumerate(chunks, start=1):
        clone = dict(chunk)
        clone["evidence_id"] = f"E{i}"
        labeled.append(clone)
    return labeled


def select_impact_vector_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "file_path": str(row.get("file_path", "")),
                "start_line": int(row.get("start_line", 0)),
                "end_line": int(row.get("end_line", 0)),
                "text": str(row.get("text", "")),
                "similarity": similarity_from_distance(float(row.get("distance", 1.0))),
                "source": "vector",
            }
        )
    return out


def merge_impact_chunks(
    grep_chunks: List[Dict[str, object]],
    vector_chunks: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    merged: List[Dict[str, object]] = []
    seen: set[Tuple[str, int, int]] = set()

    for chunk in grep_chunks + vector_chunks:
        key = (
            str(chunk.get("file_path", "")),
            int(chunk.get("start_line", 0)),
            int(chunk.get("end_line", 0)),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(chunk)

    return merged
