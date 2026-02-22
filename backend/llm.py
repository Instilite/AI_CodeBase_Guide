from __future__ import annotations

import json
import os
import traceback
from typing import Dict, List, Sequence, Tuple, Any

from openai import OpenAI

LLM_MODEL = "gpt-4o-mini"

# IMPORTANT:
# OpenAI json_schema response_format requires the TOP-LEVEL schema to be an OBJECT.
# So we wrap the claims array inside {"claims": [...] }.
SYSTEM_PROMPT = (
    "Use only the provided evidence chunks.\n"
    "Every claim must cite at least one evidence ID from the provided set.\n"
    "Return ONLY valid JSON. No prose.\n"
    'Return an object of shape: {"claims": [{"claim": "...", "evidence": ["E1","E3"]}]}.\n'
    "No other keys. No extra fields.\n"
)

_JSON_SCHEMA = {
    "name": "claims_object",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["claims"],
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["claim", "evidence"],
                    "properties": {
                        "claim": {"type": "string"},
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            }
        },
    },
}


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def _format_evidence(chunks: Sequence[Dict[str, object]]) -> str:
    lines: List[str] = []
    for chunk in chunks:
        evidence_id = chunk.get("evidence_id", "")
        file_path = chunk.get("file_path", "")
        start_line = chunk.get("start_line", 0)
        end_line = chunk.get("end_line", 0)
        text = chunk.get("text", "")
        lines.append(f"[{evidence_id}] {file_path}:{start_line}-{end_line}\n{text}")
    return "\n\n".join(lines)


def _call_llm_claims_object(
    *,
    user_prompt: str,
    client: OpenAI | None = None,
) -> str:
    """
    Returns raw model content expected to be a JSON OBJECT string:
      {"claims":[{"claim":"...","evidence":["E1"]}]}

    Tries json_schema response_format first.
    If that fails, falls back to plain mode but still requests the same JSON object shape.
    """
    client = client or get_openai_client()

    # Attempt 1: Structured JSON schema response_format (preferred)
    try:
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0,
            max_tokens=1000,
            response_format={"type": "json_schema", "json_schema": _JSON_SCHEMA},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content
        return content if content is not None else '{"claims":[]}'
    except Exception:
        # Log why structured mode failed, then try plain mode
        traceback.print_exc()

    # Attempt 2: Plain mode (no response_format). Still demand JSON-only object.
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = completion.choices[0].message.content
    return content if content is not None else '{"claims":[]}'


def _extract_claims_array(parsed: Any) -> list:
    """
    Enforce the top-level object wrapper: {"claims":[...]}.
    If shape is wrong, raise ValueError so caller triggers fallback.
    """
    if not isinstance(parsed, dict):
        raise ValueError("LLM returned non-object JSON (expected {'claims': [...]})")
    claims = parsed.get("claims")
    if not isinstance(claims, list):
        raise ValueError("LLM returned object without 'claims' array")
    return claims


def _normalize_claims(claim_items: Any, valid_evidence_ids: set[str]) -> List[Dict[str, object]]:
    """
    claim_items must be a list[dict] where each dict has:
      - claim: str
      - evidence: list[str]
    Filters out malformed entries and evidence IDs not in valid_evidence_ids.
    Raises if claim_items is not a list.
    """
    if not isinstance(claim_items, list):
        raise ValueError("LLM returned non-list claims")

    out: List[Dict[str, object]] = []
    for item in claim_items:
        if not isinstance(item, dict):
            continue

        claim_text = item.get("claim")
        evidence = item.get("evidence")

        if not isinstance(claim_text, str) or not isinstance(evidence, list):
            continue

        # Keep only evidence IDs that actually exist in our returned chunk list.
        evidence_ids = [
            eid for eid in evidence
            if isinstance(eid, str) and eid in valid_evidence_ids
        ]
        if not evidence_ids:
            continue

        out.append({"claim": claim_text.strip(), "evidence": evidence_ids})

    return out


def generate_ask_claims(
    *,
    question: str,
    chunks: Sequence[Dict[str, object]],
    client: OpenAI | None = None,
) -> Tuple[List[Dict[str, object]], bool]:
    """
    Returns (claims, llm_fallback_used).
    On ANY LLM error OR invalid JSON OR wrong JSON type => ([], True).
    """
    valid_ids = {str(chunk.get("evidence_id")) for chunk in chunks}
    evidence_block = _format_evidence(chunks)

    user_prompt = (
        "Answer the user question with concise, evidence-grounded claims.\n"
        f"Question: {question}\n\n"
        f"Evidence chunks:\n{evidence_block}\n\n"
        'Return JSON ONLY as: {"claims":[{"claim":"...","evidence":["E1"]}]}.\n'
        "Return 1-6 claims."
    )

    try:
        raw = _call_llm_claims_object(user_prompt=user_prompt, client=client)
        parsed = json.loads(raw)
        claim_items = _extract_claims_array(parsed)
        claims = _normalize_claims(claim_items, valid_ids)
        return claims, False
    except Exception:
        traceback.print_exc()
        return [], True


def generate_impact_summary(
    *,
    function_name: str,
    chunks: Sequence[Dict[str, object]],
    client: OpenAI | None = None,
) -> Tuple[str, bool]:
    """
    Returns (what_it_does, llm_fallback_used).
    On ANY LLM error OR invalid JSON OR wrong JSON type => ("", True).
    """
    valid_ids = {str(chunk.get("evidence_id")) for chunk in chunks}
    evidence_block = _format_evidence(chunks)

    user_prompt = (
        "Summarize what the function does based only on evidence.\n"
        f"Function: {function_name}\n\n"
        f"Evidence chunks:\n{evidence_block}\n\n"
        'Return JSON ONLY as: {"claims":[{"claim":"...","evidence":["E1"]}]}.\n'
        "Return at least 1 claim."
    )

    try:
        raw = _call_llm_claims_object(user_prompt=user_prompt, client=client)
        parsed = json.loads(raw)
        claim_items = _extract_claims_array(parsed)
        claims = _normalize_claims(claim_items, valid_ids)
        if not claims:
            return "", False
        return str(claims[0].get("claim", "")), False
    except Exception:
        traceback.print_exc()
        return "", True