import io
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from ingest import validate_and_extract, ValidationError
from chunker import chunk_repo
from embedder import embed_chunks
from store import store_chunks, delete_repo

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs = {}


def index_repo(repo_id: str, repo_path: Path):
    """Full pipeline: chunk → embed → store"""
    try:
        # Step 1: Chunk
        chunks = chunk_repo(repo_path, repo_id)
        jobs[repo_id]["chunk_count"] = len(chunks)

        # Step 2: Embed
        chunks = embed_chunks(chunks)

        # Step 3: Store in ChromaDB
        store_chunks(repo_id, chunks)

        jobs[repo_id]["status"] = "complete"

    except Exception as e:
        jobs[repo_id]["status"] = "failed"
        jobs[repo_id]["error"] = str(e)


@app.get("/")
def root():
    return {"status": "backend is alive"}


@app.post("/upload")
async def upload_repo(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    zip_bytes = await file.read()

    try:
        repo_id, repo_path = validate_and_extract(zip_bytes)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    jobs[repo_id] = {
        "status": "indexing",
        "repo_id": repo_id,
        "chunk_count": 0,
        "error": None
    }

    background_tasks.add_task(index_repo, repo_id, repo_path)
    return {"job_id": repo_id, "status": "indexing"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/repos")
def list_repos():
    return list(jobs.values())


@app.delete("/repos/{repo_id}")
def remove_repo(repo_id: str):
    delete_repo(repo_id)
    if repo_id in jobs:
        del jobs[repo_id]
    return {"deleted": True}