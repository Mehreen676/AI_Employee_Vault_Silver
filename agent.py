from __future__ import annotations

import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Optional OpenAI (cloud me use hoga)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
NEEDS_ACTION = BASE_DIR / "Needs_Action"
DONE = BASE_DIR / "Done"
LOG_FILE = BASE_DIR / "run_log.md"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change if you want
MAX_CHARS = int(os.getenv("MAX_TASK_CHARS", "6000"))  # safety

print("=== Silver Cloud Agent Running ===")

NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
DONE.mkdir(parents=True, exist_ok=True)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def write_log(line: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(line + "\n")


def openai_summarize(task_text: str) -> str:
    """
    Returns summary from OpenAI if OPENAI_API_KEY available + SDK installed.
    Otherwise returns fallback summary.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return "Cloud Silver Agent processed this task successfully. (fallback: OpenAI not configured)"

    client = OpenAI()  # reads OPENAI_API_KEY from env automatically

    prompt = f"""
You are an AI employee. Summarize the task clearly in 3-6 bullet points.
Then write a short "Next actions" section (1-3 bullets).
Keep it concise. Do NOT invent details.

TASK:
{task_text[:MAX_CHARS]}
""".strip()

    resp = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    # output_text is the simplest way to get final text
    summary_text = getattr(resp, "output_text", "").strip()
    return summary_text or "Summary generated but empty response received."


files = list(NEEDS_ACTION.glob("*.md"))

if not files:
    print("No tasks found.")
else:
    for file_path in files:
        original = file_path.read_text(encoding="utf-8", errors="ignore").strip()

        ai_summary = openai_summarize(original)

        out = f"""# Processed Task

## Original Content
{original}

## AI Summary
{ai_summary}

Status: Completed
"""

        file_path.write_text(out, encoding="utf-8")

        # Move to Done
        shutil.move(str(file_path), str(DONE / file_path.name))

        write_log(f"{utc_ts()} - Processed: {file_path.name}")
        print(f"Processed: {file_path.name}")

print("=== Done ===")
