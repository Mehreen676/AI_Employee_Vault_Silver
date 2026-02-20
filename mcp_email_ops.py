"""MCP Email Operations – send email via SMTP or simulated mode (BONUS).

Behaviour:
  - If SMTP_HOST + SMTP_USER + SMTP_PASS env vars are set: sends real email.
  - Otherwise: SIMULATED MODE — writes evidence JSON to Logs/email_simulated_<ts>.json.
  - NEVER crashes regardless of credential state.
  - All events logged to run_log.md and Logs/events_<date>.jsonl.
"""

from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _append_log(text: str) -> None:
    try:
        RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def _log_event(event_type: str, data: dict) -> None:
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        events_file = LOGS_DIR / f"events_{today}.jsonl"
        entry = {"ts": _utc_ts(), "event": event_type, **data}
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email.

    Returns:
        {"ok": True}                                                  on success
        {"ok": False, "reason": "...", "evidence_path": "..."}        on simulated / error
    """
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port_raw = os.getenv("SMTP_PORT", "587").strip()
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()

    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    # ---- Simulated mode if credentials missing -------------------------
    if not smtp_host or not smtp_user or not smtp_pass:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        evidence_path = LOGS_DIR / f"email_simulated_{_ts_slug()}.json"
        evidence = {
            "ts": _utc_ts(),
            "mode": "simulated",
            "to": to,
            "subject": subject,
            "body": body,
            "reason": "not_configured",
        }
        try:
            evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        except Exception:
            pass
        _append_log(f"{_utc_ts()} - email_send_attempt | simulated | to={to}\n")
        _log_event("email_send_simulated", {"to": to, "subject": subject})
        return {"ok": False, "reason": "not_configured", "evidence_path": str(evidence_path)}

    # ---- Real SMTP send ------------------------------------------------
    _append_log(f"{_utc_ts()} - email_send_attempt | live | to={to}\n")
    _log_event("email_send_attempt", {"to": to, "subject": subject})

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to], msg.as_string())

        _append_log(f"{_utc_ts()} - email_send_success | to={to}\n")
        _log_event("email_send_success", {"to": to, "subject": subject})
        return {"ok": True}

    except Exception as exc:
        _append_log(f"{_utc_ts()} - email_send_error | to={to} | {exc}\n")
        _log_event("email_send_error", {"to": to, "reason": str(exc)})
        return {"ok": False, "reason": str(exc)}
