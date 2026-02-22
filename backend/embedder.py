from __future__ import annotations

import os
import time
from typing import Iterable, List, Sequence

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 64


class EmbeddingError(Exception):
    pass


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_batch(
    texts: Sequence[str],
    *,
    client: OpenAI | None = None,
    max_attempts: int = 3,
) -> List[List[float]]:
    if not texts:
        return []

    client = client or get_openai_client()
    delay_seconds = 0.5

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=list(texts))
            return [item.embedding for item in response.data]
        except Exception as exc:
            if attempt == max_attempts:
                raise EmbeddingError(f"Embedding API error: {exc}") from exc
            time.sleep(delay_seconds)
            delay_seconds *= 2

    raise EmbeddingError("Embedding API error: exhausted retries")


def batched(items: Sequence[dict], batch_size: int = EMBEDDING_BATCH_SIZE) -> Iterable[Sequence[dict]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]
