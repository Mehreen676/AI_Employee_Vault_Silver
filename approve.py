"""Human-in-the-Loop approval script.

Usage:
  python approve.py                   # list pending files
  python approve.py <filename.md>     # approve a specific file
  python approve.py --all             # approve all pending files

Approved files move: Pending_Approval/ -> Done/
Each approval is logged in run_log.md with UTC timestamp.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

from mcp_server import list_tasks, move_task

BASE_DIR = Path(__file__).resolve().parent
PENDING_APPROVAL = BASE_DIR / "Pending_Approval"
DONE = BASE_DIR / "Done"
RUN_LOG = BASE_DIR / "run_log.md"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def append_log(text: str) -> None:
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(text)


def approve_file(filename: str) -> bool:
    src = PENDING_APPROVAL / filename
    if not src.exists():
        print(f"File not found: {filename}")
        return False

    DONE.mkdir(parents=True, exist_ok=True)
    dst = DONE / filename

    if move_task(src, dst):
        append_log(f"{utc_ts()} - Approved: {filename} -> Done/\n")
        print(f"Approved: {filename} -> Done/")
        return True
    else:
        print(f"Failed to move: {filename}")
        return False


def main() -> None:
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)

    pending = list_tasks(PENDING_APPROVAL)

    if len(sys.argv) < 2:
        # List mode
        if not pending:
            print("No files pending approval.")
        else:
            print("Files pending approval:")
            for f in pending:
                print(f"  - {f}")
            print(f"\nUsage: python approve.py <filename>  OR  python approve.py --all")
        return

    arg = sys.argv[1]

    if arg == "--all":
        if not pending:
            print("No files to approve.")
            return
        for f in pending:
            approve_file(f)
    else:
        approve_file(arg)


if __name__ == "__main__":
    main()
