from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from config.settings import get_settings
from pipeline.job_store import read_job_status

router = APIRouter(tags=["jobs"])


@router.get("/jobs")
async def list_jobs():
    """List all jobs, most recent first."""
    settings = get_settings()
    jobs_dir = settings.artifacts_dir / "jobs"
    if not jobs_dir.exists():
        return []

    jobs = []
    for job_dir in sorted(jobs_dir.iterdir(), reverse=True):
        status_path = job_dir / "status.json"
        if status_path.exists():
            try:
                status = read_job_status(status_path)
                # Return a summary (not the full payload/artifacts)
                jobs.append({
                    "job_id": status.get("job_id"),
                    "state": status.get("state"),
                    "created_at": status.get("created_at"),
                    "updated_at": status.get("updated_at"),
                    "error": status.get("error"),
                    "owner": status.get("payload", {}).get("owner"),
                    "repo": status.get("payload", {}).get("repo"),
                    "run_id": status.get("payload", {}).get("run_id"),
                    "head_sha": status.get("payload", {}).get("head_sha"),
                    "steps": status.get("steps", []),
                    "pr_url": status.get("artifacts", {}).get("pr_url"),
                    "fix_summary": status.get("artifacts", {}).get("fix_summary"),
                })
            except Exception:
                continue

    return jobs


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    settings = get_settings()
    status_path = settings.artifacts_dir / "jobs" / job_id / "status.json"
    if not status_path.exists():
        raise HTTPException(status_code=404, detail="job not found")
    return read_job_status(status_path)


@router.get("/jobs/{job_id}/artifact")
async def get_job_artifact(job_id: str, path: str):
    settings = get_settings()
    job_dir = settings.artifacts_dir / "jobs" / job_id
    target = (job_dir / path).resolve()
    if not str(target).startswith(str(job_dir.resolve())):
        raise HTTPException(status_code=400, detail="invalid path")
    if not target.exists() or target.is_dir():
        raise HTTPException(status_code=404, detail="artifact not found")
    return {"path": str(target.relative_to(job_dir)), "content": target.read_text(encoding="utf-8", errors="ignore")}
