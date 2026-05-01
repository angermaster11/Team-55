from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from config.settings import Settings, get_settings
from pipeline.job_store import init_job, update_job_status
from repo.git_ops import clone_repo
from repo.git_ops import create_pr
from sandbox.docker_runner import run_in_docker
from utils.error_extractor import extract_errors
from utils.log_fetcher import get_logs
from agents.bugfix_graph import generate_patch, apply_edits, generate_fix_summary
from utils.logger import get_logger
from pipeline.autofix import apply_autofixes


log = get_logger("healpipe.pipeline")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_effective_unified_diff(patch: str) -> bool:
    if not patch:
        return False
    return ("diff --git " in patch) or ("--- " in patch and "+++ " in patch)


def _strip_file_from_unified_diff(patch: str, *, file_path: str) -> str:
    """Remove all diff blocks that modify the given file path."""
    if not patch:
        return patch

    out_lines: list[str] = []
    lines = patch.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            block_start = i
            i += 1
            while i < len(lines) and not lines[i].startswith("diff --git "):
                i += 1
            block = "".join(lines[block_start:i])
            if f" a/{file_path} " in block.splitlines()[0] or f" b/{file_path}" in block.splitlines()[0]:
                continue
            out_lines.append(block)
        else:
            out_lines.append(line)
            i += 1

    return "".join(out_lines)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="ignore")


