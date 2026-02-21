"""Silver Cloud Agent – fully upgraded for Hackathon 0 Silver Tier.

Pipeline per task:
  Needs_Action/<task>.md
    -> Plans/<task>_Plan.md          (reasoning plan via planning_skill)
    -> Pending_Approval/<task>.md    (AI summary via summarize_skill, awaiting approval)
    -> Pending_Approval/linkedin_draft_<task>.md  (if business task, via linkedin_skill)

Skill routing:
  skills/planning_skill.py  – structured plan generation
  skills/summarize_skill.py – task summarisation
  skills/linkedin_skill.py  – LinkedIn post draft creation

All events logged to:
  run_log.md            (human-readable, UTC)
  prompt_history.md     (full prompt audit trail: timestamp, model, status, file, snippet)
  Logs/events_<date>.jsonl  (structured JSONL)
  Logs/summary_<ts>.md      (end-of-run stats)

Safe: never crashes if OPENAI_API_KEY is missing — deterministic fallback used.

Optional strict mode (local / advanced use only):
  Set OPENAI_REQUIRED=true to raise an error if OPENAI_API_KEY is missing.
  Default is false — existing fallback behaviour is unchanged.
  NOT set in the GitHub Actions workflow.
"""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# -------- MCP Tools --------
from mcp_file_ops import (
    list_tasks,
    move_task,
    append_file,
    write_file,
    log_event,
)

# -------- Skills (skill-routing pattern) --------
from skills.planning_skill import generate_plan, PROMPT_TEMPLATE as PLAN_PROMPT_TEMPLATE
from skills.summarize_skill import generate_summary, PROMPT_TEMPLATE as SUMMARY_PROMPT_TEMPLATE
from skills.linkedin_skill import generate_linkedin_post, is_business_task, PROMPT_TEMPLATE as LINKEDIN_PROMPT_TEMPLATE

# -------- Paths --------
BASE_DIR = Path(__file__).resolve().parent
NEEDS_ACTION = BASE_DIR / "Needs_Action"
PENDING_APPROVAL = BASE_DIR / "Pending_Approval"
DONE = BASE_DIR / "Done"
PLANS = BASE_DIR / "Plans"
LOGS_DIR = BASE_DIR / "Logs"
RUN_LOG = BASE_DIR / "run_log.md"
PROMPT_HISTORY = BASE_DIR / "prompt_history.md"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_CHARS = int(os.getenv("MAX_TASK_CHARS", "6000"))

