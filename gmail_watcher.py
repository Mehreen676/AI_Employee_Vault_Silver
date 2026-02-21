"""
Gmail Watcher – ingests unread inbox emails into Inbox/ as task files.

CLOUD MODE:
  - Always runs (no GMAIL_OAUTH_ENABLED guard).
  - Exits cleanly if credentials missing.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INBOX = BASE_DIR / "Inbox"
DONE = BASE_DIR / "Done"
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"

ALLOWED_DOMAINS = {
    "google.com",
    "github.com",
    "microsoft.com",
    "azure.com",
    "anthropic.com",
}

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MARK_AS_READ = False


# ---------------------------------------------------------------------------

def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def utc_file_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def append_log(text: str) -> None:
    try:
        RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def log_event(event_type: str, data: dict) -> None:
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        events_file = LOGS_DIR / f"events_{today}.jsonl"
        entry = {"ts": utc_ts(), "event": event_type, **data}
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def extract_domain(email_addr: str) -> str:
    match = re.search(r"@([\w.-]+)", email_addr)
    return match.group(1).lower() if match else ""


def domain_allowed(email_addr: str) -> bool:
    domain = extract_domain(email_addr)
    return any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS)


def get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def file_exists_for_id(msg_id: str) -> bool:
    suffix = f"_{msg_id}.md"
    for folder in [INBOX, DONE]:
        if folder.is_dir():
            if any(f.name.endswith(suffix) for f in folder.glob("*.md")):
                return True
    return False


# ---------------------------------------------------------------------------
# Gmail auth
# ---------------------------------------------------------------------------

def auth_gmail():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Gmail libraries missing.")
        raise SystemExit(1)

    creds = None
    token_path = BASE_DIR / "token.json"
    creds_path = BASE_DIR / "credentials.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print("credentials.json not found.")
                raise SystemExit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Gmail Watcher Running ===")

    INBOX.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    append_log(f"{utc_ts()} - Gmail: starting\n")
    log_event("gmail_watcher_started", {})

    try:
        service = auth_gmail()
    except Exception:
        append_log(f"{utc_ts()} - Gmail: auth_failed\n")
        log_event("gmail_auth_failed", {})
        return

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=10,
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        append_log(f"{utc_ts()} - Gmail: no_unread\n")
        log_event("gmail_no_unread", {})
        return

    ingested = 0

    for msg in messages:
        msg_id = msg["id"]

        detail = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        headers = detail.get("payload", {}).get("headers", [])
        sender = get_header(headers, "From")
        subject = get_header(headers, "Subject")
        date = get_header(headers, "Date")
        snippet = detail.get("snippet", "")

        if not domain_allowed(sender):
            continue

        if file_exists_for_id(msg_id):
            continue

        filename = f"email_{utc_file_ts()}_{msg_id}.md"

        content = (
            "# Email Task\n\n"
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"Date: {date}\n\n"
            "## Snippet\n\n"
            f"{snippet}\n\n"
            "Source: Gmail\n"
            f"Allowed Domain: {extract_domain(sender)}\n"
            "Status: New\n"
        )

        (INBOX / filename).write_text(content, encoding="utf-8")

        append_log(
            f"{utc_ts()} - Gmail: ingested | {filename} | from={sender}\n"
        )
        log_event("gmail_ingested", {"file": filename})
        ingested += 1

    append_log(f"{utc_ts()} - Gmail: done | ingested={ingested}\n")
    log_event("gmail_watcher_done", {"ingested": ingested})

    print(f"=== Gmail Watcher Done ({ingested} ingested) ===")


if __name__ == "__main__":
    main()