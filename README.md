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

## Silver Tier Features

### 1. Two Watchers (2+ input channels)

**watcher_inbox.py** — Moves `Inbox/*.md` files to `Needs_Action/` automatically.
```
python watcher_inbox.py
```

**watcher_manual.py** — Reads `manual_input.txt`, splits on `---`, creates individual task files in `Needs_Action/`.
```
# Add tasks to manual_input.txt:
echo "Review quarterly budget\n---\nDraft client email" > manual_input.txt
python watcher_manual.py
```

Both watchers log every action to `run_log.md` with UTC timestamps.

### 2. Human-in-the-Loop Approval (HITL)

Tasks no longer go directly to `Done/`. The new flow:

```
Needs_Action/ --> agent.py --> Pending_Approval/ --> approve.py --> Done/
```

- `agent.py` processes tasks and places drafts in `Pending_Approval/`
- A human must run `approve.py` to move them to `Done/`
- Cloud workflow does NOT auto-approve — approval is manual only

```
python approve.py              # list pending files
python approve.py task.md      # approve one file
python approve.py --all        # approve all pending
```

### 3. Plan.md Reasoning Loop

For every task, `agent.py` generates a plan file in `Plans/`:

```
Plans/<taskname>_Plan.md
```

Each plan contains:
- Task Analysis
- Step-by-step Plan
- Risks / Edge cases
- Output format checklist

Plan generation is logged in `prompt_history.md` (model + status + full prompt or "fallback").

### 4. MCP-Style Tool Integration

`mcp_server.py` provides two callable tools used by the agent:

| Tool | Description |
|------|-------------|
| `list_tasks(folder)` | Returns list of `*.md` filenames in a folder |
| `move_task(src, dst)` | Moves a file and returns success boolean |

`agent.py` and `approve.py` import and use these tools instead of direct file operations. This simulates MCP (Model Context Protocol) tool usage locally.

### 5. Gmail Watcher (Local Ingestion)

`gmail_watcher.py` reads unread Gmail inbox emails via the Gmail API and creates task files in `Inbox/`.

- Filters senders to trusted domains only: `google.com`, `github.com`, `microsoft.com`, `azure.com`
- Skips duplicates (checks Inbox/ and Done/ for existing messageId)
- Each email becomes `Inbox/email_YYYYMMDD_HHMMSS_<messageId>.md`
- Logs every ingestion to `run_log.md`

**How to run locally:**
```bash
# First time: place credentials.json in repo root (from Google Cloud Console)
# Install Gmail API deps:
pip install google-auth google-auth-oauthlib google-api-python-client

# Run the watcher:
python gmail_watcher.py

# Then run the inbox watcher to move emails into the pipeline:
python watcher_inbox.py
```

> Gmail watcher is **local only** — OAuth credentials are gitignored and never used in the cloud workflow. GitHub Actions processes whatever lands in `Inbox/` or `Needs_Action/` regardless of source.

### 6. Cloud Scheduled Run (GitHub Actions)

`.github/workflows/silver-agent.yml` runs every 10 minutes:
1. `python watcher_inbox.py` — ingest Inbox tasks
2. `python watcher_manual.py` — ingest manual tasks
3. `python agent.py` — process + generate plans + send to Pending_Approval
4. Commit & push all changes back to repo

Triggers: `schedule` + `workflow_dispatch` only (no `push` = no infinite loops).

---

## How to Demo Silver

### Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`
- (Optional) Set `OPENAI_API_KEY` env var for real AI summaries

### Full Demo Steps

1. **Drop a task** into Inbox or Needs_Action:
   ```
   echo "Summarize Q4 sales data" > Inbox/demo-task.md
   ```

2. **Run the watchers** to ingest:
   ```
   python watcher_inbox.py
   ```

3. **Run the agent** to process + plan:
   ```
   python agent.py
   ```

4. **Check outputs**:
   - `Pending_Approval/demo-task.md` — processed draft awaiting approval
   - `Plans/demo-task_Plan.md` — reasoning plan
   - `run_log.md` — timestamped log entries
   - `prompt_history.md` — full prompts logged

5. **Approve the task** (HITL):
   ```
   python approve.py demo-task.md
   ```

6. **Verify**: `Done/demo-task.md` now contains the final output.

### What the Judge Sees

| Requirement | Evidence |
|-------------|----------|
| 3 watchers | `watcher_inbox.py` + `watcher_manual.py` + `gmail_watcher.py` |
| HITL approval | `approve.py` — manual approval required |
| Plan.md reasoning | `Plans/<task>_Plan.md` generated per task |
| MCP tools | `mcp_server.py` — `list_tasks` + `move_task` |
| OpenAI summarization | `agent.py` `openai_call()` with graceful fallback |
| Logs with UTC timestamps | `run_log.md` + `prompt_history.md` |
| GitHub Actions (10 min) | `.github/workflows/silver-agent.yml` cron |
| No infinite loop | No `push` trigger in workflow |
| Never crashes | Graceful fallback on missing key/folders/files |

🏁 Final Status

🟢 Bronze Tier: Fully Implemented
🟢 Silver Tier: Fully Implemented
🟢 PDF Requirements: 100% Covered
🟢 End-to-End Workflow: Verified