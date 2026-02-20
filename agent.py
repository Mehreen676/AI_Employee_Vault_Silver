"""Silver Cloud Agent – fully upgraded for Hackathon 0 Silver Tier.

Pipeline per task:
  Needs_Action/<task>.md
    -> Plans/<task>_Plan.md          (reasoning plan)
    -> Pending_Approval/<task>.md    (processed output awaiting human approval)
    -> Pending_Approval/linkedin_draft_<task>.md  (if business/marketing task)

All events logged to:
  run_log.md          (human-readable, UTC)
  prompt_history.md   (full prompt audit trail)
  Logs/events_<date>.jsonl  (structured JSONL)
  Logs/summary_<ts>.md      (end-of-run stats)

Safe: never crashes if OPENAI_API_KEY is missing — deterministic fallback plan used.

Optional strict mode (local / advanced use only):
  Set OPENAI_REQUIRED=true to raise an error if OPENAI_API_KEY is missing.
  Default is false — existing fallback behaviour is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# -------- OpenAI (optional) --------
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# -------- MCP Tools --------
from mcp_file_ops import (
    list_tasks,
    move_task,
    append_file,
    write_file,
    log_event,
)

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

# Keywords that trigger LinkedIn draft creation
BUSINESS_KEYWORDS = {
    "marketing", "linkedin", "campaign", "promote", "post", "brand",
    "social media", "announcement", "launch", "advertisement", "pitch",
    "business", "product", "sales", "lead", "growth", "engagement",
    "content", "strategy", "partnership", "investor", "revenue",
}


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


def is_business_task(text: str) -> bool:
    """Return True if the task text contains business/marketing keywords."""
    lower = text.lower()
    return any(kw in lower for kw in BUSINESS_KEYWORDS)


# ---------------------------------------------------------------------------
# OpenAI helpers
# ---------------------------------------------------------------------------

def _check_openai_required() -> None:
    """If OPENAI_REQUIRED=true and key is missing, log and raise RuntimeError."""
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


def _call_openai(prompt: str) -> tuple[str, str]:
    """Call OpenAI API. Returns (response_text, status)."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return ("", "no_api_key")
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
        )
        text = resp.choices[0].message.content.strip()
        if not text:
            return ("", "openai_empty")
        return (text, "openai_ok")
    except Exception as exc:
        return (f"(OpenAI error: {exc})", "openai_error")


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------

PLAN_PROMPT_TEMPLATE = """\
You are a senior AI business analyst. Given the task below, produce a structured Plan.

Output EXACTLY this format:

## 1. Task Analysis
<1-3 sentence analysis of what is being asked>

## 2. Step-by-Step Plan
1. <step>
2. <step>
3. <step>

## 3. Risks & Edge Cases
- <risk or edge case>
- <risk or edge case>

## 4. Output Checklist
- [ ] <deliverable>
- [ ] <deliverable>

Keep it concise and actionable. Do NOT invent facts.

TASK:
{task_text}
"""


def generate_plan(task_text: str, task_name: str) -> tuple[str, str]:
    """Generate a Plan.md for the task. Returns (plan_content, status)."""
    prompt = PLAN_PROMPT_TEMPLATE.format(task_text=task_text[:MAX_CHARS])
    response, status = _call_openai(prompt)

    if status == "openai_ok" and response:
        plan_body = response
    else:
        # Deterministic fallback plan
        plan_body = (
            "## 1. Task Analysis\n"
            f"Task '{task_name}' has been received and queued for processing. "
            "AI plan generation is unavailable (OpenAI not configured); "
            "a deterministic fallback plan is provided.\n\n"
            "## 2. Step-by-Step Plan\n"
            "1. Review the task content in Needs_Action.\n"
            "2. Identify the required output or deliverable.\n"
            "3. Execute or delegate the task to the appropriate team member.\n"
            "4. Log completion and move to Done.\n\n"
            "## 3. Risks & Edge Cases\n"
            "- Missing context or incomplete task description.\n"
            "- Dependency on external data not yet available.\n\n"
            "## 4. Output Checklist\n"
            "- [ ] Task reviewed by human approver.\n"
            "- [ ] Action taken and documented.\n"
            "- [ ] Moved to Done after approval.\n"
        )
        status = "plan_fallback"

    plan_md = (
        f"# Plan: {task_name}\n\n"
        f"Generated: {utc_ts()}\n"
        f"Model: {MODEL}\n"
        f"Status: {status}\n\n"
        "---\n\n"
        f"{plan_body}\n"
    )
    return plan_md, status


# ---------------------------------------------------------------------------
# Summary / AI summary generation
# ---------------------------------------------------------------------------

