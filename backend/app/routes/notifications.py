from __future__ import annotations

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import get_settings
from utils.logger import get_logger

log = get_logger("healpipe.notifications")

router = APIRouter(tags=["notifications"])

# Simple file-based settings store for notification preferences
_SETTINGS_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "notification_settings.json"


class NotificationSettings(BaseModel):
    email: str = ""
    notify_on_pr: bool = True
    notify_on_failure: bool = True


def _load_notification_settings() -> dict:
    if _SETTINGS_FILE.exists():
        try:
            return json.loads(_SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_notification_settings(settings: dict) -> None:
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


@router.get("/settings/notifications")
async def get_notification_settings():
    """Get current notification settings."""
    return _load_notification_settings()


@router.post("/settings/notifications")
async def save_notification_settings(settings: NotificationSettings):
    """Save notification settings (email, preferences)."""
    data = settings.dict()
    _save_notification_settings(data)
    log.info("notification settings saved email=%s", data.get("email"))
    return {"ok": True, "message": "Settings saved", "settings": data}


def send_notification_email(
    *,
    repo: str,
    pr_url: str,
    fix_summary: str,
    job_id: str,
) -> bool:
    """Send email notification about a completed fix.
    Uses the saved notification settings for the recipient email.
    Falls back to a simple log if SMTP is not configured."""
    settings = _load_notification_settings()
    email = settings.get("email", "")
    
    if not email:
        log.info("no notification email configured, skipping")
        return False

    subject = f"🔧 HealPipe: Fix pushed for {repo}"
    
    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #3b82f6, #10b981); padding: 24px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 20px;">🔧 HealPipe Fix Report</h1>
        </div>
        <div style="background: #f8fafc; padding: 24px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
            <p style="color: #334155; font-size: 16px; margin-top: 0;">
                A bug in <strong>{repo}</strong> was automatically detected and a Pull Request has been created.
            </p>
            
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin: 0 0 8px 0; color: #1e293b; font-size: 14px;">📝 Fix Summary</h3>
                <p style="color: #475569; font-size: 14px; margin: 0; line-height: 1.6;">{fix_summary}</p>
            </div>
            
            <a href="{pr_url}" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">
                View Pull Request →
            </a>
            
            <p style="color: #94a3b8; font-size: 12px; margin-top: 24px;">
                Job ID: {job_id} • Powered by HealPipe
            </p>
        </div>
    </div>
    """

    # Try to send via SMTP (Gmail, etc.)
    s = get_settings()
    smtp_host = getattr(s, 'smtp_host', None) or "smtp.gmail.com"
    smtp_port = getattr(s, 'smtp_port', None) or 587
    smtp_user = getattr(s, 'smtp_user', None) or ""
    smtp_pass = getattr(s, 'smtp_pass', None) or ""

    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            log.info("notification email sent to=%s subject=%s", email, subject)
            return True
        except Exception as e:
            log.warning("SMTP send failed: %s, falling back to log", e)

    # If no SMTP, just log it (the frontend will still show the notification)
    log.info("EMAIL NOTIFICATION (logged, SMTP not configured):\n  To: %s\n  Subject: %s\n  Summary: %s\n  PR: %s", email, subject, fix_summary, pr_url)
    return True
