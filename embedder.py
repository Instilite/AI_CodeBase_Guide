import os
from openai import OpenAI

api_key = "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"
api_key = api_key.strip().encode('ascii', 'ignore').decode('ascii')

client = OpenAI(api_key=api_key)

def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def embed_chunks(chunks: list[dict]) -> list[dict]:
    for chunk in chunks:
        chunk["embedding"] = embed_text(chunk["text"])
    return chunks