# Frontend-Backend Integration (AI Codebase Guide)

## 1) Endpoints (exactly 7)

1. `GET /health`
2. `POST /upload`
3. `GET /status/{job_id}`
4. `GET /repos`
5. `DELETE /repos/{repo_id}`
6. `POST /ask`
7. `POST /impact`

No other endpoints are supported.

## 2) Request/Response Quick Reference

### `GET /health`
Response `200`:
```json
{ "status": "ok" }
```

### `POST /upload` (multipart form)
Form field: `file` (zip)

Response `202`:
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "repo_id": "my_repo",
  "status": "indexing"
}
```

### `GET /status/{job_id}`
Response `200`:
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "repo_id": "my_repo",
  "status": "indexing",
  "chunk_count": 412,
  "error": null
}
```

### `GET /repos`
Response `200`:
```json
[
  {
    "repo_id": "demo_repo",
    "name": "demo_repo.zip",
    "chunk_count": 1234,
    "indexed_at": "2026-02-21T08:00:00Z"
  }
]
```

### `DELETE /repos/{repo_id}`
Response `200`:
```json
{ "deleted": true, "repo_id": "demo_repo" }
```

### `POST /ask`
Request:
```json
{
  "repo_id": "demo_repo",
  "question": "How does authentication work?",
  "mode": "auto"
}
```
`mode` is accepted but ignored; backend always auto-detects overview via keyword rules.

Response `200`:
```json
{
  "repo_id": "demo_repo",
  "retrieval_mode": "standard",
  "confidence_score": 0.61,
  "confidence_label": "High",
  "claims": [
    {
      "claim": "JWT tokens are verified in auth middleware.",
      "evidence": ["E1", "E3"]
    }
  ],
  "chunks": [
    {
      "evidence_id": "E1",
      "file_path": "src/auth/middleware.py",
      "start_line": 42,
      "end_line": 85,
      "text": "def verify_jwt(token): ...",
      "similarity": 0.7812,
      "source": "vector"
    }
  ],
  "llm_fallback_used": false
}
```

Fallback A degraded success (`200`):
```json
{
  "repo_id": "demo_repo",
  "retrieval_mode": "standard",
  "confidence_score": 0.58,
  "confidence_label": "High",
  "claims": [],
  "chunks": [
    {
      "evidence_id": "E1",
      "file_path": "src/auth/middleware.py",
      "start_line": 42,
      "end_line": 85,
      "text": "...",
      "similarity": 0.78,
      "source": "vector"
    }
  ],
  "llm_fallback_used": true
}
```

### `POST /impact`
Request:
```json
{
  "repo_id": "demo_repo",
  "function_name": "verify_credentials"
}
```

Response `200`:
```json
{
  "repo_id": "demo_repo",
  "function_name": "verify_credentials",
  "risk_level": "Medium",
  "file_count": 2,
  "files_referencing": ["src/auth/routes.py", "tests/test_auth.py"],
  "what_it_does": "Validates username/password against the user store.",
  "message": null,
  "chunks": [
    {
      "evidence_id": "E1",
      "file_path": "src/auth/routes.py",
      "start_line": 18,
      "end_line": 38,
      "text": "result = verify_credentials(user, pw)",
      "similarity": null,
      "source": "grep"
    },
    {
      "evidence_id": "E2",
      "file_path": "src/auth/middleware.py",
      "start_line": 5,
      "end_line": 47,
      "text": "def verify_credentials(username, password): ...",
      "similarity": 0.7341,
      "source": "vector"
    }
  ],
  "llm_fallback_used": false
}
```

Zero-match degraded success (`200`):
```json
{
  "repo_id": "demo_repo",
  "function_name": "parse_token",
  "risk_level": "Low",
  "file_count": 0,
  "files_referencing": [],
  "what_it_does": "Decodes and validates a JWT string.",
  "message": "No exact word-boundary grep matches found. Showing semantic evidence only.",
  "chunks": [],
  "llm_fallback_used": false
}
```

