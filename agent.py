"""Silver Cloud Agent – processes Needs_Action/*.md tasks."""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone

# --------------- Optional OpenAI import ---------------
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

# --------------- Paths ---------------
BASE_DIR = Path(__file__).resolve().parent
NEEDS_ACTION = BASE_DIR / "Needs_Action"
DONE = BASE_DIR / "Done"
RUN_LOG = BASE_DIR / "run_log.md"
PROMPT_HISTORY = BASE_DIR / "prompt_history.md"

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_CHARS = int(os.getenv("MAX_TASK_CHARS", "6000"))


# --------------- Helpers ---------------
def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def append_line(path: Path, text: str) -> None:
    """Append text to a file, creating it if needed."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def build_prompt(task_text: str) -> str:
    return (
        "You are an AI employee. Summarize the task clearly in 3-6 bullet points.\n"
        "Then write a short \"Next actions\" section (1-3 bullets).\n"
        "Keep it concise. Do NOT invent details.\n\n"
        f"TASK:\n{task_text[:MAX_CHARS]}"
    )


def openai_summarize(prompt: str) -> tuple[str, str]:
    """Call OpenAI to summarize. Returns (summary_text, status_note)."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key or OpenAI is None:
        return (
            "Silver Agent processed this task. (fallback: OpenAI not configured)",
            "fallback",
        )

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        summary_text = resp.choices[0].message.content.strip()
        if not summary_text:
            return ("Summary generated but empty response.", "openai_empty")
        return (summary_text, "openai_ok")
    except Exception as e:
        return (f"(OpenAI error fallback) {e}", "openai_error")


# --------------- Main ---------------
def main() -> None:
    print("=== Silver Cloud Agent Running ===")

    # Ensure folders exist
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)

    # Ensure log files exist
    if not RUN_LOG.exists():
        RUN_LOG.write_text("# Run Log\n\n", encoding="utf-8")
    if not PROMPT_HISTORY.exists():
        PROMPT_HISTORY.write_text("# Prompt History\n\n", encoding="utf-8")

    files = sorted(NEEDS_ACTION.glob("*.md"))
    # Skip .gitkeep
    files = [f for f in files if f.name != ".gitkeep"]

    if not files:
        print("No tasks found in Needs_Action/.")
        append_line(RUN_LOG, f"{utc_ts()} - No tasks found.\n")
        print("=== Done ===")
        return

    for file_path in files:
        original = file_path.read_text(encoding="utf-8", errors="ignore").strip()
        prompt = build_prompt(original)
        summary, status = openai_summarize(prompt)

        # Build output for Done/
        output = (
            "# Processed Task\n\n"
            "## Original Content\n"
            f"{original}\n\n"
            "## AI Summary\n"
            f"{summary}\n\n"
            "Status: Completed\n"
        )

        # Write processed file into Done/
        dest = DONE / file_path.name
        dest.write_text(output, encoding="utf-8")

        # Remove from Needs_Action
        file_path.unlink()

        # Append run_log.md
        append_line(RUN_LOG, f"{utc_ts()} - Processed: {file_path.name} | {status}\n")

        # Append prompt_history.md
        prompt_or_fallback = "fallback" if status == "fallback" else prompt
        prompt_block = (
            f"---\n"
            f"[{utc_ts()}] FILE: {file_path.name}\n"
            f"MODEL: {MODEL}\n"
            f"STATUS: {status}\n"
            f"PROMPT:\n{prompt_or_fallback}\n"
            f"---\n\n"
        )
        append_line(PROMPT_HISTORY, prompt_block)

        print(f"Processed: {file_path.name} ({status})")

    print("=== Done ===")


if __name__ == "__main__":
    main()
