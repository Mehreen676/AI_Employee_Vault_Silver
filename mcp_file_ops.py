"""MCP File Operations – safe, crash-free file system helpers.

Used by agent.py, approve.py, post_approved.py instead of raw file calls.
Maintains backward compatibility with mcp_server.py names.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


# ---------------------------------------------------------------------------
# Core ops
# ---------------------------------------------------------------------------

def list_files(folder: str | Path, pattern: str = "*.md") -> list[str]:
    """Return sorted list of filenames in folder matching pattern (excluding .gitkeep)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(f.name for f in folder.glob(pattern) if f.name != ".gitkeep")


def read_file(path: str | Path) -> str:
    """Safely read a file. Returns empty string on any error."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def write_file(path: str | Path, content: str) -> bool:
    """Safely write content to a file. Creates parent dirs if needed."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def append_file(path: str | Path, content: str) -> bool:
    """Append content to a file. Creates parent dirs if needed."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def move_file(src: str | Path, dst: str | Path) -> bool:
    """Move a file from src to dst. Returns True on success."""
    src, dst = Path(src), Path(dst)
    if not src.exists():
        return False
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True
    except Exception:
        return False


def copy_file(src: str | Path, dst: str | Path) -> bool:
    """Copy a file from src to dst. Returns True on success."""
    src, dst = Path(src), Path(dst)
    if not src.exists():
        return False
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Structured event logging (JSONL)
# ---------------------------------------------------------------------------

def log_event(logs_dir: Path, event_type: str, data: dict) -> None:
    """Append a structured JSON event to Logs/events_<date>.jsonl."""
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        events_file = logs_dir / f"events_{today}.jsonl"
        entry = {"ts": utc_ts(), "event": event_type, **data}
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never crash on logging


# ---------------------------------------------------------------------------
# Backward-compat aliases (mcp_server.py interface)
# ---------------------------------------------------------------------------

def list_tasks(folder: str | Path) -> list[str]:
    """Alias: list *.md files (backward compat with mcp_server.py)."""
    return list_files(folder, "*.md")


def move_task(src: str | Path, dst: str | Path) -> bool:
    """Alias: move file (backward compat with mcp_server.py)."""
    return move_file(src, dst)
