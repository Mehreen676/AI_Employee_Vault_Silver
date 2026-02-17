🤖 AI Employee Vault — Silver Tier (Hackathon 0)

An advanced Personal AI Employee system built using a structured vault architecture, multi-channel task ingestion, MCP-style tool abstraction, Human-in-the-Loop approval, and optional OpenAI-powered processing.

This implementation fully satisfies the Hackathon 0 Silver Tier specification and demonstrates a complete end-to-end intelligent task lifecycle.

🎯 Objective

To simulate a production-style AI employee that:

Accepts tasks from multiple input channels

Processes tasks using an AI reasoning layer

Generates structured execution plans

Logs full prompt history for auditability

Requires human approval before completion

Uses tool abstraction (MCP-style)

Runs locally and via cloud scheduling

🏗️ System Architecture (Silver Pipeline)
Gmail / Manual Input / Inbox
            ↓
        Watchers (3)
            ↓
      Needs_Action/
            ↓
         agent.py
            ↓
    Plans/<task>_Plan.md
            ↓
    Pending_Approval/
            ↓
        approve.py
            ↓
          Done/

📁 Project Structure
AI_Employee_Vault_Silver/
│
├── Inbox/
├── Needs_Action/
├── Pending_Approval/
├── Done/
├── Plans/
│
├── gmail_watcher.py
├── watcher_inbox.py
├── watcher_manual.py
├── agent.py
├── approve.py
├── mcp_server.py
│
├── prompt_history.md
├── run_log.md
│
└── .github/workflows/silver-agent.yml

🔁 Silver Tier Features
1️⃣ Multi-Channel Task Ingestion (3 Watchers)
watcher_inbox.py

Moves tasks from Inbox/ → Needs_Action/

python watcher_inbox.py

watcher_manual.py

Reads manual_input.txt, splits tasks using ---, and creates files in Needs_Action/.

python watcher_manual.py

gmail_watcher.py (Local Ingestion)

Reads unread Gmail messages via Gmail API

Filters trusted domains:

google.com

github.com

microsoft.com

azure.com

Skips duplicates

Logs all ingestion events

python gmail_watcher.py


⚠ Gmail OAuth credentials are gitignored and never used in cloud workflow.

2️⃣ Human-in-the-Loop (HITL) Approval

Tasks do NOT auto-complete.

Needs_Action → agent.py → Pending_Approval → approve.py → Done


Manual approval required:

python approve.py
python approve.py task.md
python approve.py --all


This ensures governance and prevents autonomous completion.

3️⃣ Plan.md Reasoning Layer

For every task processed:

Plans/<taskname>_Plan.md


Contains:

Task analysis

Step-by-step plan

Risk identification

Output checklist

This simulates structured reasoning before execution.

4️⃣ MCP-Style Tool Layer

mcp_server.py provides:

Tool	Purpose
list_tasks(folder)	Lists markdown tasks
move_task(src, dst)	Safely moves files

agent.py and approve.py use these tools instead of direct file operations.

This demonstrates tool abstraction similar to Model Context Protocol (MCP).

5️⃣ OpenAI Integration (Safe Mode)

agent.py supports:

Model: gpt-4o-mini

Graceful fallback if API key missing

Never crashes

Logs model + status

Statuses logged:

openai_ok

openai_error

fallback

6️⃣ Full Logging & Traceability
run_log.md

Logs:

File movements

Watcher events

Processing status

Approval actions

UTC timestamps

prompt_history.md

Logs:

Full prompt

Model used

File processed

Status result

This creates a complete audit trail.

7️⃣ Cloud Automation (GitHub Actions)

Workflow:
.github/workflows/silver-agent.yml

Runs every 10 minutes:

watcher_inbox.py

watcher_manual.py

agent.py

Commit updates

Triggers:

schedule

workflow_dispatch

No push trigger → No infinite loops.

🚀 How to Run (Local Demo)
1️⃣ Add Task
echo "Summarize Q4 revenue trends" > Inbox/demo.md

2️⃣ Run Watcher
python watcher_inbox.py

3️⃣ Run Agent
python agent.py

4️⃣ Review

Pending_Approval/demo.md

Plans/demo_Plan.md

run_log.md

prompt_history.md

5️⃣ Approve
python approve.py demo.md


File moves to Done/.

📊 Silver Compliance Checklist
Requirement	Status
Multiple Watchers	✅ 3 Implemented
Human Approval Layer	✅
Plan.md Reasoning	✅
MCP Tool Abstraction	✅
OpenAI Integration	✅
Full Logging	✅
Prompt History	✅
Cloud Scheduled Execution	✅
Safe Fallback Mode	✅
🏁 Final Status

🟢 Silver Tier — Fully Implemented
🟢 End-to-End Workflow — Verified
🟢 MCP Tool Layer — Active
🟢 Human-in-the-Loop — Enforced
🟢 Cloud Automation — Live