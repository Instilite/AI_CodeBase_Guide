import re
from pathlib import Path
from typing import Any

from constants import get_repo_root_path

REPO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

ASK_VALIDATION_ERROR = "question must be a non-empty string (max 2000 chars)."
IMPACT_VALIDATION_ERROR = "function_name must be a non-empty string (max 200 chars)."


class ContractError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def sanitize_mode(mode: Any) -> str | None:
    if mode == "overview":
        return "overview"
    return None


def _validate_repo_id(repo_id: Any, error_message: str) -> str:
    if not isinstance(repo_id, str):
        raise ContractError(400, error_message)
    if REPO_ID_PATTERN.fullmatch(repo_id) is None:
        raise ContractError(400, error_message)
    return repo_id


def validate_ask_input(payload: dict[str, Any]) -> dict[str, str | None]:
    repo_id = _validate_repo_id(payload.get("repo_id"), ASK_VALIDATION_ERROR)

    question = payload.get("question")
    if not isinstance(question, str):
        raise ContractError(400, ASK_VALIDATION_ERROR)

    trimmed_question = question.strip()
    if not trimmed_question or len(trimmed_question) > 2000:
        raise ContractError(400, ASK_VALIDATION_ERROR)

    return {
        "repo_id": repo_id,
        "question": trimmed_question,
        "mode": sanitize_mode(payload.get("mode")),
    }


def validate_impact_input(payload: dict[str, Any]) -> dict[str, str]:
    repo_id = _validate_repo_id(payload.get("repo_id"), IMPACT_VALIDATION_ERROR)

    function_name = payload.get("function_name")
    if not isinstance(function_name, str):
        raise ContractError(400, IMPACT_VALIDATION_ERROR)

    trimmed_function_name = function_name.strip()
    if not trimmed_function_name or len(trimmed_function_name) > 200:
        raise ContractError(400, IMPACT_VALIDATION_ERROR)

    # Path traversal guard required by contract.
    validate_repo_path(repo_id)

    return {"repo_id": repo_id, "function_name": trimmed_function_name}


def validate_repo_path(repo_id: str) -> Path:
    repo_root = get_repo_root_path()
    repo_path = (repo_root / repo_id).resolve()

    if repo_path != repo_root and repo_root not in repo_path.parents:
        raise ContractError(400, IMPACT_VALIDATION_ERROR)

    return repo_path

