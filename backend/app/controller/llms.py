from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from openai import OpenAI

from config.settings import Settings, get_settings
from utils.logger import get_logger

log = get_logger("healpipe.llm")


def get_openai_client(settings: Optional[Settings] = None) -> OpenAI:
    s = settings or get_settings()
    if not s.llm_api_key:
        raise RuntimeError("Missing LLM API key. Set HEALPIPE_LLM_API_KEY env var.")

    kwargs: dict[str, Any] = {"api_key": s.llm_api_key}
    if s.llm_base_url:
        kwargs["base_url"] = s.llm_base_url
    kwargs["timeout"] = httpx.Timeout(
        timeout=s.llm_timeout_seconds,
        connect=s.llm_connect_timeout_seconds,
    )
    kwargs["max_retries"] = s.llm_max_retries

    log.debug("creating OpenAI client base_url=%s timeout=%.0fs retries=%d", s.llm_base_url, s.llm_timeout_seconds, s.llm_max_retries)
    return OpenAI(**kwargs)


def chat_complete(messages: list[dict[str, str]], *, model: str | None = None, settings: Optional[Settings] = None) -> str:
    s = settings or get_settings()
    client = get_openai_client(s)
    use_model = model or s.llm_model

    total_chars = sum(len(m.get("content", "")) for m in messages)
    log.info("chat_complete model=%s messages=%d total_input_chars=%d", use_model, len(messages), total_chars)

    t0 = time.monotonic()
    response = client.chat.completions.create(
        model=use_model,
        messages=messages,
    )
    elapsed = time.monotonic() - t0

    content = response.choices[0].message.content or ""
    log.info("chat_complete done model=%s elapsed=%.1fs response_chars=%d", use_model, elapsed, len(content))
    return content