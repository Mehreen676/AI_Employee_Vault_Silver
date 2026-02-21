![Silver Agent](https://img.shields.io/badge/Silver%20Agent-Cloud%20Automated-brightgreen)
![HITL](https://img.shields.io/badge/HITL-Enabled-blue)
![MCP](https://img.shields.io/badge/MCP-Integrated-orange)

# AI Employee Vault — Silver Tier (Hackathon 0)

A **Personal AI Employee** system for Hackathon 0 Silver Tier. Implements multi-channel task ingestion, OpenAI-powered reasoning plans with deterministic fallback, LinkedIn Human-in-the-Loop (HITL) draft approval, MCP-style tool abstraction, and cloud scheduling via GitHub Actions.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER  (5 watchers)                      │
│                                                                       │
│  Inbox/  manual_input.txt  whatsapp_input.txt  linkedin_input.txt  Gmail│
│    │           │                  │                   │              │  │
│ [watcher_ [watcher_   [whatsapp_      [linkedin_    [gmail_          │  │
│  inbox]   manual]      watcher]        watcher]     watcher]        │  │
│     \        \             /               /           /             │  │
│      ╰────────╴───────────╴───────────────╴───────────╯             │  │
│                              │                                       │  │
│                        Needs_Action/                                 │  │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                      AGENT LAYER  (agent.py)                          │
│                                                                       │
│  skills/planning_skill.py   →  Plans/<task>_Plan.md                  │
│  skills/summarize_skill.py  →  Pending_Approval/<task>.md            │
│  skills/linkedin_skill.py   →  Pending_Approval/linkedin_draft_*.md  │
│                                (business tasks only)                  │
│                                                                       │
│  MCP tools used by agent:                                             │
│    mcp_file_ops.py      list / read / write / move                   │
│    mcp_linkedin_ops.py  LinkedIn UGC Post API + simulated            │
│    mcp_email_ops.py     SMTP email + simulated        (bonus)        │
│    mcp_calendar_ops.py  calendar events, simulated    (bonus)        │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                  HITL LAYER  (Human-in-the-Loop)                      │
│                                                                       │
│  Pending_Approval/                                                    │
│       │                                                               │
│  [approve.py]  ← MANUAL ONLY — human must run this                   │
│       │                                                               │
│  Approved/                                                            │
│       │                                                               │
│  [post_approved.py]  ← posts ONLY from Approved/                     │
│    ├── LinkedIn API  (or simulated evidence)                          │
│    └── moves file to Done/ on success                                 │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                       EVIDENCE LAYER                                  │
│                                                                       │
│  run_log.md                  human-readable UTC audit log             │
│  prompt_history.md           full prompt audit trail                  │
│  Logs/events_<date>.jsonl    structured JSONL events                  │
│  Logs/summary_<ts>.md        per-run stats (fallback count etc.)      │
│  Logs/linkedin_simulated_*.json  simulated post evidence              │
│  Logs/posted_ids.json        idempotency hash registry                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
AI_Employee_Vault_Silver/
│
├── Inbox/                      # Raw file drops — watcher_inbox picks these up
├── Needs_Action/               # Tasks queued for agent processing
├── Pending_Approval/           # Agent output awaiting human approval
├── Approved/                   # Human-approved items (ready to post)
├── Done/                       # Completed tasks and moved source files
├── Plans/                      # <task>_Plan.md reasoning plans
├── Logs/                       # events_<date>.jsonl + summary_<ts>.md + evidence
├── prompts/                    # Timestamped Claude run prompt logs
├── skills/                     # Skill modules used by agent.py
│   ├── planning_skill.py       #   structured plan generation
│   ├── summarize_skill.py      #   task summarisation
│   └── linkedin_skill.py       #   LinkedIn post draft creation
├── specs/                      # Requirement / spec documents
│
├── .github/workflows/
│   └── silver-agent.yml        # GitHub Actions: scheduled every 10 min + manual
│
├── watcher_inbox.py            # Watcher 1: Inbox/ → Needs_Action/
├── watcher_manual.py           # Watcher 2: manual_input.txt → Needs_Action/
├── whatsapp_watcher.py         # Watcher 3: whatsapp_input.txt (simulated)
├── linkedin_watcher.py         # Watcher 4: linkedin_input.txt (simulated, bonus)
├── gmail_watcher.py            # Watcher 5: Gmail API (exits cleanly if no credentials)
│
├── agent.py                    # Core agent: plans + summaries + LinkedIn drafts
├── approve.py                  # HITL: Pending_Approval → Approved (manual only)
├── post_approved.py            # LinkedIn poster: Approved → Done
│
├── mcp_file_ops.py             # MCP tool: file helpers
├── mcp_linkedin_ops.py         # MCP tool: LinkedIn UGC Post API + simulated
├── mcp_email_ops.py            # MCP tool: SMTP email + simulated  (bonus)
├── mcp_calendar_ops.py         # MCP tool: calendar events, simulated  (bonus)
├── mcp_server.py               # Original MCP server (backward compatibility)
│
├── evidence_pack.py            # Generates evidence ZIP for judges
├── JUDGE_PROOF.md              # Detailed compliance evidence guide
├── run_log.md                  # Human-readable UTC audit log
├── prompt_history.md           # Full prompt audit trail
│
├── manual_input.txt            # Drop manual tasks here (separator: ---)
├── whatsapp_input.txt          # Simulated WhatsApp DM input
├── linkedin_input.txt          # Simulated LinkedIn DM input
│
├── .env.example                # Template for all environment variables
├── requirements.txt
└── .gitignore
```

---

## Watchers

Five watchers ingest tasks from different sources into `Needs_Action/`. Each watcher logs every event to `run_log.md` and `Logs/events_<date>.jsonl`, and moves or clears its source after ingestion to prevent re-processing.

| Script | Source | Mode |
|--------|--------|------|
| `watcher_inbox.py` | `Inbox/` — any `.md` file dropped here | Live |
| `watcher_manual.py` | `manual_input.txt` — entries split by `---` | Live |
| `whatsapp_watcher.py` | `whatsapp_input.txt` — simulated WhatsApp DMs | Simulated |
| `linkedin_watcher.py` | `linkedin_input.txt` — simulated LinkedIn DMs | Simulated (bonus) |
| `gmail_watcher.py` | Gmail API — unread inbox, domain-filtered, deduplicated | OAuth (exits cleanly if credentials absent) |

---

## Agent (`agent.py`)

`agent.py` reads every file in `Needs_Action/` and runs three skill modules in sequence per task.

### Skill 1 — Planning (`skills/planning_skill.py`)
- Produces `Plans/<task>_Plan.md`: task analysis, step-by-step plan, risks, and a checklist.
- Calls OpenAI if `OPENAI_API_KEY` is set and quota is available.
- Falls back to a deterministic template if the key is missing or the API returns a quota/rate error (e.g. `429 insufficient_quota`). Fallback is logged as status `plan_fallback`.

### Skill 2 — Summarise (`skills/summarize_skill.py`)
- Produces `Pending_Approval/<task>.md`: original content + AI summary + model + status.
- Same OpenAI-or-fallback pattern. Fallback logged as status `fallback`.

### Skill 3 — LinkedIn Draft (`skills/linkedin_skill.py`)
- Runs only when the task is classified as a business or marketing task.
- Produces `Pending_Approval/linkedin_draft_<task>_<hash>.md` containing: generated post text, source task reference, task hash, and a risk note requiring human approval before posting.
- Same OpenAI-or-fallback pattern.

After all three skills run, the source file is moved from `Needs_Action/` to `Done/_source_<task>.md`.

### Fallback Behaviour
If `OPENAI_API_KEY` is absent **or** the API returns a quota error (HTTP 429 / `insufficient_quota`), all skills produce deterministic fallback output. The agent completes without crashing. Fallback usage is counted and written to `Logs/summary_<ts>.md` and `prompt_history.md`.

> In the cloud workflow `OPENAI_REQUIRED=true` is set — the agent exits with an error if the key is missing entirely in CI.

### Per-Run Logging
| File | What is logged |
|------|---------------|
| `run_log.md` | One UTC line per event (plan created, task processed, errors) |
| `prompt_history.md` | Timestamp, model, status (`openai_ok` / `plan_fallback` / `fallback`), filename, prompt snippet |
| `Logs/events_<date>.jsonl` | Structured JSONL — one object per event |
| `Logs/summary_<ts>.md` | Counts: tasks processed, plans created, LinkedIn drafts, OpenAI OK, fallbacks, errors |

---

## HITL — Human-in-the-Loop (`approve.py`)

`approve.py` is the **only** mechanism that moves files from `Pending_Approval/` to `Approved/`. It is never called automatically.

```bash
python approve.py                          # list all pending files
python approve.py linkedin_draft_foo.md    # approve a specific file
python approve.py --all                    # approve all pending files
```

LinkedIn drafts are tagged `[LINKEDIN]` in the list output. Each approval is logged to `run_log.md` and `Logs/events_<date>.jsonl`.

`post_approved.py` will **never** process files still in `Pending_Approval/`. It scans for unapproved `linkedin_draft_*` files and logs each one as `blocked_without_approval` — auditable proof that the HITL gate was enforced.

---

## LinkedIn Posting (`post_approved.py`)

`post_approved.py` scans `Approved/` for `linkedin_draft_*.md` files only.

**Simulated mode (default — no credentials required):**
- Writes evidence JSON to `Logs/linkedin_simulated_<ts>.json`.
- File stays in `Approved/` (not moved to `Done/`).

**Real posting mode:**
- Requires `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_PERSON_URN` + `LINKEDIN_SIMULATED=false`.
- Calls the LinkedIn UGC Post API.
- On success: moves file to `Done/` and records task hash in `Logs/posted_ids.json`.

**Idempotency:** `Logs/posted_ids.json` tracks SHA1 hashes of all posted tasks. Re-running `post_approved.py` skips already-posted items — no double-posting.

LinkedIn will **never** post publicly unless all three conditions are explicitly met.

---

## MCP Tool Layer

| Module | Responsibility |
|--------|---------------|
| `mcp_file_ops.py` | Safe file helpers: list, read, write, move, copy, log_event |
| `mcp_linkedin_ops.py` | LinkedIn UGC Post API + simulated mode + evidence JSON |
| `mcp_email_ops.py` | SMTP email sending + simulated mode (bonus) |
| `mcp_calendar_ops.py` | Local simulated calendar event store (bonus) |
| `mcp_server.py` | Original MCP server entry point (backward compatibility) |

All MCP tools degrade gracefully when credentials are absent — they write evidence files and return structured results rather than raising exceptions.

---

## Simulated vs Real Modes

| Feature | Default | Condition for real mode | Evidence when simulated |
|---------|---------|------------------------|------------------------|
| LinkedIn posting | Simulated | `LINKEDIN_SIMULATED=false` + token + URN | `Logs/linkedin_simulated_*.json` |
| Email sending | Simulated | `SMTP_HOST` + `SMTP_USER` + `SMTP_PASS` | `Logs/email_simulated_*.json` |
| OpenAI plans | Fallback if no key / quota exceeded | `OPENAI_API_KEY` set and quota available | `plan_fallback` / `fallback` in Plans/ and prompt_history.md |
| Gmail ingestion | Disabled in cloud unless enabled | `GMAIL_OAUTH_ENABLED=true` + credentials | clean exit logged to run_log.md |
| WhatsApp ingestion | Always simulated | n/a — reads local file | `whatsapp_input.txt` cleared after ingestion |
| LinkedIn ingestion | Always simulated | n/a — reads local file | `linkedin_input.txt` cleared after ingestion |
| Calendar ops | Always simulated | n/a | `Logs/calendar_events.json` |

---

## GitHub Actions Cloud Automation

**File:** `.github/workflows/silver-agent.yml`

**Triggers:**
- Scheduled every 10 minutes (`cron: "*/10 * * * *"`)
- Manual dispatch via `workflow_dispatch`
- No push trigger (avoids recursive commit loops)

**Step order per run:**
1. Watcher 1 — `Inbox/` → `Needs_Action/`
2. Watcher 2 — `manual_input.txt` → `Needs_Action/`
3. Watcher 3 — `whatsapp_input.txt` → `Needs_Action/` (simulated)
4. Watcher 4 — `linkedin_input.txt` → `Needs_Action/` (simulated)
5. Gmail OAuth file setup — only if `GMAIL_OAUTH_ENABLED=true`
6. Watcher 5 — Gmail → `Inbox/` — only if `GMAIL_OAUTH_ENABLED=true`
7. Agent — reads `Needs_Action/`, generates `Plans/` and `Pending_Approval/`
8. Post — HITL check + LinkedIn posting from `Approved/` → `Done/`
9. Commit and push (`git pull --rebase` before push; only relevant dirs staged)
10. Print run summary
11. Upload evidence artifact (30-day retention)

**Committed directories per run:** `Needs_Action/`, `Pending_Approval/`, `Approved/`, `Done/`, `Plans/`, `Logs/`, `run_log.md`, `prompt_history.md`.

---

## Secrets Setup

Add these as **GitHub Repository Secrets** (Settings → Secrets → Actions):

| Secret | Required | Description |
|--------|----------|-------------|
| `OPENAI_API_KEY` | Yes (cloud) | OpenAI API key — required in cloud workflow (`OPENAI_REQUIRED=true`) |
| `OPENAI_MODEL` | Optional | Model name; default `gpt-4o-mini` |
| `LINKEDIN_ACCESS_TOKEN` | Optional | LinkedIn OAuth token for live posting |
| `LINKEDIN_PERSON_URN` | Optional | e.g. `urn:li:person:AbCdEfGh` |
| `LINKEDIN_SIMULATED` | Optional | `false` = enable real posting; default `true` |
| `GMAIL_OAUTH_ENABLED` | Optional | `true` = run Gmail watcher in cloud; default `false` |
| `GMAIL_CLIENT_SECRET_JSON` | Optional | Full contents of `credentials.json` (Gmail only) |
| `GMAIL_TOKEN_JSON` | Optional | Full contents of `token.json` (Gmail only) |

For local development: `cp .env.example .env` and fill in values. `.env` is gitignored — never commit it.

---

## Gmail Domain Allowlist

`gmail_watcher.py` only ingests emails from senders in these domains (subdomains included):

- `google.com`
- `github.com`
- `microsoft.com`
- `azure.com`
- `anthropic.com`

Emails from all other domains are silently skipped. Deduplication is by Gmail message ID — the same email is never written twice. To add domains, edit `ALLOWED_DOMAINS` in `gmail_watcher.py`.

---

## Judge Quick Demo (2–3 minutes)

Everything below works without any credentials — simulated mode only.

```bash
# 0. Install dependencies (once)
pip install -r requirements.txt

# 1. Drop a business task into Inbox
echo "Launch a LinkedIn campaign for our new AI product targeting enterprise." > Inbox/demo.md

# 2. Run Watcher 1 — Inbox → Needs_Action
python watcher_inbox.py
ls Needs_Action/   # demo.md should appear

# 3. Run the agent — generates Plan + summary + LinkedIn draft
python agent.py
ls Plans/            # demo_Plan.md
ls Pending_Approval/ # demo.md  +  linkedin_draft_demo_<hash>.md
cat prompt_history.md  # shows model, status (openai_ok or plan_fallback), snippet

# 4. Show HITL hard block — post_approved refuses unapproved drafts
python post_approved.py
# Output: [BLOCKED] linkedin_draft_demo_*.md — requires human approval first.
cat run_log.md   # look for "blocked_without_approval"

# 5. Human approval — Pending_Approval → Approved
python approve.py        # lists pending files with [LINKEDIN] tag
python approve.py --all  # approve all
ls Approved/             # linkedin_draft_demo_*.md now here

# 6. Post (simulated — no credentials needed)
python post_approved.py
# Output: "Not posted (simulated_mode). File kept in Approved/."
ls Logs/                 # linkedin_simulated_*.json written as evidence

# 7. Review audit trail
cat run_log.md
cat prompt_history.md
cat Logs/events_$(date +%Y-%m-%d).jsonl
cat Logs/summary_*.md

# 8. Generate evidence pack for judges
python evidence_pack.py
# Creates evidence_<timestamp>.zip — share this file
```

---

## Evidence Paths

| Evidence | Path |
|----------|------|
| UTC audit log | `run_log.md` |
| Prompt audit trail | `prompt_history.md` |
| Structured JSONL events | `Logs/events_<YYYY-MM-DD>.jsonl` |
| Per-run stats (fallback count, tasks processed) | `Logs/summary_<timestamp>.md` |
| LinkedIn simulated posts | `Logs/linkedin_simulated_<timestamp>.json` |
| Idempotency registry | `Logs/posted_ids.json` |
| Reasoning plans | `Plans/<taskname>_Plan.md` |
| LinkedIn drafts (pending) | `Pending_Approval/linkedin_draft_*.md` |
| Approved items | `Approved/` |
| Completed tasks | `Done/` |
| Evidence ZIP | `evidence_<timestamp>.zip` |
| GitHub Actions artifacts | Actions tab → run → Artifacts (30-day retention) |

---

## Silver Tier Compliance Checklist

| ID | Requirement | Implementation | Status |
|----|-------------|----------------|--------|
| A1 | Watcher: Inbox → Needs_Action | `watcher_inbox.py` | ✅ |
| A2 | Watcher: manual_input.txt → Needs_Action | `watcher_manual.py` | ✅ |
| A3 | Watcher: simulated channel | `whatsapp_watcher.py` | ✅ |
| A4 | Watcher: Gmail API, domain filter, dedup | `gmail_watcher.py` | ✅ |
| A5 | 5th watcher: LinkedIn simulated ingestion | `linkedin_watcher.py` | ✅ BONUS |
| B | `Plans/<task>_Plan.md` per task | `skills/planning_skill.py` → `Plans/` | ✅ |
| B | OpenAI integration + deterministic fallback (missing key or 429) | `skills/*.py` each wrap `_call_openai` with fallback | ✅ |
| B | `prompt_history.md` (timestamp, model, status, file, snippet) | `agent.py:_log_prompt_history()` | ✅ |
| C1 | MCP file ops module | `mcp_file_ops.py` | ✅ |
| C2 | MCP LinkedIn ops (live + simulated + evidence) | `mcp_linkedin_ops.py` | ✅ |
| C3 | MCP email ops (SMTP + simulated) | `mcp_email_ops.py` | ✅ BONUS |
| C4 | MCP calendar ops (simulated) | `mcp_calendar_ops.py` | ✅ BONUS |
| D | LinkedIn draft for business tasks in Pending_Approval | `agent.py` + `skills/linkedin_skill.py` | ✅ |
| D | Draft format: title, source, post text, status, risk note, hash | `agent.py:li_draft_md` | ✅ |
| D | `post_approved.py` posts only from `Approved/` | `post_approved.py` | ✅ |
| D | Idempotency: `Logs/posted_ids.json` prevents double-posting | `post_approved.py` | ✅ BONUS |
| D | HITL hard block log (`blocked_without_approval`) | `post_approved.py:_check_and_log_pending_blocks()` | ✅ BONUS |
| E | `approve.py`: Pending_Approval → Approved (manual only) | `approve.py` | ✅ |
| E | `approve.py` list / single / `--all` | `approve.py` | ✅ |
| F | GitHub Actions: every 10 min + `workflow_dispatch` | `.github/workflows/silver-agent.yml` | ✅ |
| F | Workflow order: watchers → agent → post → commit | `silver-agent.yml` | ✅ |
| F | Gmail guard: step conditional on `GMAIL_OAUTH_ENABLED` | `silver-agent.yml` | ✅ |
| F | Safe push: `git pull --rebase` before push | `silver-agent.yml` | ✅ |
| F | Artifact upload per run (30-day retention) | `silver-agent.yml` upload-artifact step | ✅ BONUS |
| G | README: diagram, checklist, demo steps, secrets setup | `README.md` | ✅ |
| G | `JUDGE_PROOF.md` compliance mapping | `JUDGE_PROOF.md` | ✅ |
| H | `.gitignore`: `.env`, `credentials.json`, `token.json`, `__pycache__` | `.gitignore` | ✅ |
| H | `.env.example` with all keys | `.env.example` | ✅ |
| I1 | Structured event logging: `Logs/events_<date>.jsonl` | All modules | ✅ BONUS |
| I2 | `evidence_pack.py`: ZIP for judges | `evidence_pack.py` | ✅ BONUS |
| I3 | Gmail domain allowlist | `gmail_watcher.py:ALLOWED_DOMAINS` | ✅ BONUS |
| I4 | Stats summary with fallback counts: `Logs/summary_<ts>.md` | `agent.py` | ✅ BONUS |
| I5 | Modular skill package (`skills/`) | `planning_skill.py`, `summarize_skill.py`, `linkedin_skill.py` | ✅ BONUS |

---

## Status

- Silver Tier — Fully Implemented + All Bonus Items
- End-to-End Pipeline — Verified locally and via GitHub Actions
- MCP Tool Layer — 4 modules (file, linkedin, email, calendar)
- Human-in-the-Loop — Enforced (`approve.py` required; never bypassed in code)
- LinkedIn HITL + Idempotency — Active
- Cloud Automation — GitHub Actions (5 watchers + agent + poster, every 10 min)
- Simulated Mode — All features functional without any credentials
- Fallback Mode — All OpenAI skills degrade gracefully on missing key or quota error
- Evidence Pack — `python evidence_pack.py`
