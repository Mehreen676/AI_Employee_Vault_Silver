from pathlib import Path
from datetime import datetime
import shutil

BASE_DIR = Path(__file__).resolve().parent
INBOX = BASE_DIR / "Inbox"
NEEDS = BASE_DIR / "Needs_Action"
DONE = BASE_DIR / "Done"
LOG = BASE_DIR / "prompt_history.md"

INBOX.mkdir(exist_ok=True)
NEEDS.mkdir(exist_ok=True)
DONE.mkdir(exist_ok=True)

def log(line: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    LOG.write_text((LOG.read_text(encoding="utf-8") if LOG.exists() else "") + f"\n[{ts}] {line}", encoding="utf-8")

def choose_skill(text: str) -> str:
    t = text.lower()
    if t.startswith("linkedin:"):
        return "linkedin_post"
    return "process_task"

def run_skill(skill: str, text: str) -> str:
    if skill == "linkedin_post":
        content = text.split(":", 1)[1].strip() if ":" in text else text
        return f"# LinkedIn Draft\n\n{content}\n\n#AI #Automation #Productivity"
    return f"# Processed Task\n\n{text}\n\n✅ Status: Completed"

def main():
    log("Silver Agent started (skill routing enabled).")
    for f in INBOX.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue

        skill = choose_skill(text)
        log(f"Decision: file={f.name} -> skill={skill}")

        # move to Needs_Action
        needs_file = NEEDS / f.name
        shutil.move(str(f), str(needs_file))
        log(f"Move: Inbox -> Needs_Action ({needs_file.name})")

        # execute skill
        output = run_skill(skill, text)
        needs_file.write_text(output, encoding="utf-8")

        # move to Done
        done_file = DONE / needs_file.name
        shutil.move(str(needs_file), str(done_file))
        log(f"Move: Needs_Action -> Done ({done_file.name})")

    log("Silver Agent run completed.")

if __name__ == "__main__":
    main()
