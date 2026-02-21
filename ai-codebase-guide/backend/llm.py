import json
import os
from typing import Any

from openai import OpenAIError

LLM_MODEL = "gpt-4o-mini"


class LLMServiceError(Exception):
    pass


def _build_evidence_text(chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for chunk in chunks:
        evidence_id = str(chunk.get("evidence_id", "?"))
        file_path = str(chunk.get("file_path", ""))
        start_line = int(chunk.get("start_line", 1))
        end_line = int(chunk.get("end_line", start_line))
        text = str(chunk.get("text", ""))
        lines.append(
            f"{evidence_id} | {file_path}:{start_line}-{end_line}\n{text}"
        )
    return "\n\n".join(lines)


def generate_ask_claims(
    openai_client: Any, question: str, chunks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if os.getenv("FORCE_LLM_FAILURE") == "1":
        raise LLMServiceError("Forced LLM failure.")

    if openai_client is None:
        raise LLMServiceError("OpenAI client is not configured.")

    evidence_text = _build_evidence_text(chunks)
    if not evidence_text.strip():
        raise LLMServiceError("Evidence text is empty.")

    safe_question = question.replace("\\", "\\\\").replace('"', '\\"')
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict JSON generator. Use ONLY the provided evidence. "
                "Return JSON object with key 'claims' only. "
                "Each item in claims must be: "
                "{\"claim\": \"string\", \"evidence\": [\"E1\", \"E2\"]}."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {safe_question}\n\n"
                f"Evidence:\n{evidence_text}\n\n"
                "Return JSON now."
            ),
        },
    ]

    try:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=messages,
        )
        raw_text = response.choices[0].message.content or ""
    except OpenAIError as exc:
        raise LLMServiceError("LLM API error.") from exc
    except Exception as exc:
        raise LLMServiceError("LLM API error.") from exc

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise LLMServiceError("LLM JSON parse failed.") from exc

    claims = parsed.get("claims", None)
    if not isinstance(claims, list):
        raise LLMServiceError("Missing or invalid claims.")

    valid_ids = {str(chunk.get("evidence_id", "?")) for chunk in chunks}
    sanitized_claims: list[dict[str, Any]] = []
    for claim_obj in claims:
        if not isinstance(claim_obj, dict):
            raise LLMServiceError("Invalid claim item.")

        claim_text = claim_obj.get("claim")
        evidence = claim_obj.get("evidence")
        if not isinstance(claim_text, str) or not claim_text.strip():
            raise LLMServiceError("Invalid claim text.")
        if not isinstance(evidence, list):
            raise LLMServiceError("Invalid evidence list.")

        clean_evidence: list[str] = []
        for evidence_id in evidence:
            if isinstance(evidence_id, str) and (evidence_id in valid_ids or evidence_id == "?"):
                clean_evidence.append(evidence_id)
        if not clean_evidence:
            clean_evidence = ["?"]

        sanitized_claims.append({"claim": claim_text.strip(), "evidence": clean_evidence})

    return sanitized_claims


def generate_impact_description(
    openai_client: Any, function_name: str, chunks: list[dict[str, Any]]
) -> str:
    if os.getenv("FORCE_LLM_FAILURE") == "1":
        raise LLMServiceError("Forced LLM failure.")

    if openai_client is None:
        raise LLMServiceError("OpenAI client is not configured.")

    evidence_text = _build_evidence_text(chunks)
    if not evidence_text.strip():
        raise LLMServiceError("Evidence text is empty.")

    safe_function_name = function_name.replace("\\", "\\\\").replace('"', '\\"')
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict JSON generator. Use ONLY the evidence provided. "
                "Return exactly one JSON object with this key: "
                "{\"what_it_does\": \"string\"}."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Function name: {safe_function_name}\n\n"
                f"Evidence:\n{evidence_text}\n\n"
                "Return JSON now."
            ),
        },
    ]

    try:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=messages,
        )
        raw_text = response.choices[0].message.content or ""
    except OpenAIError as exc:
        raise LLMServiceError("LLM API error.") from exc
    except Exception as exc:
        raise LLMServiceError("LLM API error.") from exc

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise LLMServiceError("LLM JSON parse failed.") from exc

    what_it_does = parsed.get("what_it_does")
    if not isinstance(what_it_does, str):
        raise LLMServiceError("Missing what_it_does.")

    cleaned = what_it_does.strip()
    if not cleaned:
        return "Description unavailable."
    return cleaned
