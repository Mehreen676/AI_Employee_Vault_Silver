"""Watcher 2 – Manual input ingestion.

Reads manual_input.txt, splits on '---' separator lines,
creates a unique *.md file in Needs_Action/ for each task block,
then clears the file. Logs each ingested task in run_log.md.
Safe: never crashes on missing file or empty content.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
MANUAL_INPUT = BASE_DIR / "manual_input.txt"
NEEDS_ACTION = BASE_DIR / "Needs_Action"
RUN_LOG = BASE_DIR / "run_log.md"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def append_log(text: str) -> None:
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(text)


def main() -> None:
    print("=== Watcher Manual Running ===")

    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

    if not MANUAL_INPUT.exists():
        print("No manual_input.txt found.")
        return

    raw = MANUAL_INPUT.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        print("manual_input.txt is empty.")
        return

    blocks = [b.strip() for b in raw.split("---") if b.strip()]

    if not blocks:
        print("No task blocks found in manual_input.txt.")
        return

    for i, block in enumerate(blocks, start=1):
        fname = f"manual_{ts_slug()}_{i}.md"
        dest = NEEDS_ACTION / fname
        dest.write_text(block + "\n", encoding="utf-8")
        append_log(f"{utc_ts()} - Watcher_Manual: ingested task -> {fname}\n")
        print(f"Ingested: {fname}")

    # Clear the file after ingestion
    MANUAL_INPUT.write_text("", encoding="utf-8")
    print("Cleared manual_input.txt.")

    print("=== Watcher Manual Done ===")


if __name__ == "__main__":
    main()