Fallback A degraded success (`200`):
```json
{
  "repo_id": "demo_repo",
  "function_name": "verify_credentials",
  "risk_level": "Medium",
  "file_count": 2,
  "files_referencing": ["src/auth/routes.py", "src/auth/middleware.py"],
  "what_it_does": "",
  "message": null,
  "chunks": [
    {
      "evidence_id": "E1",
      "file_path": "src/auth/routes.py",
      "start_line": 18,
      "end_line": 38,
      "text": "...",
      "similarity": null,
      "source": "grep"
    }
  ],
  "llm_fallback_used": true
}
```

## 3) Error Model (canonical)

Every non-2xx response uses:
```json
{
  "error": "string_code",
  "message": "human readable",
  "repo_id": null,
  "details": null
}
```

### Error code registry

- `indexing_in_progress` -> `409`
  - `/repos`, `/ask`, `/impact`
- `repo_not_found` -> `404`
  - `/ask`, `/impact`, `DELETE /repos/{repo_id}`
- `job_not_found` -> `404`
  - `/status/{job_id}`
- `zip_too_large` -> `413`
  - `/upload`
- `zip_invalid` -> `422`
  - `/upload`
- `validation_error` -> `422`
  - request/body/path validation
- `internal_error` -> `500`
  - unhandled server faults

## 4) Indexing Guards and 409 Rules

### Stale marker cleanup rule (mandatory)
Before every 409 check, stale `.indexing` markers (`mtime > 1800s`) are deleted.

### Endpoints that can return 409
- `GET /repos`
- `POST /ask`
- `POST /impact`

### Endpoints that never return 409
- `GET /health`
- `GET /status/{job_id}`
- `DELETE /repos/{repo_id}`

### Existence oracle
`./repos/{repo_id}/repo_meta.json` is the only repo existence oracle.
If missing: repo is treated as not found.

## 5) Polling Flow

1. `POST /upload` -> immediately receive `{job_id, repo_id, status:"indexing"}`.
2. Poll `GET /status/{job_id}` until status is `complete` or `failed`.
3. If complete, call `GET /repos` to refresh selector.
4. Query with `POST /ask` and `POST /impact`.

## 6) Evidence Rendering Rules

- `evidence_id` labels are assigned after final chunk list freeze, before LLM call.
- Claims only cite those E-IDs.
- For grep chunks: `similarity` is **always `null`**.
- For vector chunks: `similarity` is `round(1 - cosine_distance, 4)`.

## 7) Confidence and Risk (Mechanical)

### `/ask` confidence
- `sim_i = 1 - chroma_cosine_distance_i`
- `confidence_score = round(mean(sim_i), 2)` from selected chunk list only
- labels:
  - `>= 0.55` -> `High`
  - `>= 0.35` -> `Medium`
  - `< 0.35` -> `Low`

### `/impact` risk
Risk is derived strictly from `file_count` (`files_referencing` length):
- `0-1` -> `Low`
- `2-3` -> `Medium`
- `>=4` -> `High`

LLM output never sets risk.

## 8) Runtime + Env + CORS

### Required env
- `OPENAI_API_KEY` (required for embeddings and LLM)
- Optional: `CORS_ALLOW_ORIGINS` comma-separated (default `*`)

### Run
```bash
python3 -m pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

## 9) Filesystem Schemas

### `repos/{repo_id}/repo_meta.json`
```json
{
  "repo_id": "demo_repo",
  "name": "demo_repo.zip",
  "indexed_at": "2026-02-21T12:00:00Z",
  "chunk_count": 1234
}
```

### `jobs/{job_id}.json`
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "repo_id": "demo_repo",
  "status": "indexing",
  "chunk_count": 412,
  "error": null
}
```

## 10) Key Backend Behaviors to Honor in UI

- `HTTP 200` with `llm_fallback_used=true` is degraded success, not an error.
- `/impact` zero-match shows a non-null `message`; all other impact responses use `message: null`.
- Delete is unconditional with respect to indexing marker (`.indexing` does not block `DELETE /repos/{repo_id}`).
