from fastapi import APIRouter, BackgroundTasks, Request, HTTPException

from config.settings import get_settings
from github.webhook_verify import verify_github_webhook
from pipeline.runner import create_job, run_job
from utils.logger import get_logger

router = APIRouter( tags=["webhook_listener"])

log = get_logger("healpipe.webhook")

@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        settings = get_settings()

        log.info("webhook received")

        verified = await verify_github_webhook(request, secret=settings.github_webhook_secret)
        if not verified:
            log.warning("webhook signature invalid")
            raise HTTPException(status_code=401, detail="invalid webhook signature")

        if settings.github_webhook_secret:
            log.info("webhook signature verified")

        payload = await request.json()

        run = payload.get("workflow_run")
        if not run:
            log.info("ignored webhook: no workflow_run")
            return {"status": "ignored", "message": "no workflow_run in payload"}

        conclusion = run.get("conclusion")
        run_id = run.get("id")
        head_sha = run.get("head_sha")

        repo_obj = payload.get("repository") or {}
        owner = ((repo_obj.get("owner") or {}).get("login")) or ""
        repo = repo_obj.get("name") or ""
        clone_url = repo_obj.get("clone_url") or (f"https://github.com/{owner}/{repo}.git" if owner and repo else "")

        if not run_id or not owner or not repo:
            log.warning("bad payload: missing run_id/owner/repo")
            raise HTTPException(status_code=400, detail="missing run_id/owner/repo in payload")

        if conclusion != "failure":
            log.info("ignored workflow_run: conclusion=%r owner=%s repo=%s run_id=%s", conclusion, owner, repo, run_id)
            return {"status": "ignored", "message": f"workflow conclusion is {conclusion!r}"}

        job_payload = {
            "owner": owner,
            "repo": repo,
            "run_id": run_id,
            "head_sha": head_sha,
            "clone_url": clone_url,
        }
        job_id, status_path = create_job(payload=job_payload, settings=settings)

        log.info("queued job_id=%s owner=%s repo=%s run_id=%s sha=%s", job_id, owner, repo, run_id, head_sha)

        background_tasks.add_task(
            run_job,
            job_id=job_id,
            status_path=status_path,
            owner=owner,
            repo=repo,
            run_id=int(run_id),
            head_sha=head_sha,
            clone_url=clone_url,
            settings=settings,
        )

        return {"status": "queued", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        log.exception("webhook processing error: %s", e)
        return {"status": "error", "message": "Failed to process webhook"}
    