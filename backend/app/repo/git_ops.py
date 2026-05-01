from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from utils.logger import get_logger


log = get_logger("healpipe.git")


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    log.debug("git cmd: %s", " ".join(cmd))
    t0 = time.monotonic()
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    log.debug("git cmd done rc=%s elapsed=%.2fs", result.returncode, time.monotonic() - t0)
    return result


def clone_repo(*, clone_url: str, dest_dir: Path, sha: Optional[str] = None, github_token: Optional[str] = None) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    log.info("git clone start url=%s dest=%s sha=%s", clone_url, dest_dir, sha)
    t0 = time.monotonic()

    cmd = ["git", "clone", "--no-tags", "--depth", "1", clone_url, str(dest_dir)]

    env = None
    if github_token and clone_url.startswith("https://github.com/"):
        # Avoid embedding tokens into the URL; use an auth header.
        basic = ("x-access-token:" + github_token).encode("utf-8")
        import base64

        header = "AUTHORIZATION: basic " + base64.b64encode(basic).decode("ascii")
        cmd = ["git", "-c", f"http.extraHeader={header}", "clone", "--no-tags", "--depth", "1", clone_url, str(dest_dir)]

    proc = _run(cmd)
    if proc.returncode != 0:
        log.error("git clone failed: %s", proc.stderr.strip()[:500])
        raise RuntimeError(f"git clone failed: {proc.stderr.strip()}")

    clone_elapsed = time.monotonic() - t0
    log.info("git clone done elapsed=%.2fs", clone_elapsed)

    if sha:
        log.info("git fetch+checkout sha=%s", sha)
        proc2 = _run(["git", "fetch", "--depth", "1", "origin", sha], cwd=dest_dir)
        if proc2.returncode != 0:
            log.error("git fetch sha failed: %s", proc2.stderr.strip()[:500])
            raise RuntimeError(f"git fetch sha failed: {proc2.stderr.strip()}")
        proc3 = _run(["git", "checkout", "--detach", sha], cwd=dest_dir)
        if proc3.returncode != 0:
            log.error("git checkout failed: %s", proc3.stderr.strip()[:500])
            raise RuntimeError(f"git checkout failed: {proc3.stderr.strip()}")
        log.info("git checkout sha=%s done", sha)

    log.info("git clone done dest=%s total_elapsed=%.2fs", dest_dir, time.monotonic() - t0)


def create_pr(*, repo_dir: Path, job_id: str, owner: str, repo: str, github_token: Optional[str], draft: bool = False) -> dict:
    """Create a branch, commit local changes, push, and open a GitHub PR.

    When *draft* is True the PR is created as a GitHub draft PR (useful when
    tests still fail so the fix can be reviewed manually).

    Returns a dict with keys: ok (bool), pr_url (str|None), error (str|None)
    """
    if not github_token:
        return {"ok": False, "error": "no github_token provided"}

    import base64
    import json
    import httpx

    branch = f"healpipe/fix/{job_id[:8]}"
    pr_kind = "draft PR" if draft else "PR"
    log.info("creating %s branch=%s owner=%s repo=%s", pr_kind, branch, owner, repo)

    # Create branch
    proc = _run(["git", "checkout", "-b", branch], cwd=repo_dir)
    if proc.returncode != 0:
        # If branch exists, try to checkout it
        proc2 = _run(["git", "checkout", branch], cwd=repo_dir)
        if proc2.returncode != 0:
            log.error("git checkout -b failed: %s", proc.stderr or proc.stdout)
            return {"ok": False, "error": f"git checkout -b failed: {proc.stderr or proc.stdout}"}

    # Add and commit
    _run(["git", "add", "-A"], cwd=repo_dir)

    commit_msg = f"Automated fix by healpipe for job {job_id}"
    if draft:
        commit_msg = f"[WIP] Automated fix attempt by healpipe for job {job_id}"

    commit = _run(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    if commit.returncode != 0:
        out = (commit.stdout or "") + (commit.stderr or "")
        if "nothing to commit" in out.lower():
            log.warning("nothing to commit for %s", pr_kind)
            return {"ok": False, "error": "no changes to commit"}
        log.error("git commit failed: %s", out.strip()[:500])
        return {"ok": False, "error": f"git commit failed: {out.strip()}"}

    # Push with http.extraHeader auth
    basic = ("x-access-token:" + github_token).encode("utf-8")
    header = "AUTHORIZATION: basic " + base64.b64encode(basic).decode("ascii")
    push = _run(["git", "-c", f"http.extraHeader={header}", "push", "-u", "origin", branch], cwd=repo_dir)
    if push.returncode != 0:
        log.error("git push failed: %s", (push.stderr or push.stdout).strip()[:500])
        return {"ok": False, "error": f"git push failed: {(push.stderr or push.stdout).strip()}"}

    log.info("pushed branch=%s, creating %s via API", branch, pr_kind)

    # Create PR via GitHub API
    api = "https://api.github.com"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github+json"}

    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(f"{api}/repos/{owner}/{repo}", headers=headers)
            if r.status_code != 200:
                return {"ok": False, "error": f"failed to fetch repo info: {r.status_code} {r.text}"}
            repo_info = r.json()
            base = repo_info.get("default_branch", "main")

            if draft:
                title = f"[healpipe] [WIP] Fix attempt ({job_id[:8]})"
                body = (
                    f"⚠️ **Draft PR** — Automated patch generated by Healpipe for job `{job_id}`.\n\n"
                    "Tests are **still failing** after this patch. This PR needs manual review and further fixes."
                )
            else:
                title = f"[healpipe] Automated fix ({job_id[:8]})"
                body = f"✅ Automated patch generated by Healpipe for job `{job_id}`. Tests passed in the sandbox."

            pr_body = {
                "title": title,
                "head": branch,
                "base": base,
                "body": body,
                "draft": draft,
            }

            r2 = client.post(f"{api}/repos/{owner}/{repo}/pulls", headers=headers, json=pr_body)
            if r2.status_code not in (200, 201):
                log.error("PR API failed: %s %s", r2.status_code, r2.text[:500])
                return {"ok": False, "error": f"failed to create PR: {r2.status_code} {r2.text}", "response": r2.text}
            pr = r2.json()
            log.info("%s created url=%s", pr_kind, pr.get("html_url"))
            return {"ok": True, "pr_url": pr.get("html_url")}
    except Exception as e:
        log.exception("%s creation exception: %s", pr_kind, e)
        return {"ok": False, "error": str(e)}

