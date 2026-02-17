import os
from datetime import datetime

VAULT_PATH = r"C:\Users\Zohair\Desktop\AI_Employee_Vault"
NEEDS_ACTION = os.path.join(VAULT_PATH, "Needs_Action")
PROMPTS = os.path.join(VAULT_PATH, "prompts")

def normalize_md(filename: str) -> str:
    """
    Ensures the filename ends with exactly one '.md'
    Handles cases like 'x.md.md' or 'x' (no extension).
    """
    name = filename
    while name.lower().endswith(".md"):
        name = name[:-3]
    return name + ".md"

def pick_task():
    if not os.path.isdir(NEEDS_ACTION):
        raise FileNotFoundError(f"Needs_Action folder not found: {NEEDS_ACTION}")

    files = [f for f in os.listdir(NEEDS_ACTION) if f.lower().endswith(".md")]
    files.sort()
    return files[0] if files else None

def main():
    os.makedirs(PROMPTS, exist_ok=True)

    task = pick_task()
    if not task:
        print("No tasks found in Needs_Action.")
        return

    task_md = normalize_md(task)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    prompt_filename = normalize_md(f"{ts}__process__{task_md}")
    prompt_file = os.path.join(PROMPTS, prompt_filename)

    prompt = f"""# Claude Run Prompt — Process Task

## Context
You must act as the AI Employee Agent. Follow:
- ./CLAUDE.md
- ./skills/process_task.SKILL.md

## Task File
- ./Needs_Action/{task_md}

## Instructions
1) Read ./skills/process_task.SKILL.md
2) Read ./Needs_Action/{task_md}
3) Rewrite ./Needs_Action/{task_md} using the skill template
4) Move ./Needs_Action/{task_md} to ./Done/{task_md}
5) Append a log line to ./run_log.md:
   [YYYY-MM-DD HH:MM] {task_md} -> TASK_COMPLETE
6) Reply only: TASK_COMPLETE
"""

    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    print("Prompt generated:")
    print(prompt_file)
    print("\nNext:")
    print("1) Open this prompt file in VS Code")
    print("2) Paste its contents into Claude Code chat")
    print("3) Approve read/write/mv permissions when asked")

if __name__ == "__main__":
    main()
