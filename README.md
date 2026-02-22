# AI Codebase Guide

A two-tab web application for retrieval-augmented code analysis. Upload a repo, ask questions about it, and explore function-level impact — every answer surfaces the exact code chunks it used.

---

## Project Structure

```
/
├── frontend/          # Next.js web app (this README)
└── backend/           # FastAPI Python server
```

---

## Getting Started

You need **two terminals open at the same time** — one for the backend, one for the frontend.

### Terminal 1 — Backend (Python / FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend runs on **http://localhost:8000**.

> Before running, create a `.env` file inside the `backend/` folder:
> ```
> OPENAI_API_KEY=sk-your-key-here
> ```

### Terminal 2 — Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on **http://localhost:3000**.

> Create a `.env.local` file inside the `frontend/` folder if needed:
> ```
> OPENAI_API_KEY=sk-your-key-here
> ```

---

## How to Use

### 1. Upload a Repo
Click **Upload Repo** in the top bar and select a `.zip` file of the codebase you want to analyze. The backend will index it in the background — this may take a moment depending on the size.

### 2. Ask Tab
Type any natural language question about the codebase, or click one of the quick-select buttons. Hit Enter or the arrow button to submit. Results include:
- **Claims** — structured findings with evidence references (E1, E2...)
- **Evidence panel** — the exact code chunks used to generate the answer

### 3. Impact Tab
Enter a function name to see how widely it's referenced across the codebase. Results include:
- **Risk level** — Low / Medium / High based on how many files reference it
- **What it does** — one-line LLM description
- **Files referencing** — every file that calls this function
- **Evidence** — the code chunks retrieved for context

---

## Backend API

The backend exposes 7 endpoints. The frontend uses all of them.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — always returns `{ "status": "ok" }` |
| GET | `/repos` | List all indexed repos |
| POST | `/upload` | Upload a `.zip` file for indexing (returns `job_id` immediately) |
| GET | `/status/{job_id}` | Poll indexing progress |
| DELETE | `/repos/{repo_id}` | Delete a repo and its index |
| POST | `/ask` | Ask a question about a repo |
| POST | `/impact` | Analyze a function's impact across the repo |

### Upload flow
`POST /upload` accepts a `.zip` file (max 15 MB compressed / 200 MB uncompressed) and returns a `job_id` immediately. Indexing runs in the background. Poll `GET /status/{job_id}` until `status` is `"complete"` before querying.

### Ask request
```json
{
  "repo_id": "my_repo",
  "question": "How does authentication work?"
}
```

### Impact request
```json
{
  "repo_id": "my_repo",
  "function_name": "verify_credentials"
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React, plain CSS |
| Backend | FastAPI, Uvicorn, Python 3.11+ |
| Vector DB | ChromaDB (local, persists across restarts) |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |

---

## Important Notes

- The `chroma_db/` folder inside `backend/` is the local vector database. Don't delete it unless you want to re-index everything.
- Both `.env` (backend) and `.env.local` (frontend) are gitignored — never commit API keys.
- The backend must be running on port 8000 before the frontend can answer questions.
- Repos are identified by a sanitized version of the zip filename (e.g. `my_repo.zip` → `repo_id: my_repo`).

---

## Demo

To seed a demo repo without uploading a zip, run from inside the `backend/` folder:

```bash
python seed_demo_repo.py
```

This loads a small demo dataset into ChromaDB so you can test the Ask and Impact tabs immediately.
