from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_job(base_dir: Path, job_id: str, payload: dict[str, Any]) -> Path:
    job_dir = base_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    status = {
        "job_id": job_id,
        "state": "queued",
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
        "payload": payload,
        "steps": [],
        "error": None,
        "artifacts": {},
    }

    status_path = job_dir / "status.json"
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False))
    return status_path


def read_job_status(status_path: Path) -> dict[str, Any]:
    return json.loads(status_path.read_text())


def update_job_status(status_path: Path, *, state: str | None = None, step: dict[str, Any] | None = None, error: str | None = None, artifacts: dict[str, Any] | None = None) -> None:
    status = read_job_status(status_path)
    if state is not None:
        status["state"] = state
    if step is not None:
        status.setdefault("steps", []).append({"at": _utc_now_iso(), **step})
    if error is not None:
        status["error"] = error
    if artifacts is not None:
        status.setdefault("artifacts", {}).update(artifacts)
    status["updated_at"] = _utc_now_iso()
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False))
