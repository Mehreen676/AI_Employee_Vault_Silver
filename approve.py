"""Human-in-the-Loop approval script.

Moves files:  Pending_Approval/ -> Approved/
                                    (NOT directly Done — post_approved.py handles Done)

Usage:
  python approve.py                   # list pending files
  python approve.py <filename.md>     # approve a specific file
  python approve.py --all             # approve all pending files

Each approval is logged in run_log.md (UTC) and Logs/events_<date>.jsonl.
NEVER auto-approves — always requires explicit human invocation.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp_file_ops import list_tasks, move_task, append_file, log_event

BASE_DIR = Path(__file__).resolve().parent
PENDING_APPROVAL = BASE_DIR / "Pending_Approval"
APPROVED = BASE_DIR / "Approved"
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _append_log(text: str) -> None:
    append_file(RUN_LOG, text)


def _log_ev(event_type: str, data: dict) -> None:
    log_event(LOGS_DIR, event_type, data)


def approve_file(filename: str) -> bool:
    """Move one file from Pending_Approval/ to Approved/."""
    src = PENDING_APPROVAL / filename
    if not src.exists():
        print(f"File not found in Pending_Approval: {filename}")
        return False

    APPROVED.mkdir(parents=True, exist_ok=True)
    dst = APPROVED / filename

    if move_task(src, dst):
        _append_log(f"{utc_ts()} - Approved: {filename} -> Approved/\n")
        _log_ev("file_approved", {"file": filename, "dest": "Approved/"})
        print(f"Approved: {filename} -> Approved/")
        return True
    else:
        print(f"Failed to move: {filename}")
        _append_log(f"{utc_ts()} - Approve_FAILED: {filename}\n")
        _log_ev("file_approve_failed", {"file": filename})
        return False


def main() -> None:
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    APPROVED.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    pending = list_tasks(PENDING_APPROVAL)

    if len(sys.argv) < 2:
        # List mode
        if not pending:
            print("No files pending approval.")
        else:
            print(f"Files pending approval ({len(pending)}):")
            for f in pending:
                tag = " [LINKEDIN]" if f.startswith("linkedin_draft_") else ""
                print(f"  - {f}{tag}")
            print(
                "\nUsage:\n"
                "  python approve.py <filename.md>   approve one file\n"
                "  python approve.py --all           approve all files\n"
                "\nApproved files move to Approved/ (NOT Done).\n"
                "Run post_approved.py to post LinkedIn drafts and finalize Done."
            )
        return

    arg = sys.argv[1]

    if arg == "--all":
        if not pending:
            print("No files to approve.")
            return
        approved_count = 0
        for f in pending:
            if approve_file(f):
                approved_count += 1
        print(f"\nApproved {approved_count}/{len(pending)} files -> Approved/")
    else:
        approve_file(arg)


if __name__ == "__main__":
    main()
