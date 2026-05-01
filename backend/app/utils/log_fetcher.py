import requests
import zipfile
import io
import os
import time

from config.settings import get_settings
from utils.logger import get_logger


log = get_logger("healpipe.logs")


def get_logs(owner: str, repo: str, run_id: int, *, token: str | None = None, dest_dir: str | None = None) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"

    settings = get_settings()
    github_token = token or settings.github_token
    if not github_token:
        raise RuntimeError("Missing GitHub token. Set HEALPIPE_GITHUB_TOKEN env var.")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }

    log.info("fetching logs url=%s owner=%s repo=%s run_id=%s", url, owner, repo, run_id)
    t0 = time.monotonic()

    try:
        response = requests.get(url, headers=headers, timeout=60)
    except requests.Timeout:
        log.error("log fetch timed out owner=%s repo=%s run_id=%s", owner, repo, run_id)
        return {"ok": False, "error": "Request timed out after 60s"}
    except requests.RequestException as e:
        log.error("log fetch error owner=%s repo=%s run_id=%s error=%s", owner, repo, run_id, e)
        return {"ok": False, "error": str(e)}

    fetch_elapsed = time.monotonic() - t0
    log.info("log fetch done status=%s size=%d bytes elapsed=%.2fs", response.status_code, len(response.content), fetch_elapsed)

    if response.status_code != 200:
        log.warning("failed to fetch logs owner=%s repo=%s run_id=%s status=%s body=%s",
                     owner, repo, run_id, response.status_code, response.text[:500])
        return {"ok": False, "status_code": response.status_code, "error": response.text}

    # Extract ZIP
    try:
        z = zipfile.ZipFile(io.BytesIO(response.content))
    except zipfile.BadZipFile as e:
        log.error("invalid zip in log response owner=%s repo=%s run_id=%s error=%s", owner, repo, run_id, e)
        return {"ok": False, "error": f"Bad ZIP file: {e}"}

    base_dir = dest_dir or str(settings.artifacts_dir / "logs")
    os.makedirs(base_dir, exist_ok=True)

    combined_path = os.path.join(base_dir, "raw_logs.txt")
    combined_text_parts: list[str] = []
    file_count = 0

    with open(combined_path, "w") as outfile:
        for file in z.namelist():
            with z.open(file) as f:
                content = f.read().decode("utf-8", errors="ignore")
                outfile.write(f"\n\n===== {file} =====\n\n")
                outfile.write(content)
                combined_text_parts.append(f"\n\n===== {file} =====\n\n{content}")
                file_count += 1

    combined_text = "".join(combined_text_parts)
    log.info("logs saved owner=%s repo=%s run_id=%s path=%s files=%d total_chars=%d",
             owner, repo, run_id, combined_path, file_count, len(combined_text))
    return {"ok": True, "combined_path": combined_path, "combined_text": combined_text}