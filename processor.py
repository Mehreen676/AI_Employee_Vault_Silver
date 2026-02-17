import os
import shutil
from datetime import datetime

VAULT_PATH = r"C:\Users\Zohair\Desktop\AI_Employee_Vault"

NEEDS_ACTION = os.path.join(VAULT_PATH, "Needs_Action")
DONE = os.path.join(VAULT_PATH, "Done")
SKILL_FILE = os.path.join(VAULT_PATH, "skills", "process_task.SKILL.md")
LOG_FILE = os.path.join(VAULT_PATH, "run_log.md")

print("===================================")
print(" AI Employee Processor (Skill Mode)")
print("===================================\n")

def load_skill():
    if os.path.exists(SKILL_FILE):
        with open(SKILL_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "No skill definition found."

def log_run(filename):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now()}] Skill executed on: {filename}\n")

skill_definition = load_skill()
files = os.listdir(NEEDS_ACTION)

if not files:
    print("No tasks found in Needs_Action.")
else:
    for file in files:
        if file.endswith(".md"):
            file_path = os.path.join(NEEDS_ACTION, file)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            summary = f"""
# Processed Task

## Skill Used
process_task.SKILL.md

## Original Content
{content}

## AI Summary
This task has been processed according to the defined Agent Skill workflow.

Status: Completed
"""

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(summary)

            shutil.move(file_path, os.path.join(DONE, file))
            log_run(file)

            print(f"Skill processed and moved: {file}")

print("\nProcessing Complete.")