# Optional strict mode — disabled by default, never enabled in workflow
OPENAI_REQUIRED = os.getenv("OPENAI_REQUIRED", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _append_log(text: str) -> None:
    append_file(RUN_LOG, text)


def _log_ev(event_type: str, data: dict) -> None:
    log_event(LOGS_DIR, event_type, data)


def _task_hash(task_text: str) -> str:
    """Create a short stable hash for idempotency."""
    return hashlib.sha1(task_text.encode("utf-8")).hexdigest()[:12]


def _log_prompt_history(
    *,
    record_type: str,
    filename: str,
    plan_fname: str,
    model: str,
    status: str,
    prompt_snippet: str,
) -> None:
    """Append a well-structured entry to prompt_history.md.

    Records: UTC timestamp, model, status, task filename, prompt snippet.
    Never logs secrets — only prompt text (which contains no credentials).
    """
    entry = (
        f"---\n"
        f"[{utc_ts()}] {record_type}: {plan_fname}\n"
        f"TASK FILE: {filename}\n"
        f"MODEL: {model}\n"
        f"STATUS: {status}\n"
        f"PROMPT_SNIPPET:\n{prompt_snippet}\n"
        f"---\n\n"
    )
    append_file(PROMPT_HISTORY, entry)


# ---------------------------------------------------------------------------
# OPENAI_REQUIRED strict-mode check
# ---------------------------------------------------------------------------

def _check_openai_required() -> None:
    """If OPENAI_REQUIRED=true and key is missing, log clearly and raise RuntimeError."""
    if not OPENAI_REQUIRED:
        return
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        msg = (
            "OPENAI_REQUIRED=true but OPENAI_API_KEY is not set. "
            "Set the key or set OPENAI_REQUIRED=false to use fallback mode."
        )
        _append_log(f"{utc_ts()} - Agent: ERROR | {msg}\n")
        _log_ev("agent_openai_required_missing", {"reason": msg})
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Silver Agent Running ===")

    # Ensure directories exist
    for d in [NEEDS_ACTION, PENDING_APPROVAL, DONE, PLANS, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Ensure log files exist
    if not RUN_LOG.exists():
        RUN_LOG.write_text("# Run Log\n\n", encoding="utf-8")
    if not PROMPT_HISTORY.exists():
        PROMPT_HISTORY.write_text("# Prompt History\n\n", encoding="utf-8")

    _append_log(f"{utc_ts()} - Agent: started | model={MODEL} | openai_required={OPENAI_REQUIRED}\n")
    _log_ev("agent_started", {"model": MODEL, "openai_required": OPENAI_REQUIRED})

    # ---- Strict mode check (optional, disabled by default) ---------------
    try:
        _check_openai_required()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Stats counters
    stats = {
        "tasks_processed": 0,
        "plans_created": 0,
        "linkedin_drafts_created": 0,
        "fallback_count": 0,
        "openai_ok_count": 0,
        "errors": 0,
    }

    file_names = list_tasks(NEEDS_ACTION)

    if not file_names:
        print("No tasks found in Needs_Action/.")
        _append_log(f"{utc_ts()} - Agent: no_tasks_found\n")
        _log_ev("agent_no_tasks", {})
    else:
        for name in file_names:
            file_path = NEEDS_ACTION / name
            print(f"\n--- Processing: {name} ---")

            try:
                original = file_path.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception as exc:
                print(f"Error reading {name}: {exc}")
                stats["errors"] += 1
                continue

            task_stem = Path(name).stem  # filename without .md
            task_hash = _task_hash(original)

            # ---- Skill 1: Planning ----------------------------------------
            plan_content, plan_status = generate_plan(original, task_stem)
            plan_fname = f"{task_stem}_Plan.md"
            write_file(PLANS / plan_fname, plan_content)
            stats["plans_created"] += 1

            if "fallback" in plan_status:
                stats["fallback_count"] += 1

            _append_log(f"{utc_ts()} - Agent: plan_created | {plan_fname} | {plan_status}\n")
            _log_ev("plan_created", {"file": plan_fname, "status": plan_status, "task": name})

            # Prompt history: plan entry
            prompt_snippet = (
                "fallback (no API key)"
                if "fallback" in plan_status
                else PLAN_PROMPT_TEMPLATE.format(task_text=original[:300])
            )
            _log_prompt_history(
                record_type="PLAN FILE",
                filename=name,
                plan_fname=plan_fname,
                model=MODEL,
                status=plan_status,
                prompt_snippet=prompt_snippet,
            )

            # ---- Skill 2: Summarize ----------------------------------------
            summary, sum_status = generate_summary(original)

            if sum_status == "openai_ok":
                stats["openai_ok_count"] += 1
            else:
                stats["fallback_count"] += 1

            # ---- Write Pending_Approval output -----------------------------
            output_md = (
                f"# Processed Task: {task_stem}\n\n"
                f"**Processed:** {utc_ts()}\n"
                f"**Model:** {MODEL}\n"
                f"**Status:** {sum_status}\n"
                f"**Task Hash:** {task_hash}\n"
                f"**Plan:** Plans/{plan_fname}\n\n"
                "---\n\n"
                "## Original Content\n\n"
                f"{original}\n\n"
                "---\n\n"
                "## AI Summary\n\n"
                f"{summary}\n\n"
                "---\n\n"
                "**Awaiting human approval via approve.py**\n"
            )
            write_file(PENDING_APPROVAL / name, output_md)

            # Prompt history: summary entry
            summary_snippet = (
                "fallback (no API key)"
                if sum_status == "fallback"
                else SUMMARY_PROMPT_TEMPLATE.format(task_text=original[:300])
            )
            _log_prompt_history(
                record_type="SUMMARY",
                filename=name,
                plan_fname=name,
                model=MODEL,
                status=sum_status,
                prompt_snippet=summary_snippet,
            )

            # ---- Skill 3: LinkedIn (if business task) ----------------------
            if is_business_task(original):
                li_text, li_status = generate_linkedin_post(original)

                li_draft_fname = f"linkedin_draft_{task_stem}_{task_hash}.md"
                li_draft_path = PENDING_APPROVAL / li_draft_fname

                li_draft_md = (
                    f"# LinkedIn Post Approval\n\n"
                    f"**Title:** LinkedIn Post Approval\n"
                    f"**Source Task:** {name}\n"
                    f"**Generated:** {utc_ts()}\n"
                    f"**Status:** Pending Approval\n"
                    f"**Task Hash:** {task_hash}\n"
                    f"**Risk Note:** Requires human approval before posting to LinkedIn.\n\n"
                    "---\n\n"
                    "## Generated Post Text\n\n"
                    f"{li_text}\n\n"
                    "---\n\n"
                    "*To approve: run `python approve.py` and select this file.*\n"
                    "*To post: run `python post_approved.py` after approval.*\n"
                )
                write_file(li_draft_path, li_draft_md)
                stats["linkedin_drafts_created"] += 1

                _append_log(
                    f"{utc_ts()} - Agent: linkedin_draft_created | {li_draft_fname} | {li_status}\n"
                )
                _log_ev(
                    "linkedin_draft_created",
                    {"file": li_draft_fname, "source": name, "status": li_status},
                )

                # Prompt history: linkedin entry
                li_snippet = (
                    "fallback (no API key)"
                    if "fallback" in li_status
                    else LINKEDIN_PROMPT_TEMPLATE.format(task_text=original[:300])
                )
                _log_prompt_history(
                    record_type="LINKEDIN DRAFT",
                    filename=name,
                    plan_fname=li_draft_fname,
                    model=MODEL,
                    status=li_status,
                    prompt_snippet=li_snippet,
                )
                print(f"  LinkedIn draft: {li_draft_fname}")

            # ---- Move processed task out of Needs_Action ------------------
            move_task(file_path, DONE / f"_source_{name}")
            stats["tasks_processed"] += 1

            _append_log(f"{utc_ts()} - Agent: processed | {name} | {sum_status}\n")
            _log_ev("task_processed", {"file": name, "status": sum_status, "hash": task_hash})
            print(f"  Processed: {name} ({sum_status})")

    # ---- Write stats summary ----------------------------------------------
    summary_fname = f"summary_{ts_slug()}.md"
    summary_md = (
        f"# Agent Run Summary\n\n"
        f"**Run time:** {utc_ts()}\n"
        f"**Model:** {MODEL}\n\n"
        "| Metric | Count |\n"
        "|--------|-------|\n"
        f"| Tasks processed | {stats['tasks_processed']} |\n"
        f"| Plans created | {stats['plans_created']} |\n"
        f"| LinkedIn drafts created | {stats['linkedin_drafts_created']} |\n"
        f"| OpenAI OK responses | {stats['openai_ok_count']} |\n"
        f"| Fallback responses | {stats['fallback_count']} |\n"
        f"| Errors | {stats['errors']} |\n\n"
        f"Pending approvals: see Pending_Approval/\n"
    )
    write_file(LOGS_DIR / summary_fname, summary_md)
    _log_ev("agent_summary", stats)
    _append_log(f"{utc_ts()} - Agent: done | {stats}\n")

    print(f"\n=== Silver Agent Done ===")
    print(f"  Tasks processed : {stats['tasks_processed']}")
    print(f"  Plans created   : {stats['plans_created']}")
    print(f"  LinkedIn drafts : {stats['linkedin_drafts_created']}")
    print(f"  Fallbacks used  : {stats['fallback_count']}")
    print(f"  Summary written : Logs/{summary_fname}")


if __name__ == "__main__":
    main()
