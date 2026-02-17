import os
import time
import shutil
from datetime import datetime

# ====== CONFIG ======
VAULT_PATH = r"C:\Users\Zohair\Desktop\AI_Employee_Vault"

INBOX = os.path.join(VAULT_PATH, "Inbox")
NEEDS_ACTION = os.path.join(VAULT_PATH, "Needs_Action")
LOG_FILE = os.path.join(VAULT_PATH, "run_log.md")

print("===================================")
print(" AI Employee Watcher Started ")
print("===================================")
print(f"Monitoring Folder: {INBOX}")
print("Press Ctrl + C to stop\n")

# Ensure folders exist
if not os.path.exists(INBOX):
    print("Inbox folder not found!")
    exit()

if not os.path.exists(NEEDS_ACTION):
    print("Needs_Action folder not found!")
    exit()

def log_action(filename):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n---\n")
        log.write(f"Time: {timestamp}\n")
        log.write(f"File: {filename}\n")
        log.write(f"Action: Moved to Needs_Action\n")

while True:
    try:
        files = os.listdir(INBOX)

        if files:
            for file in files:
                if file.endswith(".md"):
                    source = os.path.join(INBOX, file)
                    destination = os.path.join(NEEDS_ACTION, file)

                    shutil.move(source, destination)
                    log_action(file)
                    print(f"Moved: {file} → Needs_Action")

        time.sleep(3)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
