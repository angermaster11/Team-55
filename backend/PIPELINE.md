# Healpipe CI Fix Pipeline (Webhook → Docker → Patch → Re-test)

## What it does

- Receives GitHub `workflow_run` webhooks at `POST /webhook`
- On `conclusion == "failure"` it creates a `job_id` and runs a background job:
  - downloads Actions logs
  - extracts error contexts
  - clones the repo at `head_sha`
  - runs `pytest` inside a Docker sandbox
  - (optional) asks an LLM for a unified diff patch and applies it
  - re-runs tests
- Job status is available at `GET /jobs/{job_id}`

## Required env vars

Set these in your shell (or `backend/app/.env`):

- `HEALPIPE_GITHUB_TOKEN` (required): GitHub token for downloading Actions logs (and cloning private repos)
- `HEALPIPE_GITHUB_WEBHOOK_SECRET` (recommended): used to verify `X-Hub-Signature-256`
- `HEALPIPE_LLM_API_KEY` (optional): enables patch generation
- `HEALPIPE_LLM_BASE_URL` (optional): OpenAI-compatible base URL
- `HEALPIPE_LLM_MODEL` (optional)

Optional:

- `HEALPIPE_DOCKER_IMAGE` (default: `python:3.11-slim`)

## Build sandbox image (recommended)

```bash
cd backend
docker build -t healpipe-sandbox:latest -f sandbox/Dockerfile sandbox
export HEALPIPE_DOCKER_IMAGE=healpipe-sandbox:latest
```

## Run API

```bash
cd backend/app
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Debug

- Artifacts are written under `backend/app/artifacts/jobs/{job_id}/`
- View status: `GET /jobs/{job_id}`
- View text artifact: `GET /jobs/{job_id}/artifact?path=logs/raw_logs.txt`
