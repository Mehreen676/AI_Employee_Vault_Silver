🤖 AI Employee Vault — Bronze Tier (Hackathon 0)

A structured Personal AI Employee system built using an Obsidian Vault + Local Python automation.

This implementation follows the official Hackathon 0 Bronze Tier specification and demonstrates a complete end-to-end AI task workflow.

🎯 Objective

To simulate a Personal AI Employee that:

Monitors incoming tasks

Processes them using defined Agent Skills

Updates task status

Maintains workflow structure

Moves completed work to archive

🧠 Bronze Tier Requirements (PDF Compliant)

This project satisfies ALL Bronze Tier requirements:

✔ Obsidian Vault structure created
✔ Inbox → Needs_Action → Done workflow implemented
✔ Filesystem watcher implemented (watcher.py)
✔ AI processing script implemented (processor.py)
✔ Agent Skill documented in /skills
✔ End-to-end task lifecycle verified
✔ Prompt history logging implemented
✔ Git version control configured
✔ Clean project documentation provided

Status: 100% Bronze Tier Complete

🏗️ System Architecture
User drops task → Inbox
        ↓
watcher.py detects new file
        ↓
File moved to Needs_Action
        ↓
processor.py processes task
        ↓
AI summary appended
        ↓
Status marked Completed
        ↓
File moved to Done

📁 Vault Structure
AI_Employee_Vault/
│
├── Inbox/
├── Needs_Action/
├── Done/
│
├── skills/
│   └── process_task.SKILL.md
│
├── specs/
│
├── Company_Handbook.md
├── Dashboard.md
├── Welcome.md
├── CLAUDE.md
├── prompt_history.md
│
├── watcher.py
└── processor.py

⚙️ Requirements

Python 3.x

Windows / PowerShell

Obsidian (recommended for vault visualization)

Git (for version control)

🚀 How to Run
1️⃣ Start the Watcher (Inbox → Needs_Action)
cd C:\Users\Zohair\Desktop\AI_Employee_Vault
python watcher.py


Now create a markdown task inside:

Inbox/


Example:

skill_test.md

2️⃣ Process Tasks (Needs_Action → Done)

Open a second terminal:

cd C:\Users\Zohair\Desktop\AI_Employee_Vault
python processor.py


The task will:

Be rewritten in processed format

Include AI Summary section

Be marked as Completed

Move automatically to /Done

🧠 Agent Skill (Bronze Implementation)

All AI functionality is implemented as a documented Agent Skill:

skills/process_task.SKILL.md


Skill Definition Includes:

Task reading logic

Summary generation

Status update

File movement logic

Output confirmation (TASK_COMPLETE)

This aligns with Bronze requirement:

“All AI functionality should be implemented as Agent Skills.”

🧪 Workflow Verification

Tested Successfully:

✔ Inbox detection
✔ File auto-movement
✔ Task rewriting
✔ Status tagging
✔ Archive movement
✔ Git commit + push

📊 Implementation Level
Feature	Status
Vault Structure	✅ Complete
Task Monitoring	✅ Complete
Task Processing	✅ Complete
Agent Skill Definition	✅ Complete
GitHub Repository	✅ Live
README Documentation	✅ Complete
🔮 Future Enhancements (Silver / Gold Ready)

This architecture is designed to scale toward:

Background daemon service

Multi-Skill architecture

Approval workflows

Cloud deployment

API-based AI integration

Multi-agent routing

Logging & analytics dashboard

👨‍💻 Developer

Mehreen Asghar
Hackathon 0 — Bronze Tier Submission

## How to Demo Silver

### Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`
- (Optional) Set `OPENAI_API_KEY` env var for real AI summaries

### Local Demo Steps

1. **Drop a task file** into `Needs_Action/`:
   ```
   echo "Summarize Q4 sales data" > Needs_Action/demo-task.md
   ```

2. **Run the agent**:
   ```
   python agent.py
   ```

3. **Verify outputs**:
   - `Done/demo-task.md` — contains `# Processed Task`, `## Original Content`, `## AI Summary`, and `Status: Completed`
   - `run_log.md` — new line with UTC timestamp, filename, and status
   - `prompt_history.md` — full prompt log (or "fallback" if no API key)

4. **Run again with empty queue** — agent prints "No tasks found" and exits cleanly (no crash).

### Cloud Demo (GitHub Actions)
- Push a `.md` file into `Needs_Action/` and commit.
- Go to **Actions > Silver Agent (Cloud Run) > Run workflow** (or wait for the 10-min cron).
- The bot commits processed results back automatically.

### What the Judge Sees
| Check | Evidence |
|-------|----------|
| Reads from `Needs_Action/*.md` | `agent.py` line 86 |
| OpenAI summarization (with key) | `agent.py` line 57-69 |
| Graceful fallback (no key/crash) | `agent.py` line 51-55 |
| Output format in `Done/` | `# Processed Task` > `## Original Content` > `## AI Summary` > `Status: Completed` |
| `run_log.md` updated | UTC timestamp + filename + status per run |
| `prompt_history.md` updated | Full prompt or "fallback" logged per file |
| GitHub Actions every 10 min | `.github/workflows/silver-agent.yml` cron |
| No infinite loop | Workflow triggers: `schedule` + `workflow_dispatch` only (no `push`) |

🏁 Final Status

🟢 Bronze Tier: Fully Implemented
🟢 Silver Tier: Fully Implemented
🟢 PDF Requirements: 100% Covered
🟢 End-to-End Workflow: Verified