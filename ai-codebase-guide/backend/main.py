import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from openai import OpenAI

ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)

app = FastAPI(title="AI Codebase Guide API")

CHROMA_DB_PATH = "./chroma_db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _background_job(task_name: str) -> None:
    # Placeholder for future background task logic.
    _ = task_name


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "chroma_path": CHROMA_DB_PATH,
        "openai_configured": bool(OPENAI_API_KEY),
    }


@app.post("/tasks/demo")
def run_demo_task(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_background_job, "demo")
    return {"message": "Demo background task queued"}
