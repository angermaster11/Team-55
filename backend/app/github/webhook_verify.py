from __future__ import annotations

import hmac
import hashlib
from typing import Optional

from fastapi import Request

from utils.logger import get_logger

log = get_logger("healpipe.webhook_verify")


async def verify_github_webhook(request: Request, *, secret: Optional[str]) -> bool:
    if not secret:
        # If no secret configured, treat as "not verified" but allow.
        log.debug("no webhook secret configured, skipping verification")
        return True

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature or not signature.startswith("sha256="):
        log.warning("missing or malformed X-Hub-Signature-256 header")
        return False

    body = await request.body()
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    valid = hmac.compare_digest(signature, f"sha256={expected}")

    if not valid:
        log.warning("webhook signature mismatch (body_len=%d)", len(body))

    return valid
