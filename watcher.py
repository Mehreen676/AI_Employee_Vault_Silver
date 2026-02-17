import os
import time
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ✅ Cross-platform vault root (local + cloud)
BASE_DIR = Path(__file__).resolve().parent

INBOX = BASE_DIR / "Inbox"
NEEDS_ACTION = BASE_DIR / "Needs_Action"
LOG_FILE = BASE_DIR / "run_log.md"

print("===================================")
print(" AI Employee Watcher Started ")
print("===================================")
print(f"Monitoring Folder: {INBOX}")
print("Press Ctrl + C to stop\n")

# Ensure folders exist
INBOX.mkdir(parents=True, exist_ok=True)
NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

def log_action(filename: str):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write("\n---\n")
        log.write(f"Time: {timestamp}\n")
        log.write(f"File: {filename}\n")
        log.write("Action: Moved to Needs_Action\n")
        log.write("Action: Triggered processor.py\n")

def run_processor():
    print("Triggering Silver processor automatically...")
    # ✅ use same python running watcher (better for venv)
    subprocess.run([os.sys.executable, "processor.py"], check=False)

while True:
    try:
        files = os.listdir(INBOX)

        moved_any = False

        if files:
            for file in files:
                if file.endswith(".md"):
                    source = INBOX / file
                    destination = NEEDS_ACTION / file

                    shutil.move(str(source), str(destination))
                    print(f"Moved: {file} → Needs_Action")
                    log_action(file)
                    moved_any = True

        # ✅ Silver autonomy: if something moved, run processor automatically
        if moved_any:
            run_processor()

        time.sleep(3)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
