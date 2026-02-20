![Silver Agent Status](https://img.shields.io/badge/Silver-Agent-Cloud_Automated-brightgreen)
![HITL](https://img.shields.io/badge/HITL-Enabled-blue)
![MCP](https://img.shields.io/badge/MCP-Integrated-orange)

# AI Employee Vault — Silver Tier (Hackathon 0)

A fully production-grade **Personal AI Employee** system with multi-channel task ingestion,
Claude/OpenAI-powered reasoning plans, LinkedIn HITL auto-posting, MCP-style tool abstraction,
and cloud scheduling via GitHub Actions.

---

## System Architecture

```
Watchers (Inbox / Manual / WhatsApp / LinkedIn / Gmail)
        ↓
Needs_Action
        ↓
Agent (Plan Generator)
        ↓
Pending_Approval (HITL)
        ↓
Approved
        ↓
Post + Done
        ↓
Logs + Evidence Pack
```

---

## LinkedIn Posting Mode

By default, LinkedIn posting runs in **SIMULATED MODE**.

Real posting is only enabled when valid credentials are provided:
- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_PERSON_URN`

This prevents unintended public posts.

Transparency = audit trust.

---

## Pipeline Diagram

```
Inbox/          manual_input.txt   whatsapp_input.txt   linkedin_input.txt   Gmail (guarded)
   |                  |                   |                    |                   |
[watcher_inbox] [watcher_manual]  [whatsapp_watcher]  [linkedin_watcher]   [gmail_watcher]
        \               \                /                   /
         +-----------+--+------+--------+
                     |
               Needs_Action/
                     |
                 [agent.py]
                /          \
    Plans/<task>_Plan.md    Pending_Approval/<task>.md
                                  |
                    (if marketing) +-- Pending_Approval/linkedin_draft_<task>.md
                                  |
                           [approve.py]  ← HUMAN ONLY (manual CLI)
                                  |
                            Approved/
                                  |
                          [post_approved.py]
                          /              \
             linkedin_* -> LinkedIn API    move to Done/
             (or simulated evidence)       (on success)
```

---

## Full File Structure

```
AI_Employee_Vault_Silver/
│
├── Inbox/                          # Raw email drops / Obsidian tasks
├── Needs_Action/                   # Queued tasks for agent
├── Pending_Approval/               # Agent output awaiting human approval
├── Approved/                       # Human-approved items (ready to post)
├── Done/                           # Completed tasks
├── Plans/                          # <task>_Plan.md reasoning plans
├── Logs/                           # events_<date>.jsonl + summary_<ts>.md
│
├── watcher_inbox.py                # Watcher 1: Inbox -> Needs_Action
├── watcher_manual.py               # Watcher 2: manual_input.txt -> Needs_Action
├── whatsapp_watcher.py             # Watcher 3: whatsapp_input.txt (simulated)
├── linkedin_watcher.py             # Watcher 4: linkedin_input.txt (simulated)
├── gmail_watcher.py                # Watcher 5: Gmail API (local + guarded cloud)
│
├── agent.py                        # Core agent: Plans + summaries + LinkedIn drafts
├── approve.py                      # HITL: Pending_Approval -> Approved (manual)
├── post_approved.py                # LinkedIn poster: Approved -> Done
│
├── mcp_file_ops.py                 # MCP tool: safe file helpers
├── mcp_linkedin_ops.py             # MCP tool: LinkedIn UGC Post API + simulated
├── mcp_email_ops.py                # MCP tool: SMTP email (BONUS)
├── mcp_calendar_ops.py             # MCP tool: calendar events (BONUS)
├── mcp_server.py                   # Original MCP server (backward compat)
├── evidence_pack.py                # BONUS: zip evidence for judges
│
├── run_log.md                      # Human-readable UTC audit log
├── prompt_history.md               # Full prompt audit trail
│
├── manual_input.txt                # Drop tasks here (split by ---)
├── whatsapp_input.txt              # Simulated WhatsApp DMs
├── linkedin_input.txt              # Simulated LinkedIn DMs/leads
│
├── .env.example                    # Template for env vars
├── requirements.txt
├── .gitignore
└── .github/workflows/silver-agent.yml
```

---

## Silver Tier Compliance Checklist

| Requirement | Status |
|-------------|--------|
| **A1** watcher_inbox.py (Inbox → Needs_Action) | ✅ |
| **A2** watcher_manual.py (manual_input.txt → Needs_Action) | ✅ |
| **A3** whatsapp_watcher.py (simulated, whatsapp_input.txt) | ✅ |
| **A4** gmail_watcher.py (Gmail API, domain filter, dedup, cloud guard) | ✅ |
| **A5 BONUS** linkedin_watcher.py (simulated, linkedin_input.txt) | ✅ |
| **B** Plans/<task>_Plan.md per task (analysis, steps, risks, checklist) | ✅ |
| **B** OpenAI plan generation + deterministic fallback (no crash) | ✅ |
| **B** prompt_history.md logging (model, status, full prompt) | ✅ |
| **C1** mcp_file_ops.py (list/read/write/move/copy helpers) | ✅ |
| **C2** mcp_linkedin_ops.py (create_post + simulated mode + evidence) | ✅ |
| **C2 BONUS** LINKEDIN_SIMULATED mode + evidence JSON | ✅ |
| **C3 BONUS** mcp_email_ops.py (SMTP + simulated mode) | ✅ |
| **C4 BONUS** mcp_calendar_ops.py (local simulated store) | ✅ |
| **D** agent.py detects business tasks, creates LinkedIn Draft Approval | ✅ |
| **D** LinkedIn draft format: title, source, post text, status, risk note, hash | ✅ |
| **D** post_approved.py: scans Approved/, posts, moves to Done/ | ✅ |
| **D BONUS** Idempotency: posted_ids.json prevents double-posting | ✅ |
| **E** approve.py: Pending_Approval → Approved (NEVER auto-approve) | ✅ |
| **E** approve.py --all, approve.py file.md, approve.py (list) | ✅ |
| **F** GitHub Actions: every 10 min + workflow_dispatch (no push trigger) | ✅ |
| **F** Workflow step order: watchers → agent → post_approved → commit | ✅ |
| **F** Gmail guard: only runs if GMAIL_OAUTH_ENABLED=true | ✅ |
| **F** Safe push: git pull --rebase before push | ✅ |
| **F** Commits only relevant dirs (Needs_Action, Plans, Logs, etc.) | ✅ |
| **G** README: pipeline diagram, checklist, demo steps, secrets setup | ✅ |
| **G** Judge Quick Demo section | ✅ |
| **H** .gitignore: .env, credentials.json, token.json, __pycache__ | ✅ |
| **H** .env.example with all keys | ✅ |
| **I BONUS** Structured event logging: Logs/events_<date>.jsonl | ✅ |
| **I BONUS** evidence_pack.py: zip for judges | ✅ |
| **I BONUS** Domain allowlist for Gmail + documented | ✅ |
| **I BONUS** Stats summary: Logs/summary_<ts>.md after each agent run | ✅ |

---

## Secrets Setup

Add these as **GitHub Repository Secrets** (Settings → Secrets → Actions):

| Secret | Required | Description |
|--------|----------|-------------|
| `OPENAI_API_KEY` | Optional | OpenAI key; agent uses fallback if missing |
| `OPENAI_MODEL` | Optional | Default: `gpt-4o-mini` |
| `LINKEDIN_ACCESS_TOKEN` | Optional | LinkedIn OAuth token for live posting |
| `LINKEDIN_PERSON_URN` | Optional | e.g. `urn:li:person:AbCdEfGh` |
| `LINKEDIN_SIMULATED` | Optional | `true` = simulated mode (default: true) |
| `GMAIL_OAUTH_ENABLED` | Optional | `true` = run Gmail watcher in cloud (default: false) |

Copy `.env.example` to `.env` for local development (never commit `.env`).

---

## Local Demo — Step by Step

### Prerequisites
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY at minimum
```

### 1. Add a business task (triggers LinkedIn draft)
```bash
echo "Launch marketing campaign for our new AI product on LinkedIn with enterprise focus." > Inbox/business_task.md
```

### 2. Run all watchers
```bash
python watcher_inbox.py
python watcher_manual.py
python whatsapp_watcher.py
python linkedin_watcher.py
# Gmail (local only, needs credentials.json):
# GMAIL_OAUTH_ENABLED=true python gmail_watcher.py
```

### 3. Run the agent
```bash
python agent.py
```
Agent creates:
- `Plans/business_task_Plan.md` — reasoning plan
- `Pending_Approval/business_task.md` — processed task awaiting approval
- `Pending_Approval/linkedin_draft_business_task_<hash>.md` — LinkedIn draft

### 4. Verify Plans were created
```bash
ls Plans/
cat "Plans/business_task_Plan.md"
```

### 5. Verify LinkedIn draft in Pending_Approval
```bash
ls Pending_Approval/
cat "Pending_Approval/linkedin_draft_business_task_<hash>.md"
```

### 6. Human approval (HITL)
```bash
# List pending
python approve.py

# Approve the LinkedIn draft specifically
python approve.py "linkedin_draft_business_task_<hash>.md"

# Or approve everything
python approve.py --all
```
Files move from `Pending_Approval/` → `Approved/`.

### 7. Post to LinkedIn (or simulate)
```bash
# Without credentials — simulated evidence written to Logs/
python post_approved.py

# With LinkedIn credentials set in .env — real post
LINKEDIN_SIMULATED=false python post_approved.py
```

### 8. Verify logs
```bash
cat run_log.md
cat prompt_history.md
ls Logs/
cat Logs/events_$(date +%Y-%m-%d).jsonl   # structured events
cat Logs/summary_*.md                      # run stats
```

### 9. Generate evidence pack (for judges)
```bash
python evidence_pack.py
# Creates evidence_<timestamp>.zip
```

---

## Judge Quick Demo (2-3 minutes)

1. **Watchers** — Drop a task in `Inbox/` and run `python watcher_inbox.py`. Check `Needs_Action/`.
2. **Agent + Plans** — Run `python agent.py`. Check `Plans/` for `*_Plan.md` and `Pending_Approval/` for the processed task + LinkedIn draft.
3. **HITL Approval** — Run `python approve.py` to see pending list. Run `python approve.py --all` to approve. Check `Approved/`.
4. **LinkedIn Post** — Run `python post_approved.py`. Without credentials, simulated evidence appears in `Logs/linkedin_simulated_*.json`.
5. **Audit Trail** — Open `run_log.md`, `prompt_history.md`, `Logs/events_*.jsonl`, `Logs/summary_*.md`.
6. **Evidence Pack** — Run `python evidence_pack.py`. Share the generated ZIP.

---

## Gmail Domain Allowlist

Only emails from these domains are ingested by `gmail_watcher.py`:
- `google.com`
- `github.com`
- `microsoft.com`
- `azure.com`
- `anthropic.com`

To add more domains, edit the `ALLOWED_DOMAINS` set in `gmail_watcher.py`.

---

## Screenshots / Evidence Placeholders

| Evidence | Path |
|----------|------|
| Run log | `run_log.md` |
| Prompt history | `prompt_history.md` |
| Plans directory | `Plans/` |
| Pending approval | `Pending_Approval/` |
| Approved directory | `Approved/` |
| Done directory | `Done/` |
| Structured events | `Logs/events_<date>.jsonl` |
| Run summary | `Logs/summary_<timestamp>.md` |
| LinkedIn evidence | `Logs/linkedin_simulated_<timestamp>.json` |
| Evidence ZIP | `evidence_<timestamp>.zip` |

---

## Status

🟢 **Silver Tier — Fully Implemented + All Bonus Items**
🟢 End-to-End Pipeline — Verified
🟢 MCP Tool Layer — 4 modules (file, linkedin, email, calendar)
🟢 Human-in-the-Loop — Enforced (approve.py required)
🟢 LinkedIn HITL + Idempotency — Active
🟢 Cloud Automation — GitHub Actions (5 watchers + agent + poster)
🟢 Simulated Mode — All features work without credentials
🟢 Evidence Pack — `python evidence_pack.py`
