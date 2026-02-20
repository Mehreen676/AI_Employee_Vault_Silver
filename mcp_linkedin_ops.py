"""MCP LinkedIn Operations – post content via LinkedIn UGC Post API.

Behaviour:
  - If LINKEDIN_ACCESS_TOKEN + LINKEDIN_PERSON_URN set AND LINKEDIN_SIMULATED != true:
      makes a real UGC Post API call.
  - Otherwise: runs in SIMULATED MODE:
      writes evidence JSON to Logs/linkedin_simulated_<ts>.json
      returns {"ok": false, "reason": "...", "evidence_path": "..."}
  - NEVER crashes regardless of credential state.
  - All attempts logged to run_log.md and Logs/events_<date>.jsonl.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests as _requests
except ImportError:
    _requests = None  # type: ignore

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


def _write_simulated_evidence(reason: str, text: str, token_present: bool, urn_present: bool) -> str:
    """Write simulated evidence JSON and return its path."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path = LOGS_DIR / f"linkedin_simulated_{_ts_slug()}.json"
    evidence = {
        "ts": _utc_ts(),
        "mode": "simulated",
        "reason": reason,
        "post_text": text,
        "token_present": token_present,
        "person_urn_present": urn_present,
    }
    try:
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    except Exception:
        pass
    return str(evidence_path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_post(text: str) -> dict:
    """Post text to LinkedIn.

    Returns:
        {"ok": True, "post_id": "..."}               on real success
        {"ok": False, "reason": "...", "evidence_path": "..."}  on simulated / error
    """
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    person_urn = os.getenv("LINKEDIN_PERSON_URN", "").strip()
    simulated_flag = os.getenv("LINKEDIN_SIMULATED", "true").strip().lower() in ("true", "1", "yes")

    token_present = bool(token)
    urn_present = bool(person_urn)

    # ---- Simulated mode ------------------------------------------------
    if not token or not person_urn or simulated_flag:
        reason = "simulated_mode" if simulated_flag else "not_configured"
        evidence_path = _write_simulated_evidence(reason, text, token_present, urn_present)
        _append_log(
            f"{_utc_ts()} - linkedin_post_attempt | mode=simulated | reason={reason}\n"
        )
        _log_event("linkedin_post_attempt", {"mode": "simulated", "reason": reason})
        return {"ok": False, "reason": reason, "evidence_path": evidence_path}

    # ---- requests not installed ----------------------------------------
    if _requests is None:
        reason = "requests_not_installed"
        _append_log(f"{_utc_ts()} - linkedin_post_error | {reason}\n")
        _log_event("linkedin_post_error", {"reason": reason})
        return {"ok": False, "reason": reason}

    # ---- Live API call -------------------------------------------------
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    _append_log(f"{_utc_ts()} - linkedin_post_attempt | mode=live\n")
    _log_event("linkedin_post_attempt", {"mode": "live"})

    try:
        resp = _requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            post_id = resp.headers.get("x-restli-id", "unknown")
            _append_log(f"{_utc_ts()} - linkedin_post_success | post_id={post_id}\n")
            _log_event("linkedin_post_success", {"post_id": post_id})
            return {"ok": True, "post_id": post_id}
        else:
            body_preview = resp.text[:300]
            _append_log(
                f"{_utc_ts()} - linkedin_post_error | status={resp.status_code} | body={body_preview}\n"
            )
            _log_event(
                "linkedin_post_error",
                {"status": resp.status_code, "body": body_preview},
            )
            return {
                "ok": False,
                "reason": f"api_error_{resp.status_code}",
                "body": body_preview,
            }
    except Exception as exc:
        _append_log(f"{_utc_ts()} - linkedin_post_error | {exc}\n")
        _log_event("linkedin_post_error", {"reason": str(exc)})
        return {"ok": False, "reason": str(exc)}
