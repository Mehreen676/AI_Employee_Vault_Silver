"""MCP Calendar Operations – create/read calendar events (BONUS).

Currently runs in SIMULATED MODE (local JSON store).
Extend with Google Calendar API credentials to enable live mode.
All events logged to run_log.md and Logs/events_<date>.jsonl.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"
CALENDAR_DB = LOGS_DIR / "calendar_events.json"


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


def _load_db() -> list:
    try:
        if CALENDAR_DB.exists():
            return json.loads(CALENDAR_DB.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_db(events: list) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CALENDAR_DB.write_text(json.dumps(events, indent=2), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_event(title: str, start: str, end: str, description: str = "") -> dict:
    """Create a calendar event in the local simulated store.

    Returns:
        {"ok": True, "event": {...}}
    """
    events = _load_db()
    event = {
        "id": _ts_slug(),
        "title": title,
        "start": start,
        "end": end,
        "description": description,
        "created_at": _utc_ts(),
        "mode": "simulated",
    }
    events.append(event)
    _save_db(events)
    _append_log(f"{_utc_ts()} - calendar_event_created | title={title} | start={start}\n")
    _log_event("calendar_event_created", {"title": title, "start": start, "end": end})
    return {"ok": True, "event": event}


def read_events() -> dict:
    """Read all calendar events from the local store.

    Returns:
        {"ok": True, "events": [...], "count": N}
    """
    events = _load_db()
    _log_event("calendar_events_read", {"count": len(events)})
    return {"ok": True, "events": events, "count": len(events)}
