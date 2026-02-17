import os
import shutil
from datetime import datetime
from pathlib import Path

# ✅ Cross-platform vault root:
# - Cloud (GitHub Actions) me: repo root
# - Local me: current folder (same repo)
BASE_DIR = Path(__file__).resolve().parent

NEEDS_ACTION = BASE_DIR / "Needs_Action"
DONE = BASE_DIR / "Done"
SKILL_FILE = BASE_DIR / "skills" / "process_task.SKILL.md"
LOG_FILE = BASE_DIR / "run_log.md"

print("===================================")
print(" AI Employee Processor (Skill Mode)")
print("===================================\n")

def ensure_dirs():
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "skills").mkdir(parents=True, exist_ok=True)

def load_skill():
    if SKILL_FILE.exists():
        return SKILL_FILE.read_text(encoding="utf-8")
    return "No skill definition found."

def log_run(filename: str):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}] Skill executed on: {filename}\n")

ensure_dirs()

skill_definition = load_skill()  # (Silver: keep for future use)
files = os.listdir(NEEDS_ACTION)

if not files:
    print("No tasks found in Needs_Action.")
else:
    for file in files:
        if file.endswith(".md"):
            file_path = NEEDS_ACTION / file

            content = file_path.read_text(encoding="utf-8", errors="ignore")

            summary = f"""# Processed Task

## Skill Used
process_task.SKILL.md

## Original Content
{content}

## AI Summary
This task has been processed according to the defined Agent Skill workflow.

Status: Completed
"""

            file_path.write_text(summary, encoding="utf-8")

            shutil.move(str(file_path), str(DONE / file))
            log_run(file)

            print(f"Skill processed and moved: {file}")

print("\nProcessing Complete.")
