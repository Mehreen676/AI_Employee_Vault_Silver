"""Send Test Email – CLI script for verifying MCP email integration.

Reads recipient from TO_EMAIL env var (or first CLI arg) and sends a test
message via mcp_email_ops.send_email().

If SMTP credentials are not configured, runs in simulated mode and writes
evidence to Logs/email_simulated_<ts>.json — never crashes.

Usage:
  python send_test_email.py
  python send_test_email.py recipient@example.com

Env vars (set in .env locally or GitHub Secrets):
  TO_EMAIL    Recipient address (required)
  SMTP_HOST   SMTP server hostname
  SMTP_PORT   Port (default 587)
  SMTP_USER   SMTP login username
  SMTP_PASS   SMTP login password
  SMTP_FROM   Sender address (optional; defaults to SMTP_USER)

All events logged to run_log.md and Logs/events_<date>.jsonl (UTC).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp_email_ops import send_email

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


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


def main() -> None:
    print("=== Send Test Email ===")

    # Resolve recipient
    to_email = ""
    if len(sys.argv) > 1:
        to_email = sys.argv[1].strip()
    if not to_email:
        to_email = os.getenv("TO_EMAIL", "").strip()

    if not to_email:
        print("ERROR: No recipient specified.")
        print("Usage: python send_test_email.py recipient@example.com")
        print("   or: set TO_EMAIL env var and run python send_test_email.py")
        _append_log(f"{_utc_ts()} - SendTestEmail: ERROR | no_recipient\n")
        _log_event("send_test_email_error", {"reason": "no_recipient"})
        sys.exit(1)

    subject = "AI Employee Vault — Silver Tier Test Email"
    body = (
        "Hello,\n\n"
        "This is a test email sent by the AI Employee Vault Silver Tier agent.\n\n"
        "It confirms that the MCP Email Operations module (mcp_email_ops.py) "
        "is correctly configured and able to send emails via SMTP.\n\n"
        f"Sent at: {_utc_ts()}\n\n"
        "-- Silver Agent"
    )

    _append_log(f"{_utc_ts()} - SendTestEmail: started | to={to_email}\n")
    _log_event("send_test_email_started", {"to": to_email})

    result = send_email(to=to_email, subject=subject, body=body)

    if result.get("ok"):
        print(f"Email sent successfully to {to_email}.")
        _append_log(f"{_utc_ts()} - SendTestEmail: success | to={to_email}\n")
        _log_event("send_test_email_success", {"to": to_email})
    else:
        reason = result.get("reason", "unknown")
        evidence = result.get("evidence_path", "")

        if reason == "not_configured":
            print(f"Simulated mode: SMTP credentials not configured.")
            print(f"Evidence written to: {evidence}")
            _append_log(
                f"{_utc_ts()} - SendTestEmail: simulated | not_configured | to={to_email} | evidence={evidence}\n"
            )
            _log_event("send_test_email_simulated", {"to": to_email, "evidence": evidence})
        else:
            print(f"Email send failed: {reason}")
            _append_log(f"{_utc_ts()} - SendTestEmail: failed | to={to_email} | reason={reason}\n")
            _log_event("send_test_email_failed", {"to": to_email, "reason": reason})

    print("=== Send Test Email Done ===")


if __name__ == "__main__":
    main()
