"""Post Approved LinkedIn Drafts.

Scans Approved/ for linkedin_draft_*.md files, posts them via
mcp_linkedin_ops.create_post(), then moves processed files to Done/.

HITL Hard Block:
  - Before processing, scans Pending_Approval/ for any linkedin_draft_* files.
  - Each unapproved draft is logged as "blocked_without_approval" — clear evidence
    that the system enforces human approval before any LinkedIn action.
  - ONLY files physically inside Approved/ are ever posted.
  - Files in Pending_Approval/ are NEVER touched or posted by this script.

Idempotency:
  - Tracks posted task hashes in Logs/posted_ids.json.
  - Skips files whose hash was already posted to avoid double-posting.

Behaviour:
  - NEVER auto-approves — only processes files already in Approved/.
  - If LinkedIn not configured / LINKEDIN_SIMULATED=true:
      keeps file in Approved/ (NOT moved to Done)
      logs "linkedin_not_configured" or "linkedin_simulated"
      writes evidence JSON to Logs/
  - If posting succeeds:
      moves file to Done/
      records hash in Logs/posted_ids.json

Usage:
  python post_approved.py

Logs all events to run_log.md (UTC) and Logs/events_<date>.jsonl.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from mcp_file_ops import list_files, move_file, append_file, log_event
from mcp_linkedin_ops import create_post

BASE_DIR = Path(__file__).resolve().parent
PENDING_APPROVAL = BASE_DIR / "Pending_Approval"
APPROVED = BASE_DIR / "Approved"
DONE = BASE_DIR / "Done"
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"
POSTED_IDS_FILE = LOGS_DIR / "posted_ids.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def _append_log(text: str) -> None:
    append_file(RUN_LOG, text)


def _log_ev(event_type: str, data: dict) -> None:
    log_event(LOGS_DIR, event_type, data)


def _load_posted_ids() -> set:
    """Load the set of already-posted task hashes."""
    try:
        if POSTED_IDS_FILE.exists():
            data = json.loads(POSTED_IDS_FILE.read_text(encoding="utf-8"))
            return set(data.get("posted_hashes", []))
    except Exception:
        pass
    return set()


def _save_posted_ids(hashes: set) -> None:
    """Persist the set of posted task hashes."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        POSTED_IDS_FILE.write_text(
            json.dumps({"posted_hashes": sorted(hashes)}, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _extract_hash_from_file(content: str) -> str:
    """Extract task hash from a linkedin_draft file."""
    match = re.search(r"\*\*Task Hash:\*\*\s*([a-f0-9]{12})", content)
    if match:
        return match.group(1)
    return ""


def _extract_post_text(content: str) -> str:
    """Extract the generated post text from a linkedin_draft file."""
    marker = "## Generated Post Text"
    idx = content.find(marker)
    if idx == -1:
        return content.strip()
    after = content[idx + len(marker):].strip()
    # Cut at the next --- separator
    sep_idx = after.find("\n---")
    if sep_idx != -1:
        after = after[:sep_idx].strip()
    # Remove trailing instruction lines
    lines = [l for l in after.splitlines() if not l.startswith("*To ")]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# HITL Hard Block — scan Pending_Approval and log unapproved drafts
# ---------------------------------------------------------------------------

def _check_and_log_pending_blocks() -> int:
    """Scan Pending_Approval/ for unapproved linkedin_draft_* files.

    Each one is logged as 'blocked_without_approval' — hard evidence of HITL
    enforcement. Returns the count of blocked files found.
    """
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    pending_li = list_files(PENDING_APPROVAL, "linkedin_draft_*.md")
    if not pending_li:
        return 0

    for fname in pending_li:
        msg = (
            f"HITL_BLOCK: '{fname}' is in Pending_Approval/ and has NOT been approved. "
            "Move to Approved/ via `python approve.py` before this script can post it."
        )
        print(f"  [BLOCKED] {fname} — requires human approval first.")
        _append_log(f"{utc_ts()} - PostApproved: blocked_without_approval | {fname}\n")
        _log_ev(
            "blocked_without_approval",
            {"file": fname, "location": "Pending_Approval/", "action_required": "approve.py"},
        )

    print(
        f"\n  {len(pending_li)} draft(s) are waiting for approval in Pending_Approval/.\n"
        "  Run: python approve.py --all   (or approve individually)\n"
        "  Then re-run post_approved.py to post them.\n"
    )
    return len(pending_li)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Post Approved Running ===")

    APPROVED.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    _append_log(f"{utc_ts()} - PostApproved: started\n")
    _log_ev("post_approved_started", {})

    # ---- HITL Hard Block check -----------------------------------------
    print("\n[HITL CHECK] Scanning Pending_Approval/ for unapproved drafts...")
    blocked_count = _check_and_log_pending_blocks()
    if blocked_count == 0:
        print("  No unapproved drafts found in Pending_Approval/. Good.")
        _append_log(f"{utc_ts()} - PostApproved: hitl_check_clear | no_pending_drafts\n")
    _log_ev("hitl_check_done", {"blocked_count": blocked_count})

    # ---- Only process files inside Approved/ ----------------------------
    print("\n[APPROVED] Scanning Approved/ for approved LinkedIn drafts...")
    li_files = list_files(APPROVED, "linkedin_draft_*.md")

    if not li_files:
        print("No approved LinkedIn drafts found in Approved/.")
        _append_log(f"{utc_ts()} - PostApproved: no_approved_linkedin_files\n")
        _log_ev("post_approved_no_files", {})
        print("=== Post Approved Done ===")
        return

    posted_hashes = _load_posted_ids()

    stats = {
        "found": len(li_files),
        "posted": 0,
        "skipped_duplicate": 0,
        "skipped_not_configured": 0,
        "errors": 0,
    }

    for fname in li_files:
        fpath = APPROVED / fname
        print(f"\n--- Attempting: {fname} ---")

        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            print(f"  Error reading {fname}: {exc}")
            stats["errors"] += 1
            continue

        # ---- Idempotency check -----------------------------------------
        task_hash = _extract_hash_from_file(content)
        if task_hash and task_hash in posted_hashes:
            print(f"  Skipping (already posted): hash={task_hash}")
            _append_log(
                f"{utc_ts()} - PostApproved: skipped_duplicate | {fname} | hash={task_hash}\n"
            )
            _log_ev("linkedin_post_duplicate_skip", {"file": fname, "hash": task_hash})
            stats["skipped_duplicate"] += 1
            continue

        # ---- Extract post text -----------------------------------------
        post_text = _extract_post_text(content)
        if not post_text:
            print(f"  Could not extract post text from {fname}. Skipping.")
            stats["errors"] += 1
            continue

        # ---- Attempt to post (Approved/ only — HITL enforced) ----------
        result = create_post(post_text)

        if result.get("ok"):
            # Success — move to Done
            post_id = result.get("post_id", "unknown")
            done_path = DONE / fname
            move_file(fpath, done_path)
            if task_hash:
                posted_hashes.add(task_hash)
                _save_posted_ids(posted_hashes)
            _append_log(
                f"{utc_ts()} - PostApproved: posted | {fname} | post_id={post_id}\n"
            )
            _log_ev(
                "linkedin_posted_and_done",
                {"file": fname, "post_id": post_id, "hash": task_hash},
            )
            print(f"  Posted! post_id={post_id} -> Done/{fname}")
            stats["posted"] += 1

        else:
            reason = result.get("reason", "unknown")
            evidence = result.get("evidence_path", "")

            if reason in ("not_configured", "simulated_mode"):
                # Keep in Approved — log but don't move
                _append_log(
                    f"{utc_ts()} - PostApproved: {reason} | {fname} | kept in Approved/\n"
                )
                _log_ev(
                    "linkedin_not_posted_kept",
                    {"file": fname, "reason": reason, "evidence": evidence},
                )
                print(f"  Not posted ({reason}). File kept in Approved/.")
                if evidence:
                    print(f"  Evidence: {evidence}")
                stats["skipped_not_configured"] += 1
            else:
                # API error — keep in Approved, log error
                _append_log(
                    f"{utc_ts()} - PostApproved: api_error | {fname} | reason={reason}\n"
                )
                _log_ev(
                    "linkedin_post_api_error",
                    {"file": fname, "reason": reason},
                )
                print(f"  API error ({reason}). File kept in Approved/.")
                stats["errors"] += 1

    _save_posted_ids(posted_hashes)
    _append_log(f"{utc_ts()} - PostApproved: done | {stats}\n")
    _log_ev("post_approved_done", stats)

    print(f"\n=== Post Approved Done ===")
    print(f"  HITL blocked  : {blocked_count}")
    print(f"  Found         : {stats['found']}")
    print(f"  Posted        : {stats['posted']}")
    print(f"  Duplicate     : {stats['skipped_duplicate']}")
    print(f"  Not configured: {stats['skipped_not_configured']}")
    print(f"  Errors        : {stats['errors']}")


if __name__ == "__main__":
    main()
