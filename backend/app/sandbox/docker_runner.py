from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import os

from utils.logger import get_logger


log = get_logger("healpipe.docker")


@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    command: list[str]
    elapsed_seconds: float = 0.0


def run_in_docker(
    *,
    image: str,
    repo_dir: Path,
    command: str,
    workdir: str = "/work",
    env: Mapping[str, str] | None = None,
    cpus: float = 2.0,
    memory: str = "2g",
    pids_limit: int = 256,
    timeout_seconds: int = 20 * 60,
    run_as_user: bool = True,
) -> CommandResult:
    repo_dir = repo_dir.resolve()

    if not repo_dir.exists():
        raise FileNotFoundError(str(repo_dir))

    docker_cmd: list[str] = [
        "docker",
        "run",
        "--rm",
        "--cpus",
        str(cpus),
        "--memory",
        memory,
        "--pids-limit",
        str(pids_limit),
        "-v",
        f"{str(repo_dir)}:{workdir}:rw",
        "-w",
        workdir,
    ]

    if run_as_user:
        docker_cmd.extend(["--user", f"{os.getuid()}:{os.getgid()}"])

    if env:
        for k, v in env.items():
            docker_cmd.extend(["-e", f"{k}={v}"])

    docker_cmd.extend([image, "sh", "-lc", command])

    log.info(
        "docker run start image=%s workdir=%s cpus=%.1f memory=%s timeout=%ds cmd_len=%d",
        image, workdir, cpus, memory, timeout_seconds, len(command),
    )
    log.debug("docker full command: %s", " ".join(docker_cmd))

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        log.error("docker run TIMEOUT after %.1fs (limit=%ds)", elapsed, timeout_seconds)
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr=f"Docker container timed out after {timeout_seconds}s",
            command=docker_cmd,
            elapsed_seconds=elapsed,
        )

    elapsed = time.monotonic() - t0
    stdout_lines = (proc.stdout or "").count("\n")
    stderr_lines = (proc.stderr or "").count("\n")

    log.info(
        "docker run done exit_code=%s elapsed=%.1fs stdout_lines=%d stderr_lines=%d",
        proc.returncode, elapsed, stdout_lines, stderr_lines,
    )

    if proc.returncode != 0 and elapsed > 60:
        log.warning(
            "docker run slow failure: exit_code=%s took %.1fs — consider checking pip install or network issues",
            proc.returncode, elapsed,
        )

    return CommandResult(
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        command=docker_cmd,
        elapsed_seconds=elapsed,
    )
