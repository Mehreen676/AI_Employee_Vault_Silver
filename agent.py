from pathlib import Path
import shutil
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
NEEDS_ACTION = BASE_DIR / "Needs_Action"
DONE = BASE_DIR / "Done"
LOG_FILE = BASE_DIR / "run_log.md"

print("=== Silver Cloud Agent Running ===")

NEEDS_ACTION.mkdir(exist_ok=True)
DONE.mkdir(exist_ok=True)

files = list(NEEDS_ACTION.glob("*.md"))

if not files:
    print("No tasks found.")
else:
    for file_path in files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        summary = f"""# Processed Task

## Original Content
{content}

## AI Summary
Cloud Silver Agent processed this task successfully.

Status: Completed
"""

        file_path.write_text(summary, encoding="utf-8")

        shutil.move(str(file_path), str(DONE / file_path.name))

        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"{datetime.utcnow()} - Processed: {file_path.name}\n")

        print(f"Processed: {file_path.name}")

print("=== Done ===")
