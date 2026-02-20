"""Watcher 3 – WhatsApp simulated ingestion.

Reads whatsapp_input.txt, splits tasks on '---' separator lines,
creates Needs_Action/wa_<timestamp>_<n>.md for each block,
then clears the file. Logs each ingested task to run_log.md (UTC).

This is a SIMULATED watcher (no real WhatsApp API). It demonstrates
multi-channel ingestion by reading a local text file as a stand-in for
WhatsApp DMs/messages.

Safe: never crashes on missing file or empty content.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WHATSAPP_INPUT = BASE_DIR / "whatsapp_input.txt"
NEEDS_ACTION = BASE_DIR / "Needs_Action"
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def ts_slug() -> str:
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


def main() -> None:
    print("=== WhatsApp Watcher (Simulated) Running ===")

    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if not WHATSAPP_INPUT.exists():
        print("No whatsapp_input.txt found. Skipping.")
        append_log(f"{utc_ts()} - WhatsApp_Watcher: no_input_file\n")
        log_event("whatsapp_watcher_skip", {"reason": "no_input_file"})
        return

    raw = WHATSAPP_INPUT.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        print("whatsapp_input.txt is empty. Skipping.")
        append_log(f"{utc_ts()} - WhatsApp_Watcher: empty_file\n")
        log_event("whatsapp_watcher_skip", {"reason": "empty_file"})
        return

    blocks = [b.strip() for b in raw.split("---") if b.strip()]

    if not blocks:
        print("No task blocks found in whatsapp_input.txt.")
        return

    ingested = 0
    slug = ts_slug()
    for i, block in enumerate(blocks, start=1):
        fname = f"wa_{slug}_{i}.md"
        dest = NEEDS_ACTION / fname
        try:
            dest.write_text(
                f"# WhatsApp Task (Simulated)\n\nSource: whatsapp_input.txt\n\n{block}\n",
                encoding="utf-8",
            )
            append_log(f"{utc_ts()} - WhatsApp_Watcher: ingested -> {fname}\n")
            log_event("whatsapp_task_ingested", {"file": fname})
            print(f"Ingested: {fname}")
            ingested += 1
        except Exception as exc:
            print(f"Error writing {fname}: {exc}")

    # Clear input file after processing
    try:
        WHATSAPP_INPUT.write_text("", encoding="utf-8")
        print("Cleared whatsapp_input.txt.")
    except Exception:
        pass

    append_log(f"{utc_ts()} - WhatsApp_Watcher: done | ingested={ingested}\n")
    log_event("whatsapp_watcher_done", {"ingested": ingested})
    print(f"=== WhatsApp Watcher Done ({ingested} tasks ingested) ===")


if __name__ == "__main__":
    main()
