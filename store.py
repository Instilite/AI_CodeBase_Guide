import chromadb
from pathlib import Path

# PersistentClient means data survives server restarts
client = chromadb.PersistentClient(path="./chroma_db")


def get_collection(repo_id: str):
    return client.get_or_create_collection(
        name=f"repo_{repo_id}",
        metadata={"hnsw:space": "cosine"}
    )


def store_chunks(repo_id: str, chunks: list[dict]) -> int:
    """
    Store embedded chunks into ChromaDB.
    Each chunk must already have an 'embedding' key.
    Returns the number of chunks stored.
    """
    collection = get_collection(repo_id)

    ids        = []
    embeddings = []
    documents  = []
    metadatas  = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"chunk_{repo_id}_{i}"
        ids.append(chunk_id)
        embeddings.append(chunk["embedding"])
        documents.append(chunk["text"])
        metadatas.append({
            "repo_id"   : repo_id,
            "file_path" : chunk["file_path"],
            "start_line": chunk["start_line"],
            "end_line"  : chunk["end_line"],
        })

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    return len(ids)


def delete_repo(repo_id: str) -> bool:
    try:
        client.delete_collection(f"repo_{repo_id}")
        return True
    except Exception:
        return False