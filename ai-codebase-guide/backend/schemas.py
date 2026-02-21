from typing import Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    status: Literal[400, 404, 409, 503]


class AskRequest(BaseModel):
    # Optional here so route-level validator can return contract 400 instead of framework 422.
    repo_id: str | None = None
    question: str | None = None
    mode: str | None = None


class ImpactRequest(BaseModel):
    # Optional here so route-level validator can return contract 400 instead of framework 422.
    repo_id: str | None = None
    function_name: str | None = None


class Claim(BaseModel):
    claim: str
    evidence: list[str]


class AskChunk(BaseModel):
    evidence_id: str
    chunk_id: str
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    text: str
    similarity: float


class ImpactChunk(BaseModel):
    evidence_id: str
    chunk_id: str
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    text: str
    similarity: float | None


class AskSuccessResponse(BaseModel):
    repo_id: str
    retrieval_mode: Literal["standard", "overview"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: Literal["high", "medium", "low"]
    claims: list[Claim]
    chunks: list[AskChunk]
    llm_fallback_used: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_id": "demo",
                "retrieval_mode": "standard",
                "confidence_score": 0.6142,
                "confidence_label": "high",
                "claims": [{"claim": "Example claim", "evidence": ["E1"]}],
                "chunks": [
                    {
                        "evidence_id": "E1",
                        "chunk_id": "chunk_demo_1",
                        "file_path": "src/main.py",
                        "start_line": 1,
                        "end_line": 10,
                        "text": "def main(): pass",
                        "similarity": 0.8341,
                    }
                ],
                "llm_fallback_used": False,
            }
        }
    }


class AskFallbackResponse(AskSuccessResponse):
    llm_fallback_used: Literal[True] = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_id": "demo",
                "retrieval_mode": "standard",
                "confidence_score": 0.4821,
                "confidence_label": "medium",
                "claims": [{"claim": "Analysis unavailable. Please retry.", "evidence": ["?"]}],
                "chunks": [
                    {
                        "evidence_id": "E1",
                        "chunk_id": "chunk_demo_1",
                        "file_path": "src/main.py",
                        "start_line": 1,
                        "end_line": 10,
                        "text": "def main(): pass",
                        "similarity": 0.5001,
                    }
                ],
                "llm_fallback_used": True,
            }
        }
    }


class ImpactSuccessResponse(BaseModel):
    repo_id: str
    function_name: str
    file_count: int = Field(ge=0)
    risk_level: Literal["Low", "Medium", "High"]
    files_referencing: list[str]
    what_it_does: str
    evidence_pack: list[str]
    chunks: list[ImpactChunk]
    llm_fallback_used: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_id": "demo",
                "function_name": "authenticate",
                "file_count": 3,
                "risk_level": "Medium",
                "files_referencing": ["api/routes.py", "services/user.py"],
                "what_it_does": "Validates user credentials.",
                "evidence_pack": ["E1"],
                "chunks": [
                    {
                        "evidence_id": "E1",
                        "chunk_id": "chunk_demo_2",
                        "file_path": "api/routes.py",
                        "start_line": 40,
                        "end_line": 90,
                        "text": "authenticate(user, pw)",
                        "similarity": 0.7821,
                    }
                ],
                "llm_fallback_used": False,
            }
        }
    }


class ImpactZeroMatchResponse(ImpactSuccessResponse):
    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_id": "demo",
                "function_name": "zzz_nonexistent",
                "file_count": 0,
                "risk_level": "Low",
                "files_referencing": [],
                "what_it_does": "Function not found via grep. Vector results shown only.",
                "evidence_pack": [],
                "chunks": [],
                "llm_fallback_used": False,
            }
        }
    }


class ImpactFallbackResponse(ImpactSuccessResponse):
    llm_fallback_used: Literal[True] = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "repo_id": "demo",
                "function_name": "authenticate",
                "file_count": 3,
                "risk_level": "Medium",
                "files_referencing": ["api/routes.py", "services/user.py"],
                "what_it_does": "LLM output unavailable.",
                "evidence_pack": ["E1"],
                "chunks": [
                    {
                        "evidence_id": "E1",
                        "chunk_id": "chunk_demo_2",
                        "file_path": "api/routes.py",
                        "start_line": 40,
                        "end_line": 90,
                        "text": "authenticate(user, pw)",
                        "similarity": 0.7821,
                    }
                ],
                "llm_fallback_used": True,
            }
        }
    }

