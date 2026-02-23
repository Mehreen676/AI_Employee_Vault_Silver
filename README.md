![Silver Agent](https://img.shields.io/badge/Silver%20Agent-Cloud%20Automated-brightgreen)
![HITL](https://img.shields.io/badge/HITL-Enabled-blue)
![MCP](https://img.shields.io/badge/MCP-Integrated-orange)
![Obsidian](https://img.shields.io/badge/Obsidian-Compatible-purple)

# AI Employee Vault — Silver Tier (Hackathon 0)

A **Personal AI Employee** system for Hackathon 0 Silver Tier.
Multi-channel task ingestion → OpenAI-powered reasoning plans → LinkedIn HITL approval → cloud automation via GitHub Actions.

> **Obsidian note:** This repository can be opened as an Obsidian vault (`Dashboard.md`, `Company_Handbook.md`, `Welcome.md` are vault documents). The automation pipeline — watchers, agent, approve, post — runs entirely via Python scripts and GitHub Actions and **does not require Obsidian** to be installed or running.

---

## System Architecture

```
 ┌────────────────────────────────────────────────────────────────────┐
 │                   INGESTION LAYER  (5 watchers)                     │
 │                                                                     │
 │  Inbox/  manual_input.txt  whatsapp_input.txt  linkedin_input.txt  │
 │    │           │                  │                   │             │
 │ [watcher_  [watcher_      [whatsapp_         [linkedin_            │
 │  inbox]    manual]         watcher]           watcher]             │
 │      \        \               /                  /                 │
 │       ╰────────╴─────────────╴──────────────────╯                  │
 │                              │                                     │
 │        Gmail API ──────► [gmail_watcher] ──► Inbox/               │
 │        (when GMAIL_OAUTH_ENABLED=true + credentials present)       │
 │                              │                                     │
 │                        Needs_Action/                               │
 └──────────────────────────────┼─────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼─────────────────────────────────────┐
 │                     AGENT LAYER  (agent.py)                         │
 │                                                                     │
 │  skills/planning_skill.py   →  Plans/<task>_Plan.md                │
 │  skills/summarize_skill.py  →  Pending_Approval/<task>.md          │
 │  skills/linkedin_skill.py   →  Pending_Approval/linkedin_draft_*   │
 │                                (business tasks only)                │
 │                                                                     │
 │  MCP tools:                                                         │
 │    mcp_file_ops.py      list / read / write / move                 │
 │    mcp_linkedin_ops.py  LinkedIn UGC Post API + simulated          │
 │    mcp_email_ops.py     SMTP email + simulated        (bonus)      │
 │    mcp_calendar_ops.py  calendar events, simulated    (bonus)      │
 └──────────────────────────────┼─────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼─────────────────────────────────────┐
 │                  HITL LAYER  (Human-in-the-Loop)                    │
 │                                                                     │
 │  Pending_Approval/                                                  │
 │       │                                                             │
 │  [approve.py]  ← MANUAL ONLY — human must invoke this              │
 │       │                                                             │
 │  Approved/                                                          │
 │       │                                                             │
 │  [post_approved.py]  ← reads ONLY from Approved/                   │
 │    ├── LinkedIn UGC Post API  (or writes simulated evidence)        │
 │    └── on success → moves file to Done/                             │
 └──────────────────────────────┼─────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼─────────────────────────────────────┐
 │                       EVIDENCE LAYER                                │
 │                                                                     │
 │  run_log.md                   human-readable UTC audit log          │
 │  prompt_history.md            full prompt audit trail               │
 │  Logs/events_<date>.jsonl     structured JSONL event stream         │
 │  Logs/summary_<ts>.md         per-run stats (fallback counts etc.)  │
 │  Logs/linkedin_simulated_*.json  simulated post evidence            │
 │  Logs/posted_ids.json         idempotency hash registry             │
 └────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
AI_Employee_Vault_Silver/
│
├── Inbox/                       # Raw file drops — watcher_inbox picks these up
├── Needs_Action/                # Tasks queued for agent processing
├── Pending_Approval/            # Agent output awaiting human approval
├── Approved/                    # Human-approved items (ready to post)
├── Done/                        # Completed tasks and moved source files
├── Plans/                       # <task>_Plan.md reasoning plans
├── Logs/                        # JSONL events, summaries, evidence files
├── prompts/                     # Timestamped Claude run prompt logs
├── skills/                      # Skill modules called by agent.py
│   ├── planning_skill.py        #   structured plan generation
│   ├── summarize_skill.py       #   task summarisation
│   └── linkedin_skill.py        #   LinkedIn post draft creation
├── specs/                       # Requirement / spec documents
│
├── .github/workflows/
│   └── silver-agent.yml         # GitHub Actions: every 10 min + workflow_dispatch
│
│── Obsidian vault documents ─────────────────────────────────────────
├── Dashboard.md                 # AI Employee dashboard (Obsidian view)
├── Company_Handbook.md          # Company reference document
├── Welcome.md                   # Vault welcome note
│── Pipeline scripts ─────────────────────────────────────────────────
├── watcher_inbox.py             # Watcher 1: Inbox/ → Needs_Action/
├── watcher_manual.py            # Watcher 2: manual_input.txt → Needs_Action/
├── whatsapp_watcher.py          # Watcher 3: whatsapp_input.txt (simulated)
├── linkedin_watcher.py          # Watcher 4: linkedin_input.txt (simulated, bonus)
├── gmail_watcher.py             # Watcher 5: Gmail API (exits cleanly if credentials absent)
│
├── agent.py                     # Core agent: plans + summaries + LinkedIn drafts
├── approve.py                   # HITL: Pending_Approval → Approved (manual only)
├── post_approved.py             # LinkedIn poster: Approved → Done
│── MCP tools ────────────────────────────────────────────────────────
├── mcp_file_ops.py              # Safe file helpers (list/read/write/move/log)
├── mcp_linkedin_ops.py          # LinkedIn UGC Post API + simulated mode
├── mcp_email_ops.py             # SMTP email + simulated mode  (bonus)
├── mcp_calendar_ops.py          # Calendar events, simulated  (bonus)
├── mcp_server.py                # Original MCP server (backward compatibility)
│── Utilities ────────────────────────────────────────────────────────
├── send_test_email.py           # CLI helper: verify MCP email integration  (bonus)
├── processor.py                 # Task processor helper
├── watcher.py                   # Base watcher helper
├── agent_queue.py               # Queue-based agent variant
├── evidence_pack.py             # Generates evidence ZIP for judges
│── Docs & audit ─────────────────────────────────────────────────────
├── JUDGE_PROOF.md               # Detailed compliance evidence guide
├── run_log.md                   # Human-readable UTC audit log
├── prompt_history.md            # Full prompt audit trail
│── Input files ──────────────────────────────────────────────────────
├── manual_input.txt             # Drop manual tasks here (separator: ---)
├── whatsapp_input.txt           # Simulated WhatsApp DM input
├── linkedin_input.txt           # Simulated LinkedIn DM input
│── Config ───────────────────────────────────────────────────────────
├── .env.example                 # Template for all environment variables
├── requirements.txt
└── .gitignore                   # Excludes .env, credentials.json, token.json, __pycache__
```

---

## Watchers

Five watchers ingest tasks from different sources into `Needs_Action/`. Each watcher deduplicates and logs every event to `run_log.md` and `Logs/events_<date>.jsonl`.

| # | Script | Source | Mode |
|---|--------|--------|------|
| 1 | `watcher_inbox.py` | `Inbox/` — any `.md` file dropped here | Live |
| 2 | `watcher_manual.py` | `manual_input.txt` — entries separated by `---` | Live |
| 3 | `whatsapp_watcher.py` | `whatsapp_input.txt` — simulated WhatsApp DMs | Simulated |
| 4 | `linkedin_watcher.py` | `linkedin_input.txt` — simulated LinkedIn DMs | Simulated (bonus) |
| 5 | `gmail_watcher.py` | Gmail API — unread inbox, domain-filtered, dedup by message ID | OAuth-guarded |

### Gmail Watcher Notes

- **Cloud:** The Gmail step in `silver-agent.yml` only runs when `GMAIL_OAUTH_ENABLED=true` is set **and** the `GMAIL_CLIENT_SECRET_JSON` / `GMAIL_TOKEN_JSON` secrets are present.
- **Local:** If the Google API libraries are not installed (`pip install -r requirements.txt` not yet run), the script prints `"Gmail libraries missing."` and exits cleanly with code 1. This is a dependency issue, not a system failure — install requirements and it works.
- **Domain allowlist:** Only emails from allowed domains are ingested (see [Gmail Domain Allowlist](#gmail-domain-allowlist)).
- **Deduplication:** Each email is identified by its Gmail message ID. Re-running the watcher never writes the same email twice.

---

## Agent (`agent.py`)

`agent.py` reads every `.md` file in `Needs_Action/` and routes each through three skill modules in sequence.

### Skill 1 — Planning (`skills/planning_skill.py`)
- Produces `Plans/<task>_Plan.md` with: task analysis, step-by-step plan, risks, and a completion checklist.
- Calls OpenAI (`gpt-4o-mini` by default) if `OPENAI_API_KEY` is set and quota is available.
- **Fallback:** If the key is absent or the API returns any error (including `429 insufficient_quota`), a deterministic structured plan is generated and the status is recorded as `plan_fallback`. The agent does not crash.

### Skill 2 — Summarise (`skills/summarize_skill.py`)
- Produces `Pending_Approval/<task>.md` with: original content, AI summary, model name, and status.
- Same OpenAI-or-fallback pattern. Fallback status: `fallback`.

### Skill 3 — LinkedIn Draft (`skills/linkedin_skill.py`)
- Runs only when the task text is classified as a business or marketing task.
- Produces `Pending_Approval/linkedin_draft_<task>_<hash>.md` containing: generated post text, source task reference, SHA1 task hash, and a risk note requiring human approval before posting.
- Same OpenAI-or-fallback pattern.

After all skills run, the source file is moved from `Needs_Action/` to `Done/_source_<task>.md`.

### OpenAI Fallback Behaviour

| Condition | Behaviour | Logged status |
|-----------|-----------|---------------|
| `OPENAI_API_KEY` set, quota available | OpenAI call succeeds | `openai_ok` |
| `OPENAI_API_KEY` missing | Deterministic fallback used immediately | `plan_fallback` / `fallback` |
| API returns `429 insufficient_quota` or any HTTP error | Deterministic fallback used, error caught | `plan_fallback` / `fallback` |

Fallback counts are reported in `Logs/summary_<ts>.md` and every prompt attempt is recorded in `prompt_history.md` (timestamp, model, status, file, prompt snippet — no secrets logged).

> **Cloud note:** `OPENAI_REQUIRED=true` is set in the GitHub Actions workflow env. This causes the agent to exit with an error if `OPENAI_API_KEY` is entirely absent in CI, ensuring cloud runs always use the real API.

### Per-Run Logging

| File | Contents |
|------|---------|
| `run_log.md` | One UTC line per event (plan created, task processed, errors) |
| `prompt_history.md` | Timestamp, model, status, filename, prompt snippet |
| `Logs/events_<date>.jsonl` | Structured JSONL — one object per event |
| `Logs/summary_<ts>.md` | Counts: tasks, plans, drafts, OpenAI OK, fallbacks, errors |

---

## HITL — Human-in-the-Loop (`approve.py`)

`approve.py` is the **only** mechanism that promotes files from `Pending_Approval/` to `Approved/`. It is never called automatically — not by the agent, not by the GitHub Actions workflow.

```bash
python approve.py                          # list all pending files
python approve.py linkedin_draft_foo.md    # approve one specific file
python approve.py --all                    # approve all pending files
```

LinkedIn drafts are tagged `[LINKEDIN]` in the list view. Every approval is logged to `run_log.md` and `Logs/events_<date>.jsonl`.

`post_approved.py` enforces the HITL gate at runtime: before processing `Approved/`, it scans `Pending_Approval/` for any unapproved `linkedin_draft_*` files and logs each one as `blocked_without_approval`. This produces auditable evidence that no draft was ever posted without human sign-off.

---

## LinkedIn Posting (`post_approved.py`)

`post_approved.py` reads only from `Approved/`. Files in `Pending_Approval/` are never touched by this script.

### Simulated Mode (default — no credentials needed)

- Evidence JSON written to `Logs/linkedin_simulated_<ts>.json`.
- File stays in `Approved/` (not moved to `Done/`).
- Safe to run in any environment — no public posts are made.

### Real Posting Mode

- Requires all three: `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_PERSON_URN` + `LINKEDIN_SIMULATED=false`.
- Calls the LinkedIn UGC Post API via `mcp_linkedin_ops.create_post()`.
- On success: file moves to `Done/`, task hash saved to `Logs/posted_ids.json`.

### Idempotency

`Logs/posted_ids.json` stores the SHA1 hash of every successfully posted task. Re-running `post_approved.py` checks this registry and skips already-posted items — no double-posting, even across workflow runs.

---

## MCP Tool Layer

| Module | Responsibility |
|--------|---------------|
| `mcp_file_ops.py` | list, read, write, move, copy files; `log_event()` helper |
| `mcp_linkedin_ops.py` | LinkedIn UGC Post API calls; simulated mode; evidence JSON |
| `mcp_email_ops.py` | SMTP email sending; simulated mode; evidence JSON (bonus) |
| `mcp_calendar_ops.py` | Local simulated calendar event store (bonus) |
| `mcp_server.py` | Original MCP server entry point (backward compatibility) |

All MCP tools return structured results and write evidence files when credentials are absent — they never raise unhandled exceptions.

---

## Bonus MCP Modules

Two additional MCP modules extend the core pipeline beyond the LinkedIn requirement. Both follow the same design contract as `mcp_linkedin_ops.py`: structured return values, full audit logging, and safe degradation when credentials are absent.

### Email MCP (`mcp_email_ops.py`)

Exposes a single `send_email(to, subject, body)` function callable from any part of the pipeline.

**Simulated mode (default):**
- Triggered when any of `SMTP_HOST`, `SMTP_USER`, or `SMTP_PASS` is absent.
- Writes `Logs/email_simulated_<ts>.json` containing recipient, subject, body, and the list of missing credentials.
- Returns `{"ok": False, "reason": "not_configured", "evidence_path": "..."}`.

**Real SMTP mode:**
- Activated when all three credentials are set (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`).
- Connects via STARTTLS on port 587 (configurable via `SMTP_PORT`).
- `SMTP_FROM` is optional; falls back to `SMTP_USER` if not set.
- Passwords are never logged — only the sender address and recipient appear in audit records.
- Returns `{"ok": True}` on success; catches and logs SMTP exceptions without crashing.

A companion script `send_test_email.py` provides a CLI to verify the integration end-to-end before using it in production.

### Calendar MCP (`mcp_calendar_ops.py`)

Exposes `create_event(title, start, end, description)` and `read_events()` backed by a local JSON store at `Logs/calendar_events.json`.

- Operates entirely in **simulated mode** — no external API required.
- Each event is persisted with a timestamp-based `id`, `created_at` UTC timestamp, and `"mode": "simulated"` field.
- `read_events()` returns the full event list with a count — usable by any downstream skill or agent step.
- Every write and read is logged to `run_log.md` and `Logs/events_<date>.jsonl`.

### Why these strengthen the submission

| Criterion | Contribution |
|-----------|-------------|
| MCP tool breadth | Demonstrates the MCP abstraction pattern across three distinct action types (file, communication, scheduling) beyond the minimum LinkedIn requirement |
| Safe-by-default | Both modules write evidence files rather than failing silently — judges can verify every invocation without live credentials |
| Audit completeness | All email and calendar events appear in the same JSONL stream as the rest of the pipeline, giving a single queryable audit trail for the full run |
| Real-mode upgrade path | Email switches to live SMTP with three env vars; calendar is structured for a Google Calendar API drop-in — no code changes needed in callers |

---

## Simulated vs Real Modes

| Feature | Default | Condition for real mode | Evidence when simulated |
|---------|---------|------------------------|------------------------|
| LinkedIn posting | Simulated | `LINKEDIN_SIMULATED=false` + `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_PERSON_URN` | `Logs/linkedin_simulated_<ts>.json` |
| Email sending | Simulated | `SMTP_HOST` + `SMTP_USER` + `SMTP_PASS` set | `Logs/email_simulated_<ts>.json` |
| OpenAI plans | Fallback if key missing or quota exceeded | `OPENAI_API_KEY` valid and within quota | `plan_fallback` / `fallback` status in `Plans/` and `prompt_history.md` |
| Gmail ingestion | Disabled unless enabled | `GMAIL_OAUTH_ENABLED=true` + credentials | Clean exit logged to `run_log.md` |
| WhatsApp ingestion | Always simulated | n/a — reads local text file | `whatsapp_input.txt` cleared after ingestion |
| LinkedIn ingestion | Always simulated | n/a — reads local text file | `linkedin_input.txt` cleared after ingestion |
| Calendar ops | Always simulated | n/a | `Logs/calendar_events.json` |

---

## GitHub Actions Cloud Automation

**File:** `.github/workflows/silver-agent.yml`

**Triggers:**
- Scheduled every 10 minutes — `cron: "*/10 * * * *"`
- Manual — `workflow_dispatch`
- No push trigger (prevents recursive commit loops)

**Concurrency:** `cancel-in-progress: true` — a new scheduled run cancels any still-running previous run.

**Step order:**

| Step | Action |
|------|--------|
| 1 | Watcher 1 — `Inbox/` → `Needs_Action/` |
| 2 | Watcher 2 — `manual_input.txt` → `Needs_Action/` |
| 3 | Watcher 3 — `whatsapp_input.txt` → `Needs_Action/` |
| 4 | Watcher 4 — `linkedin_input.txt` → `Needs_Action/` |
| 5 | Gmail OAuth setup — only if `GMAIL_OAUTH_ENABLED=true` |
| 6 | Watcher 5 — Gmail → `Inbox/` — only if `GMAIL_OAUTH_ENABLED=true` |
| 7 | Agent — reads `Needs_Action/`, writes `Plans/` and `Pending_Approval/` |
| 8 | Post — HITL block check + LinkedIn posting from `Approved/` → `Done/` |
| 9 | Commit and push — `git pull --rebase` before push |
| 10 | Print summary — task counts, plan counts, error counts |
| 11 | Upload artifact — `run_log.md`, `Plans/`, `Logs/`, `Done/` etc. (30-day retention) |

**Committed paths per run:** `Needs_Action/`, `Pending_Approval/`, `Approved/`, `Done/`, `Plans/`, `Logs/`, `run_log.md`, `prompt_history.md`.

---

## Obsidian Vault Compatibility

This repository is structured to be openable as an **Obsidian vault**. The following markdown files serve as vault documents for human navigation:

| File | Purpose |
|------|---------|
| `Dashboard.md` | Live AI Employee dashboard |
| `Company_Handbook.md` | Company reference document |
| `Welcome.md` | Vault welcome and orientation note |

**The automation pipeline does not depend on Obsidian.** All watchers, the agent, approve, and post scripts are standard Python. The GitHub Actions workflow runs on `ubuntu-latest` with no Obsidian dependency. Opening the vault in Obsidian is optional and purely for human readability.

---

## Secrets Setup

Add these as **GitHub Repository Secrets** (Settings → Secrets → Actions):

| Secret | Required | Description |
|--------|----------|-------------|
| `OPENAI_API_KEY` | Yes (cloud) | OpenAI key — workflow sets `OPENAI_REQUIRED=true` |
| `OPENAI_MODEL` | Optional | Model name; default `gpt-4o-mini` |
| `LINKEDIN_ACCESS_TOKEN` | Optional | LinkedIn OAuth token for live posting |
| `LINKEDIN_PERSON_URN` | Optional | e.g. `urn:li:person:AbCdEfGh` |
| `LINKEDIN_SIMULATED` | Optional | `false` = enable real posting; default `true` |
| `GMAIL_OAUTH_ENABLED` | Optional | `true` = run Gmail watcher step in cloud; default `false` |
| `GMAIL_CLIENT_SECRET_JSON` | Optional | Full JSON contents of `credentials.json` |
| `GMAIL_TOKEN_JSON` | Optional | Full JSON contents of `token.json` |

**Local development:** `cp .env.example .env` — fill in values. `.env` is gitignored; never commit it.

---

## Gmail Domain Allowlist

`gmail_watcher.py` only ingests emails from senders whose domain matches this allowlist (exact match or subdomain):

- `google.com`
- `github.com`
- `microsoft.com`
- `azure.com`
- `anthropic.com`

All other senders are silently skipped. To add domains, edit `ALLOWED_DOMAINS` in `gmail_watcher.py`. Deduplication is by Gmail message ID — the same email is never written twice across runs.

---

## Judge Quick Demo (2–3 minutes)

All steps work in **simulated mode** — no credentials required.

```bash
# 0. Install dependencies (once)
pip install -r requirements.txt

# 1. Drop a business task into Inbox/
echo "Launch a LinkedIn campaign for our new AI product targeting enterprise." > Inbox/demo.md

# 2. Watcher 1 — moves Inbox/ → Needs_Action/
python watcher_inbox.py
ls Needs_Action/          # demo.md appears here

# 3. Agent — generates Plan + summary + LinkedIn draft
python agent.py
ls Plans/                 # demo_Plan.md
ls Pending_Approval/      # demo.md  AND  linkedin_draft_demo_<hash>.md
cat prompt_history.md     # shows model, status (openai_ok or plan_fallback), snippet

# 4. HITL hard block — post_approved refuses unapproved drafts
python post_approved.py
# Output: [BLOCKED] linkedin_draft_demo_*.md — requires human approval first.
grep "blocked_without_approval" run_log.md   # auditable evidence

# 5. Human approval — Pending_Approval/ → Approved/
python approve.py           # list files; linkedin_draft shown with [LINKEDIN] tag
python approve.py --all     # approve all
ls Approved/                # linkedin_draft_demo_*.md now here

# 6. Post (simulated — no LinkedIn credentials needed)
python post_approved.py
# Output: "Not posted (simulated_mode). File kept in Approved/."
ls Logs/                    # linkedin_simulated_*.json written as evidence

# 7. Review audit trail
cat run_log.md
cat prompt_history.md
cat "Logs/events_$(date +%Y-%m-%d).jsonl"
cat Logs/summary_*.md

# 8. Generate evidence ZIP for judges
python evidence_pack.py
# Creates: evidence_<timestamp>.zip
```

---

## Evidence Paths

| Evidence | Path |
|----------|------|
| UTC audit log | `run_log.md` |
| Prompt audit trail (model, status, snippet) | `prompt_history.md` |
| Structured JSONL events | `Logs/events_<YYYY-MM-DD>.jsonl` |
| Per-run stats (tasks, plans, fallback count) | `Logs/summary_<timestamp>.md` |
| LinkedIn simulated post records | `Logs/linkedin_simulated_<timestamp>.json` |
| Idempotency registry | `Logs/posted_ids.json` |
| Reasoning plans | `Plans/<taskname>_Plan.md` |
| LinkedIn drafts awaiting approval | `Pending_Approval/linkedin_draft_*.md` |
| Approved items | `Approved/` |
| Completed tasks | `Done/` |
| Evidence ZIP | `evidence_<timestamp>.zip` |
| GitHub Actions artifacts | Actions tab → run number → Artifacts (30-day retention) |

---

## Silver Tier Compliance Checklist

| ID | Requirement | Implementation | Status |
|----|-------------|----------------|--------|
| A1 | Watcher: Inbox → Needs_Action | `watcher_inbox.py` | ✅ |
| A2 | Watcher: manual_input.txt → Needs_Action | `watcher_manual.py` | ✅ |
| A3 | Watcher: simulated channel | `whatsapp_watcher.py` | ✅ |
| A4 | Watcher: Gmail API, domain filter, dedup | `gmail_watcher.py` | ✅ |
| A5 | 5th watcher: LinkedIn simulated | `linkedin_watcher.py` | ✅ BONUS |
| B | `Plans/<task>_Plan.md` per task | `skills/planning_skill.py` → `Plans/` | ✅ |
| B | OpenAI + deterministic fallback (missing key or 429) | `skills/*.py` — each wraps `_call_openai` with fallback | ✅ |
| B | `prompt_history.md` (timestamp, model, status, file, snippet) | `agent.py:_log_prompt_history()` | ✅ |
| C1 | MCP file ops | `mcp_file_ops.py` | ✅ |
| C2 | MCP LinkedIn ops (live + simulated + evidence) | `mcp_linkedin_ops.py` | ✅ |
| C3 | MCP email ops (SMTP + simulated) | `mcp_email_ops.py` | ✅ BONUS |
| C4 | MCP calendar ops (simulated) | `mcp_calendar_ops.py` | ✅ BONUS |
| D | LinkedIn draft for business tasks | `agent.py` + `skills/linkedin_skill.py` | ✅ |
| D | Draft format: title, source, post, status, risk note, hash | `agent.py:li_draft_md` | ✅ |
| D | `post_approved.py` posts only from `Approved/` | `post_approved.py` | ✅ |
| D | Idempotency via `Logs/posted_ids.json` | `post_approved.py` | ✅ BONUS |
| D | HITL hard block (`blocked_without_approval` logged) | `post_approved.py:_check_and_log_pending_blocks()` | ✅ BONUS |
| E | `approve.py`: manual move Pending_Approval → Approved | `approve.py` | ✅ |
| E | `approve.py` list / single file / `--all` | `approve.py` | ✅ |
| F | GitHub Actions: every 10 min + `workflow_dispatch` | `.github/workflows/silver-agent.yml` | ✅ |
| F | Workflow order: watchers → agent → post → commit | `silver-agent.yml` | ✅ |
| F | Gmail guard: step conditional on `GMAIL_OAUTH_ENABLED` | `silver-agent.yml` | ✅ |
| F | Safe push: `git pull --rebase` before push | `silver-agent.yml` | ✅ |
| F | Artifact upload per run (30-day retention) | `silver-agent.yml` upload-artifact step | ✅ BONUS |
| G | README: diagram, checklist, demo steps, secrets | `README.md` | ✅ |
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

- **Silver Tier** — Fully implemented including all bonus items
- **Pipeline** — End-to-end verified locally and via GitHub Actions
- **MCP Layer** — 4 modules: file, LinkedIn, email, calendar
- **HITL** — Architecturally enforced; `approve.py` required; never bypassed
- **LinkedIn** — Idempotency active; simulated by default; real posting opt-in
- **Cloud** — GitHub Actions every 10 min; artifact upload per run
- **Simulated mode** — Full pipeline runs without any credentials
- **Fallback mode** — All OpenAI skills degrade gracefully on missing key or quota error
- **Obsidian** — Vault-compatible; automation independent of Obsidian
- **Evidence** — `python evidence_pack.py` → `evidence_<timestamp>.zip`
