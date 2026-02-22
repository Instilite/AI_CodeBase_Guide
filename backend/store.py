from __future__ import annotations

from typing import Dict, List, Sequence

import chromadb
from chromadb.api.models.Collection import Collection


def get_persistent_client(path: str = "./chroma_db") -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=path)


def collection_name(repo_id: str) -> str:
    return f"repo_{repo_id}"


def get_or_create_repo_collection(client: chromadb.PersistentClient, repo_id: str) -> Collection:
    # Mandatory invariant: every get_or_create_collection call sets cosine distance.
    return client.get_or_create_collection(
        name=collection_name(repo_id),
        metadata={"hnsw:space": "cosine"},
    )


def get_repo_collection(client: chromadb.PersistentClient, repo_id: str) -> Collection:
    return client.get_collection(name=collection_name(repo_id))


def upsert_batch(
    collection: Collection,
    chunks: Sequence[Dict[str, object]],
    embeddings: Sequence[Sequence[float]],
) -> None:
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, object]] = []

    for chunk in chunks:
        ids.append(str(chunk["id"]))
        documents.append(str(chunk["text"]))
        metadatas.append(
            {
                "repo_id": chunk["repo_id"],
                "file_path": chunk["file_path"],
                "start_line": int(chunk["start_line"]),
                "end_line": int(chunk["end_line"]),
                "chunk_index": int(chunk["chunk_index"]),
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=[list(vector) for vector in embeddings],
    )


def query_collection(
    collection: Collection,
    query_embedding: Sequence[float],
    n_results: int,
) -> List[Dict[str, object]]:
    result = collection.query(
        query_embeddings=[list(query_embedding)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    rows: List[Dict[str, object]] = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        rows.append(
            {
                "text": document,
                "file_path": metadata.get("file_path"),
                "start_line": int(metadata.get("start_line", 0)),
                "end_line": int(metadata.get("end_line", 0)),
                "distance": float(distance),
                "source": "vector",
            }
        )
    return rows


def delete_collection_if_exists(client: chromadb.PersistentClient, repo_id: str) -> None:
    try:
        client.delete_collection(name=collection_name(repo_id))
    except Exception:
        return


def get_collection_count(client: chromadb.PersistentClient, repo_id: str) -> int:
    collection = get_repo_collection(client, repo_id)
    return int(collection.count())
