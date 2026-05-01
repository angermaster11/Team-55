from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HEALPIPE_",
        extra="ignore",
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
    )

    github_token: Optional[str] = Field(default=None, description="GitHub token for API calls (download Actions logs, PR creation).")
    github_webhook_secret: Optional[str] = Field(default=None, description="GitHub webhook secret for X-Hub-Signature-256 verification.")

    artifacts_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "artifacts",
        description="Base directory where job artifacts are stored.",
    )

    # Docker sandbox
    docker_enabled: bool = True
    docker_image: str = "python:3.11-slim"
    docker_cpus: float = 2.0
    docker_memory: str = "2g"
    docker_pids_limit: int = 256
    docker_timeout_seconds: int = 20 * 60

    # LLM (OpenAI-compatible)
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = 120.0
    llm_connect_timeout_seconds: float = 30.0
    llm_max_retries: int = 3
    # Whether to automatically create a GitHub PR when a patch makes tests pass.
    create_pr: bool = True
    # Whether to create a draft PR even when tests still fail after patch.
    create_pr_on_failure: bool = True

    # Email SMTP configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    return settings