def _tail(text: str | None, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _collect_relevant_file_context(repo_dir: Path, *, output_text: str, max_files: int = 6, max_chars_per_file: int = 6000) -> str:
    repo_root = repo_dir.resolve()

    candidates: set[str] = set()
    for fixed in ("app.py", "main.py"):
        if (repo_dir / fixed).is_file():
            candidates.add(fixed)

    for m in re.finditer(r"FAILED\s+([^\s:]+\.py)::", output_text or ""):
        candidates.add(m.group(1))
    for m in re.finditer(r"([A-Za-z0-9_./-]+\.py):\d+", output_text or ""):
        candidates.add(m.group(1))

    cleaned: list[Path] = []
    for c in sorted(candidates):
        c2 = c.strip().replace("\\", "/")
        if c2.startswith("/work/"):
            c2 = c2[len("/work/"):]
        c2 = c2.lstrip("./")
        if not c2 or c2.startswith("/") or ".." in c2.split("/"):
            continue
        p = (repo_dir / c2).resolve()
        if not p.is_file():
            continue
        try:
            p.relative_to(repo_root)
        except Exception:
            continue
        cleaned.append(p)
        if len(cleaned) >= max_files:
            break

    if not cleaned:
        return ""

    parts: list[str] = []
    for p in cleaned:
        rel = str(p.relative_to(repo_root))
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if len(txt) > max_chars_per_file:
            txt = txt[:max_chars_per_file] + "\n... (truncated)\n"
        parts.append(f"--- {rel} ---\n{txt}")
    return "\n\n".join(parts)


_HUNK_RE = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")


def _normalize_unified_diff_hunk_counts(patch: str) -> tuple[str, dict[str, int]]:
    """Fix incorrect unified-diff hunk counts (common LLM mistake)."""
    if not _is_effective_unified_diff(patch):
        return patch, {"hunks_seen": 0, "hunks_rewritten": 0}

    lines = patch.splitlines(keepends=True)
    out: list[str] = []
    stats = {"hunks_seen": 0, "hunks_rewritten": 0}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _HUNK_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        stats["hunks_seen"] += 1
        old_start = int(m.group(1))
        new_start = int(m.group(3))
        old_count_decl = int(m.group(2) or "1")
        new_count_decl = int(m.group(4) or "1")

        j = i + 1
        old_count_act = 0
        new_count_act = 0
        while j < len(lines):
            nxt = lines[j]
            if nxt.startswith("diff --git "):
                break
            if _HUNK_RE.match(nxt):
                break
            if nxt.startswith("@@ "):
                break
            if nxt.startswith("\\"):
                j += 1
                continue
            if nxt.startswith("+"):
                new_count_act += 1
            elif nxt.startswith("-"):
                old_count_act += 1
            else:
                old_count_act += 1
                new_count_act += 1
            j += 1

        if old_count_act <= 0:
            old_count_act = old_count_decl
        if new_count_act <= 0:
            new_count_act = new_count_decl

        if old_count_act != old_count_decl or new_count_act != new_count_decl:
            stats["hunks_rewritten"] += 1
            out.append(f"@@ -{old_start},{old_count_act} +{new_start},{new_count_act} @@\n")
        else:
            out.append(line)

        out.extend(lines[i + 1 : j])
        i = j

    return "".join(out), stats


def _git_apply(repo_dir: Path, patch: str) -> tuple[bool, str]:
    if not _is_effective_unified_diff(patch):
        return True, "No changes to apply (empty/ineffective diff)."

    if patch and not patch.endswith("\n"):
        patch = patch + "\n"

    log.debug("git apply: patch size=%d bytes", len(patch))

    check = subprocess.run(
        ["git", "apply", "--check", "--whitespace=nowarn", "-"],
        cwd=str(repo_dir),
        input=patch,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check.returncode != 0:
        msg = (check.stderr or check.stdout)
        log.warning("git apply --check failed: %s", (msg or "").strip()[:300])

        if ("patch does not apply" in (msg or "")) or ("patch failed" in (msg or "")):
            try:
                proc2 = subprocess.run(
                    ["patch", "-p1", "--batch", "--forward", "--fuzz=3"],
                    cwd=str(repo_dir),
                    input=patch,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError:
                return False, "git apply --check failed:\n" + msg + "\n\n(no 'patch' utility available for fallback)"

            out = (proc2.stdout or "") + (proc2.stderr or "")
            if proc2.returncode == 0:
                log.info("patch applied via 'patch' utility fallback")
                return True, "applied via 'patch' utility (git apply --check failed first)\n" + out
            return False, "git apply --check failed:\n" + msg + "\n\n'patch' fallback failed (rc=%s):\n%s" % (proc2.returncode, out)

        return False, "git apply --check failed:\n" + msg

    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=str(repo_dir),
        input=patch,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode == 0:
        log.info("git apply succeeded")
    else:
        log.warning("git apply failed after --check passed: %s", (proc.stderr or "").strip()[:300])
    return proc.returncode == 0, (proc.stderr or proc.stdout)


# ---------------------------------------------------------------------------
# Sandbox test runner  (PERFORMANCE-OPTIMIZED)
# ---------------------------------------------------------------------------

_VENV_DIR = "/work/.healpipe_venv"
_PIP_CACHE = "/work/.pip_cache"
_PIP_FLAGS = f"--quiet --no-compile --cache-dir {_PIP_CACHE} --disable-pip-version-check"


def _build_test_cmd(*, reuse_venv: bool, repo_dir: Path | None = None) -> str:
    """Build the shell command for running tests inside a Docker container.

    When *reuse_venv* is True the existing virtualenv (from a prior run) is
    activated directly — skipping venv creation and saving ~60-120 s of pip
    install time.

    Smartly detects the test framework and project structure to handle
    Flask, LangChain, Django, and any Python project.
    """
    # Detect what install commands we need
    install_parts = []
    install_parts.append(f"(test -f requirements.txt && pip install {_PIP_FLAGS} -r requirements.txt || true)")
    install_parts.append(f"(test -f requirements-dev.txt && pip install {_PIP_FLAGS} -r requirements-dev.txt || true)")
    install_parts.append(f"(test -f setup.py && pip install {_PIP_FLAGS} -e . || true)")
    install_parts.append(f"(test -f pyproject.toml && pip install {_PIP_FLAGS} -e . || true)")
    install_cmd = " && ".join(install_parts)

    # Detect the test runner — try pytest first, fall back to unittest
    test_cmd = (
        "if python -m pytest --version > /dev/null 2>&1; then "
        "  python -m pytest -q --tb=short; "
        "elif test -f manage.py; then "
        "  python manage.py test --verbosity=1; "
        "else "
        "  python -m unittest discover -v; "
        "fi"
    )

    if reuse_venv:
        return (
            f". {_VENV_DIR}/bin/activate && "
            f"{install_cmd} && "
            f"{test_cmd}"
        )

    return (
        f"python -m venv {_VENV_DIR} && "
        f". {_VENV_DIR}/bin/activate && "
        f"pip install {_PIP_FLAGS} pytest && "
        f"{install_cmd} && "
        f"{test_cmd}"
    )


def _run_tests_in_sandbox(repo_dir: Path, *, settings: Settings, reuse_venv: bool = False) -> dict[str, Any]:
    cmd = _build_test_cmd(reuse_venv=reuse_venv)

    log.info("sandbox cmd reuse_venv=%s cmd_len=%d", reuse_venv, len(cmd))

    result = run_in_docker(
        image=settings.docker_image,
        repo_dir=repo_dir,
        command=cmd,
        env={
            "HOME": "/tmp",
            "PIP_CACHE_DIR": _PIP_CACHE,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        cpus=settings.docker_cpus,
        memory=settings.docker_memory,
        pids_limit=settings.docker_pids_limit,
        timeout_seconds=settings.docker_timeout_seconds,
    )

    return {
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": " ".join(result.command),
        "elapsed_seconds": result.elapsed_seconds,
    }


def _cleanup_sandbox_artifacts(repo_dir: Path) -> None:
    """Remove transient sandbox files from the repo directory."""
    for name in (".healpipe_venv", ".pip_cache"):
        p = repo_dir / name
        if p.exists():
            try:
                shutil.rmtree(p)
                log.debug("cleaned up %s", p)
            except Exception:
                log.debug("cleanup failed for %s (non-critical)", p, exc_info=True)


# ---------------------------------------------------------------------------
# Job lifecycle
# ---------------------------------------------------------------------------

def create_job(*, payload: dict[str, Any], settings: Optional[Settings] = None) -> tuple[str, Path]:
    import uuid

    s = settings or get_settings()
    job_id = uuid.uuid4().hex
    status_path = init_job(s.artifacts_dir, job_id, payload)
    return job_id, status_path


def run_job(*, job_id: str, status_path: Path, owner: str, repo: str, run_id: int, head_sha: str | None, clone_url: str, settings: Optional[Settings] = None) -> None:
    s = settings or get_settings()

    job_started = time.monotonic()
    log.info("job start job_id=%s owner=%s repo=%s run_id=%s sha=%s", job_id, owner, repo, run_id, head_sha)

    job_dir = status_path.parent
    repo_dir = job_dir / "repo"
    artifacts: dict[str, Any] = {
        "job_dir": str(job_dir),
        "repo_dir": str(repo_dir),
        "logs_dir": str(job_dir / "logs"),
        "test_dir": str(job_dir / "tests"),
    }

    try:
        update_job_status(status_path, state="running", step={"name": "start"}, artifacts=artifacts)

        # ── 1) Download GitHub Actions logs ──────────────────────────
        update_job_status(status_path, step={"name": "download_logs"})
        t0 = time.monotonic()
        log.info("job_id=%s step=download_logs", job_id)
        logs_out = get_logs(owner, repo, run_id, dest_dir=str(job_dir / "logs"))
        if not logs_out.get("ok"):
            raise RuntimeError(f"Failed to fetch logs: {logs_out.get('error')}")
        log.info("job_id=%s step=download_logs done_s=%.2f", job_id, time.monotonic() - t0)

        combined_path = Path(logs_out["combined_path"])
        combined_text = logs_out.get("combined_text", "")
        log.info("job_id=%s logs_size=%d chars", job_id, len(combined_text))
        update_job_status(status_path, artifacts={"combined_logs_path": str(combined_path)})

        # ── 2) Parse errors from logs ────────────────────────────────
        update_job_status(status_path, step={"name": "extract_errors"})
        t0 = time.monotonic()
        log.info("job_id=%s step=extract_errors", job_id)
        errors = extract_errors(combined_text)
        _write_text(job_dir / "logs" / "errors.json", json.dumps(errors, indent=2, ensure_ascii=False))
        update_job_status(status_path, artifacts={"errors_path": str(job_dir / 'logs' / 'errors.json')})
        err_count = len(errors) if isinstance(errors, list) else "?"
        log.info("job_id=%s step=extract_errors count=%s done_s=%.2f", job_id, err_count, time.monotonic() - t0)

        # ── 3) Clone repo at SHA ─────────────────────────────────────
        update_job_status(status_path, step={"name": "clone_repo"})
        t0 = time.monotonic()
        log.info("job_id=%s step=clone_repo clone_url=%s", job_id, clone_url)
        clone_repo(clone_url=clone_url, dest_dir=repo_dir, sha=head_sha, github_token=s.github_token)
        log.info("job_id=%s step=clone_repo done_s=%.2f", job_id, time.monotonic() - t0)

        # ── 3b) Apply deterministic autofixes ────────────────────────
        update_job_status(status_path, step={"name": "autofix"})
        t0 = time.monotonic()
        log.info("job_id=%s step=autofix", job_id)
        autofix = apply_autofixes(repo_dir)
        _write_text(job_dir / "patch" / "autofix.txt", autofix.notes)
        update_job_status(status_path, artifacts={"autofix_notes": str(job_dir / 'patch' / 'autofix.txt')})
        log.info("job_id=%s step=autofix changed=%s notes=%s done_s=%.2f", job_id, autofix.changed, autofix.notes, time.monotonic() - t0)

        # ── 4) Run tests BEFORE fix ──────────────────────────────────
        if not s.docker_enabled:
            raise RuntimeError("Docker sandbox is disabled (HEALPIPE_DOCKER_ENABLED=false).")

        update_job_status(status_path, step={"name": "test_before_fix"})
        t0 = time.monotonic()
        log.info("job_id=%s step=test_before_fix docker_image=%s", job_id, s.docker_image)
        before = _run_tests_in_sandbox(repo_dir, settings=s, reuse_venv=False)
        _write_text(job_dir / "tests" / "before.json", json.dumps(before, indent=2, ensure_ascii=False))
        update_job_status(status_path, artifacts={"test_before": str(job_dir / 'tests' / 'before.json')})
        log.info(
            "job_id=%s step=test_before_fix exit_code=%s elapsed=%.1fs done_s=%.2f",
            job_id, before.get("exit_code"), before.get("elapsed_seconds", 0), time.monotonic() - t0,
        )

        if before["exit_code"] == 0:
            update_job_status(status_path, state="success", step={"name": "already_passing"})
            log.info("job end job_id=%s result=already_passing total_s=%.2f", job_id, time.monotonic() - job_started)
            return

        failure_summary = (
            "GitHub Actions extracted errors:\n" + json.dumps(errors, indent=2, ensure_ascii=False) + "\n\n" +
            "Sandbox test output (stdout tail):\n" + _tail(before.get("stdout", ""), 6000) + "\n\n" +
            "Sandbox test output (stderr tail):\n" + _tail(before.get("stderr", ""), 6000) + "\n"
        )

        ctx = _collect_relevant_file_context(
            repo_dir,
            output_text=(before.get("stdout", "") + "\n" + before.get("stderr", "")),
        )
        if ctx:
            failure_summary += "\nRelevant repo files:\n" + ctx + "\n"

        _write_text(job_dir / "logs" / "failure_summary.txt", failure_summary)
        log.info("job_id=%s failure_summary_size=%d chars", job_id, len(failure_summary))
        update_job_status(status_path, artifacts={"failure_summary": str(job_dir / 'logs' / 'failure_summary.txt')})

        # ── 5) LLM patch generation ──────────────────────────────────
        update_job_status(status_path, step={"name": "llm_generate_patch"})
        t0 = time.monotonic()
        log.info("job_id=%s step=llm_generate_patch model=%s", job_id, s.llm_model)
        patch_result = generate_patch(
            repo_dir=repo_dir,
            failure_summary=failure_summary,
            avoid_files=["requirements.txt"],
            settings=s,
        )

        _write_text(job_dir / "patch" / "attempt1.raw.txt", patch_result.raw or "")
        log.info("job_id=%s edits_count=%d raw_size=%d bytes", job_id, len(patch_result.edits), len(patch_result.raw or ""))
        update_job_status(
            status_path,
            artifacts={
                "patch_raw_attempt1": str(job_dir / 'patch' / 'attempt1.raw.txt'),
                "patch_notes": patch_result.notes,
            },
        )
        log.info("job_id=%s step=llm_generate_patch ok=%s done_s=%.2f", job_id, patch_result.ok, time.monotonic() - t0)

        if not patch_result.ok or not patch_result.edits:
            update_job_status(status_path, state="failed", error=f"No patch generated: {patch_result.notes}")
            log.warning("job end job_id=%s result=no_patch notes=%s total_s=%.2f", job_id, patch_result.notes, time.monotonic() - job_started)
            return

        # ── 5b) Apply edits (SEARCH/REPLACE blocks) ──────────────────
        update_job_status(status_path, step={"name": "apply_patch"})
        t0 = time.monotonic()
        log.info("job_id=%s step=apply_patch edits=%d", job_id, len(patch_result.edits))
        applied, apply_msg = apply_edits(repo_dir, patch_result.edits)
        _write_text(job_dir / "patch" / "apply.txt", apply_msg)
        update_job_status(status_path, artifacts={"patch_apply_output": str(job_dir / 'patch' / 'apply.txt')})
        log.info("job_id=%s step=apply_patch applied=%s done_s=%.2f", job_id, applied, time.monotonic() - t0)

        if not applied:
            update_job_status(status_path, state="failed", error=f"Edits could not be applied: {apply_msg.strip()[:500]}")
            snippet = (apply_msg or "").strip().splitlines()[:8]
            log.warning(
                "job end job_id=%s result=apply_failed reason=%s total_s=%.2f",
                job_id, " | ".join(snippet)[:500], time.monotonic() - job_started,
            )
            return

        # ── 5c) Generate fix summary ─────────────────────────────────
        log.info("job_id=%s step=generate_fix_summary", job_id)
        try:
            fix_summary = generate_fix_summary(patch_result.edits, failure_summary, settings=s)
            _write_text(job_dir / "patch" / "fix_summary.txt", fix_summary)
            update_job_status(status_path, artifacts={"fix_summary": fix_summary})
            log.info("job_id=%s fix_summary=%s", job_id, fix_summary[:200])
        except Exception as e:
            log.warning("job_id=%s fix summary failed: %s", job_id, e)
            update_job_status(status_path, artifacts={"fix_summary": apply_msg})

        # ── 6) Re-test AFTER fix (reuses venv from step 4) ──────────
        update_job_status(status_path, step={"name": "test_after_fix"})
        t0 = time.monotonic()
        log.info("job_id=%s step=test_after_fix (reusing venv)", job_id)
        after = _run_tests_in_sandbox(repo_dir, settings=s, reuse_venv=True)
        _write_text(job_dir / "tests" / "after.json", json.dumps(after, indent=2, ensure_ascii=False))
        update_job_status(status_path, artifacts={"test_after": str(job_dir / 'tests' / 'after.json')})
        log.info(
            "job_id=%s step=test_after_fix exit_code=%s elapsed=%.1fs done_s=%.2f",
            job_id, after.get("exit_code"), after.get("elapsed_seconds", 0), time.monotonic() - t0,
        )

        if after["exit_code"] == 0:
            update_job_status(status_path, state="success", step={"name": "fixed"})
            # Create a PR with the successful fix.
            try:
                if s.create_pr and s.github_token:
                    update_job_status(status_path, step={"name": "create_pr"})
                    log.info("job_id=%s step=create_pr (tests passing)", job_id)
                    pr_res = create_pr(repo_dir=repo_dir, job_id=job_id, owner=owner, repo=repo, github_token=s.github_token, draft=False)
                    if pr_res.get("ok"):
                        update_job_status(status_path, artifacts={"pr_url": pr_res.get("pr_url")})
                        log.info("job_id=%s pr created url=%s", job_id, pr_res.get("pr_url"))
                        # Send email notification
                        try:
                            from routes.notifications import send_notification_email
                            send_notification_email(
                                repo=repo,
                                pr_url=pr_res.get("pr_url", ""),
                                fix_summary=fix_summary if 'fix_summary' in dir() else "Fix applied.",
                                job_id=job_id,
                            )
                        except Exception as ne:
                            log.warning("job_id=%s email notification failed: %s", job_id, ne)
                    else:
                        update_job_status(status_path, artifacts={"pr_error": pr_res.get("error")})
                        log.warning("job_id=%s pr creation failed: %s", job_id, pr_res.get("error"))
                else:
                    log.info("job_id=%s skipping PR creation (create_pr=%s token_set=%s)", job_id, s.create_pr, bool(s.github_token))
            except Exception as e:
                log.exception("job_id=%s create_pr exception: %s", job_id, e)
            log.info("job end job_id=%s result=fixed total_s=%.2f", job_id, time.monotonic() - job_started)
        else:
            update_job_status(status_path, state="failed", error="Tests still failing after patch.")
            # Still create a draft PR so the fix attempt is visible on GitHub for review.
            try:
                if s.create_pr_on_failure and s.github_token:
                    update_job_status(status_path, step={"name": "create_draft_pr"})
                    log.info("job_id=%s step=create_draft_pr (tests still failing)", job_id)
                    pr_res = create_pr(repo_dir=repo_dir, job_id=job_id, owner=owner, repo=repo, github_token=s.github_token, draft=True)
                    if pr_res.get("ok"):
                        update_job_status(status_path, artifacts={"pr_url": pr_res.get("pr_url")})
                        log.info("job_id=%s draft pr created url=%s", job_id, pr_res.get("pr_url"))
                        # Send email notification
                        try:
                            from routes.notifications import send_notification_email
                            send_notification_email(
                                repo=repo,
                                pr_url=pr_res.get("pr_url", ""),
                                fix_summary=fix_summary if 'fix_summary' in dir() else "Draft fix pushed for review.",
                                job_id=job_id,
                            )
                        except Exception as ne:
                            log.warning("job_id=%s email notification failed: %s", job_id, ne)
                    else:
                        update_job_status(status_path, artifacts={"pr_error": pr_res.get("error")})
                        log.warning("job_id=%s draft pr creation failed: %s", job_id, pr_res.get("error"))
                else:
                    log.info("job_id=%s skipping draft PR (create_pr_on_failure=%s token_set=%s)", job_id, s.create_pr_on_failure, bool(s.github_token))
            except Exception as e:
                log.exception("job_id=%s create_draft_pr exception: %s", job_id, e)
            log.warning("job end job_id=%s result=still_failing total_s=%.2f", job_id, time.monotonic() - job_started)

    except Exception as e:
        update_job_status(status_path, state="failed", error=str(e))
        log.exception("job failed job_id=%s error=%s", job_id, e)

    finally:
        # Clean up sandbox venv/cache from the repo directory
        _cleanup_sandbox_artifacts(repo_dir)
        log.info("job_id=%s cleanup done total_s=%.2f", job_id, time.monotonic() - job_started)