SUMMARY_PROMPT_TEMPLATE = """\
You are an AI employee. Summarize the task clearly in 3-6 bullet points.
Then write a short 'Next actions' section (1-3 bullets).
Keep it concise. Do NOT invent details.

TASK:
{task_text}
"""


def generate_summary(task_text: str) -> tuple[str, str]:
    """Generate an AI summary of the task. Returns (summary_text, status)."""
    prompt = SUMMARY_PROMPT_TEMPLATE.format(task_text=task_text[:MAX_CHARS])
    response, status = _call_openai(prompt)
    if status == "openai_ok" and response:
        return response, status
    fallback = (
        "Silver Agent processed this task (fallback: OpenAI not configured).\n\n"
        "**Summary:**\n"
        "- Task received and logged.\n"
        "- Pending human review and approval.\n\n"
        "**Next actions:**\n"
        "- Review the original task content.\n"
        "- Approve or reject via approve.py.\n"
    )
    return fallback, "fallback"


# ---------------------------------------------------------------------------
# LinkedIn draft generation
# ---------------------------------------------------------------------------

LINKEDIN_PROMPT_TEMPLATE = """\
You are a professional LinkedIn content writer.
Based on the business task below, write a compelling LinkedIn post (max 200 words).
Use a professional but engaging tone. Include 2-3 relevant hashtags at the end.
Do NOT include any placeholder text like [Company Name] — write generically.

TASK:
{task_text}
"""


def generate_linkedin_post(task_text: str) -> tuple[str, str]:
    """Generate LinkedIn post text. Returns (post_text, status)."""
    prompt = LINKEDIN_PROMPT_TEMPLATE.format(task_text=task_text[:MAX_CHARS])
    response, status = _call_openai(prompt)
    if status == "openai_ok" and response:
        return response, status
    fallback = (
        "Exciting update from our team! We've been working on something remarkable "
        "and can't wait to share more details soon. Stay tuned for the big reveal.\n\n"
        "#Innovation #BusinessGrowth #ComingSoon"
    )
    return fallback, "linkedin_fallback"


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

    _append_log(f"{utc_ts()} - Agent: started\n")
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

            # ---- 1. Generate Plan ----------------------------------------
            plan_content, plan_status = generate_plan(original, task_stem)
            plan_fname = f"{task_stem}_Plan.md"
            plan_path = PLANS / plan_fname
            write_file(plan_path, plan_content)
            stats["plans_created"] += 1

            if "fallback" in plan_status:
                stats["fallback_count"] += 1

            _append_log(f"{utc_ts()} - Agent: plan_created | {plan_fname} | {plan_status}\n")
            _log_ev("plan_created", {"file": plan_fname, "status": plan_status})

            # Log plan to prompt_history
            append_file(
                PROMPT_HISTORY,
                f"---\n[{utc_ts()}] PLAN FILE: {plan_fname}\n"
                f"MODEL: {MODEL}\nSTATUS: {plan_status}\n"
                f"PROMPT:\n{'fallback' if 'fallback' in plan_status else PLAN_PROMPT_TEMPLATE.format(task_text=original[:500])}\n---\n\n",
            )

            # ---- 2. Generate Summary -------------------------------------
            summary, sum_status = generate_summary(original)

            if sum_status == "openai_ok":
                stats["openai_ok_count"] += 1
            else:
                stats["fallback_count"] += 1

            # ---- 3. Write Pending_Approval output -----------------------
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

            pending_path = PENDING_APPROVAL / name
            write_file(pending_path, output_md)

            # Log summary to prompt_history
            append_file(
                PROMPT_HISTORY,
                f"---\n[{utc_ts()}] FILE: {name}\n"
                f"MODEL: {MODEL}\nSTATUS: {sum_status}\n"
                f"PROMPT:\n{'fallback' if sum_status == 'fallback' else SUMMARY_PROMPT_TEMPLATE.format(task_text=original[:500])}\n---\n\n",
            )

            # ---- 4. Detect business task → LinkedIn draft ---------------
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
                print(f"  LinkedIn draft: {li_draft_fname}")

            # ---- 5. Move task out of Needs_Action -----------------------
            move_task(file_path, DONE / f"_source_{name}")
            stats["tasks_processed"] += 1

            _append_log(f"{utc_ts()} - Agent: processed | {name} | {sum_status}\n")
            _log_ev("task_processed", {"file": name, "status": sum_status, "hash": task_hash})
            print(f"  Processed: {name} ({sum_status})")

    # ---- 6. Write stats summary -----------------------------------------
    summary_fname = f"summary_{ts_slug()}.md"
    summary_path = LOGS_DIR / summary_fname
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
    write_file(summary_path, summary_md)
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
