from typing import Any
import os

from openai import OpenAIError

EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingServiceError(Exception):
    pass


def create_query_embedding(openai_client: Any, text: str) -> list[float]:
    if openai_client is None:
        raise EmbeddingServiceError("OpenAI client is not configured.")

    # 🔎 Diagnostic: check if server sees API key
    print("SERVER KEY:", os.getenv("OPENAI_API_KEY"))

    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        embedding = response.data[0].embedding
    except OpenAIError as exc:
        raise EmbeddingServiceError("Embedding call failed.") from exc
    except Exception as exc:
        raise EmbeddingServiceError("Embedding call failed.") from exc

    if not isinstance(embedding, list):
        raise EmbeddingServiceError("Invalid embedding response.")

    return embedding
