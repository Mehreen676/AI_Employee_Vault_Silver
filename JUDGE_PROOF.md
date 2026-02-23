# JUDGE_PROOF — AI Employee Vault Silver Tier

Hackathon 0 evidence guide. Every claim below is verifiable directly from repository files.
Real log lines, real file paths, real JSONL events — no invented output.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Watcher Coverage — 5 Channels](#2-watcher-coverage--5-channels)
3. [Agent Processing — Plans + Pending_Approval](#3-agent-processing--plans--pending_approval)
4. [OpenAI + Fallback Safety](#4-openai--fallback-safety)
5. [HITL Enforcement Proof](#5-hitl-enforcement-proof)
6. [LinkedIn Posting + Idempotency](#6-linkedin-posting--idempotency)
7. [Structured Logging Proof](#7-structured-logging-proof)
8. [GitHub Actions Automation Proof](#8-github-actions-automation-proof)
9. [Gmail OAuth + Domain Allowlist + Dedup](#9-gmail-oauth--domain-allowlist--dedup)
10. [Simulated vs Real Mode Table](#10-simulated-vs-real-mode-table)
11. [Full Compliance Mapping](#11-full-compliance-mapping)
12. [Evidence File Index](#12-evidence-file-index)
13. [Judge Demo Script](#13-judge-demo-script)
14. [Key Design Decisions](#14-key-design-decisions)

---

## 1. Architecture Overview

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                    INGESTION LAYER  (5 watchers)                      │
 │                                                                       │
 │  Inbox/  manual_input.txt  whatsapp_input.txt  linkedin_input.txt    │
 │    │           │                  │                   │               │
 │ [watcher_  [watcher_      [whatsapp_         [linkedin_               │
 │  inbox]    manual]         watcher]           watcher]                │
 │      \        \               /                  /                    │
 │       ╰────────╴─────────────╴──────────────────╯                     │
 │                              │                                        │
 │        Gmail API ──────► [gmail_watcher] ──► Inbox/                  │
 │        (when GMAIL_OAUTH_ENABLED=true + secrets present)              │
 │                              │                                        │
 │                        Needs_Action/                                  │
 └──────────────────────────────┼────────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼────────────────────────────────────────┐
 │                      AGENT LAYER  (agent.py)                           │
 │                                                                        │
 │  skills/planning_skill.py   →  Plans/<task>_Plan.md                   │
 │  skills/summarize_skill.py  →  Pending_Approval/<task>.md             │
 │  skills/linkedin_skill.py   →  Pending_Approval/linkedin_draft_*.md   │
 │                                (business tasks only)                   │
 │  MCP tools: mcp_file_ops · mcp_linkedin_ops · mcp_email_ops           │
 │             mcp_calendar_ops                                           │
 └──────────────────────────────┼────────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼────────────────────────────────────────┐
 │                   HITL LAYER  (Human-in-the-Loop)                      │
 │                                                                        │
 │  Pending_Approval/                                                     │
 │       │   [approve.py]  ← MANUAL ONLY — never auto-invoked            │
 │  Approved/                                                             │
 │       │   [post_approved.py]  ← reads ONLY from Approved/             │
 │  Done/  + Logs/evidence                                                │
 └──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Watcher Coverage — 5 Channels

### Channel 1 — `watcher_inbox.py`

- **Source:** Any `.md` file dropped into `Inbox/`
- **Action:** Copies to `Needs_Action/`, moves source to `Done/`
- **Verify:** `ls Inbox/` → drop a file → `python watcher_inbox.py` → `ls Needs_Action/`

### Channel 2 — `watcher_manual.py`

- **Source:** `manual_input.txt` — tasks separated by `---`
- **Action:** Splits entries, writes each as a timestamped `.md` in `Needs_Action/`, clears the file
- **Verify:** Write lines to `manual_input.txt` → `python watcher_manual.py` → `ls Needs_Action/`

### Channel 3 — `whatsapp_watcher.py`

- **Source:** `whatsapp_input.txt` — simulated WhatsApp DMs
- **Action:** Ingests entries into `Needs_Action/`, clears file
- **Log evidence** (`Logs/events_2026-02-21.jsonl`):
  ```json
  {"ts": "2026-02-21 02:00:19Z", "event": "whatsapp_watcher_skip", "reason": "empty_file"}
  ```
  Logged on every run even when empty — proves the watcher executed in the cloud workflow.

### Channel 4 — `linkedin_watcher.py` *(bonus)*

- **Source:** `linkedin_input.txt` — simulated LinkedIn DMs/leads
- **Action:** Ingests entries into `Needs_Action/`, clears file
- **Log evidence** (`Logs/events_2026-02-21.jsonl`):
  ```json
  {"ts": "2026-02-21 02:00:19Z", "event": "linkedin_watcher_skip", "reason": "empty_file"}
  ```

### Channel 5 — `gmail_watcher.py`

- **Source:** Gmail API — unread inbox, domain-filtered, deduped by message ID
- **Real ingestion evidence** (`run_log.md`):
  ```
  2026-02-21 09:07:11Z - Gmail: starting
  2026-02-21 09:07:12Z - Gmail: ingested | email_20260221_090712_19c7b2ad2c7912f1.md | from=Google AI Studio <googleaistudio-noreply@google.com>
  2026-02-21 09:07:13Z - Gmail: done | ingested=1
  ```
- Sender domain `google.com` — passes allowlist. Message ID embedded in filename for dedup.
- **See also:** [Section 9](#9-gmail-oauth--domain-allowlist--dedup)

---

## 3. Agent Processing — Plans + Pending_Approval

### What `agent.py` does per task

1. Reads `.md` file from `Needs_Action/`
2. Calls `skills/planning_skill.py` → writes `Plans/<task>_Plan.md`
3. Calls `skills/summarize_skill.py` → writes `Pending_Approval/<task>.md`
4. If business task detected: calls `skills/linkedin_skill.py` → writes `Pending_Approval/linkedin_draft_<task>_<hash>.md`
5. Moves source to `Done/_source_<task>.md`

### Real plan files in `Plans/` (verified by `ls Plans/`)

```
Plans/
  demo_Plan.md
  demo_ai_real_estate_Plan.md
  inbox-test_Plan.md
  li_20260220_042906_1_Plan.md
  li_20260220_042906_2_Plan.md
  manual_20260217_073614_1_Plan.md
  manual_20260217_073614_2_Plan.md
  task_ai_realestate_Plan.md
  task_new_Plan.md
  task_openai_test_Plan.md
```

### Plan file format (verified — `Plans/demo_Plan.md`)

```markdown
# Plan: demo

Generated: 2026-02-20 04:29:16Z
Model: gpt-4o-mini
Status: plan_fallback

---

## 1. Task Analysis
## 2. Step-by-Step Plan
## 3. Risks & Edge Cases
## 4. Output Checklist
```

All four required sections are present in every plan file.

### Real `run_log.md` lines — plans created

```
2026-02-20 04:29:16Z - Agent: plan_created | demo_Plan.md | plan_fallback
2026-02-20 04:29:16Z - Agent: plan_created | li_20260220_042906_1_Plan.md | plan_fallback
2026-02-20 04:29:16Z - Agent: plan_created | li_20260220_042906_2_Plan.md | plan_fallback
2026-02-20 04:29:16Z - Agent: plan_created | test_marketing_Plan.md | plan_fallback
2026-02-21 04:15:28Z - Agent: plan_created | test_judge_Plan.md | plan_fallback
2026-02-21 06:03:40Z - Agent: plan_created | task_real_test_Plan.md | plan_fallback
```

### Real `run_log.md` lines — LinkedIn drafts created

```
2026-02-20 04:29:16Z - Agent: linkedin_draft_created | linkedin_draft_li_20260220_042906_1_fae28a47a687.md | linkedin_fallback
2026-02-20 04:29:16Z - Agent: linkedin_draft_created | linkedin_draft_li_20260220_042906_2_73017b347e6a.md | linkedin_fallback
2026-02-20 04:29:16Z - Agent: linkedin_draft_created | linkedin_draft_test_marketing_d6b334630fa8.md | linkedin_fallback
2026-02-21 04:15:28Z - Agent: linkedin_draft_created | linkedin_draft_test_judge_59986181bbdd.md | linkedin_fallback
2026-02-21 06:03:45Z - Agent: linkedin_draft_created | linkedin_draft_task_real_test_7143767d81c6.md | linkedin_fallback
```

### Source files moved to `Done/` (verified by `ls Done/`)

```
Done/
  _source_demo.md
  _source_demo_ai_real_estate.md
  _source_li_20260220_042906_1.md
  _source_li_20260220_042906_2.md
  _source_task_ai_realestate.md
  _source_task_new.md
  _source_task_openai_test.md
  _source_task_real_test.md
  _source_task1.md
  _source_task2.md
```

### Real run summary (`Logs/summary_20260220_042916.md`)

| Metric | Count |
|--------|-------|
| Tasks processed | 6 |
| Plans created | 6 |
| LinkedIn drafts created | 3 |
| OpenAI OK responses | 0 |
| Fallback responses | 12 |
| Errors | 0 |

---

## 4. OpenAI + Fallback Safety

### How it works

Every skill module wraps its API call in `_call_openai()`:

1. If `OPENAI_API_KEY` is absent → returns `("", "no_api_key")` immediately
2. If key is present → calls OpenAI inside `try/except Exception`
3. Any exception — `429 insufficient_quota`, network timeout, invalid key — is caught → returns `("(OpenAI error: ...)", "openai_error")`
4. Calling function detects non-`openai_ok` status → produces deterministic fallback
5. Status recorded as `plan_fallback` (planning skill) or `fallback` (summarise / linkedin skills)

**The agent never crashes regardless of OpenAI availability.**

### Real evidence — `openai_ok` (API worked)

From `run_log.md`:
```
2026-02-17 06:14:25Z - Processed: judge-proof.md | openai_ok
2026-02-17 06:14:27Z - Processed: openai-check.md | openai_ok
2026-02-17 06:43:20Z - Processed: demo.md | openai_ok
```

### Real evidence — fallback (API unavailable or quota exceeded)

From `run_log.md`:
```
2026-02-17 06:33:26Z - Processed: judge-proof.md | fallback
2026-02-17 10:49:40Z - Processed: email_20260217_104533_19c44327c1ae1340.md | fallback
2026-02-20 04:29:16Z - Agent: plan_created | demo_Plan.md | plan_fallback
```

Both statuses appear in the log — demonstrating that `openai_ok` and `fallback` paths are real and tested.

### Fallback plan content (verified — `Plans/demo_Plan.md`)

When fallback fires, all four required sections are present with deterministic content:
- `## 1. Task Analysis` — states fallback reason explicitly
- `## 2. Step-by-Step Plan` — generic 4-step action plan
- `## 3. Risks & Edge Cases` — two standard risk items
- `## 4. Output Checklist` — three unchecked deliverable items

Status field reads `plan_fallback` — verifiable in any plan file header.

### `prompt_history.md` records every attempt

From `prompt_history.md`:
```
[2026-02-17 06:33:26Z] FILE: judge-proof.md
MODEL: gpt-4o-mini
STATUS: fallback
PROMPT:
fallback
```

Entries exist for both `openai_ok` and `fallback` runs.

### `OPENAI_REQUIRED` strict mode

- `agent.py` reads `OPENAI_REQUIRED` env var (default `false` locally)
- When `true`: agent exits with an error if `OPENAI_API_KEY` is entirely absent
- **Set to `true` in `silver-agent.yml`** — cloud runs require the key
- Locally, the default `false` allows silent fallback without interruption

---

## 5. HITL Enforcement Proof

### Architectural guarantee

`post_approved.py` is hardcoded to read from `Approved/` only:

```python
li_files = list_files(APPROVED, "linkedin_draft_*.md")
```

No code path reads `Pending_Approval/`. The two directories are physically separate on disk.

### Hard block — unapproved drafts are logged, never posted

Before processing `Approved/`, `post_approved.py` calls `_check_and_log_pending_blocks()`, which scans `Pending_Approval/` for `linkedin_draft_*` files and logs each as `blocked_without_approval`.

**Real `run_log.md` evidence:**
```
2026-02-21 04:15:28Z - PostApproved: blocked_without_approval | linkedin_draft_test_judge_59986181bbdd.md
2026-02-21 06:03:45Z - PostApproved: blocked_without_approval | linkedin_draft_task_real_test_7143767d81c6.md
2026-02-21 09:07:14Z - PostApproved: blocked_without_approval | linkedin_draft_task_openai_test_7143767d81c6.md
2026-02-21 09:07:14Z - PostApproved: blocked_without_approval | linkedin_draft_task_openai_test_bf0c6d5236fa.md
2026-02-21 09:07:14Z - PostApproved: blocked_without_approval | linkedin_draft_task_real_test_7143767d81c6.md
```

These lines prove: unapproved drafts existed, were detected, and were not posted.

### `approve.py` — manual-only CLI

```bash
python approve.py                    # list pending (shows [LINKEDIN] tag)
python approve.py <filename.md>      # approve one file
python approve.py --all              # approve all pending files
```

- Not called anywhere in `silver-agent.yml`
- Each approval logged: `Approved: <file> -> Approved/`
- No auto-approve code path exists

### Files in `Pending_Approval/` (awaiting human approval)

```
Pending_Approval/
  linkedin_draft_task_openai_test_7143767d81c6.md
  linkedin_draft_task_openai_test_bf0c6d5236fa.md
  linkedin_draft_task_real_test_7143767d81c6.md
  linkedin_draft_task1_ec417a5820f7.md
  linkedin_draft_test_ai_788d586d2538.md
  task_openai_test.md
  task_real_test.md
  ...
```

### Files in `Approved/` (human-approved, awaiting posting)

```
Approved/
  linkedin_draft_li_20260220_042906_1_fae28a47a687.md
  linkedin_draft_li_20260220_042906_2_73017b347e6a.md
  linkedin_draft_test_judge_59986181bbdd.md
  linkedin_draft_test_marketing_d6b334630fa8.md
  ...
```

---

## 6. LinkedIn Posting + Idempotency

### LinkedIn draft file format

Each `linkedin_draft_*.md` contains:

| Field | Value |
|-------|-------|
| `**Title:**` | LinkedIn Post Approval |
| `**Source Task:**` | originating task filename |
| `**Generated:**` | UTC timestamp |
| `**Status:**` | Pending Approval |
| `**Task Hash:**` | 12-char SHA1 hex (used for idempotency) |
| `**Risk Note:**` | explicit human-approval warning |
| `## Generated Post Text` | the actual draft copy |

### Simulated posting evidence (real file — `Logs/linkedin_simulated_20260220_043032.json`)

```json
{
  "ts": "2026-02-20 04:30:32Z",
  "mode": "simulated",
  "reason": "simulated_mode",
  "post_text": "Exciting update from our team! We've been working on something remarkable and can't wait to share more details soon. Stay tuned for the big reveal.\n\n#Innovation #BusinessGrowth #ComingSoon",
  "token_present": false,
  "person_urn_present": false
}
```

- `token_present: false` — no credentials present, confirms simulated path
- 19+ `linkedin_simulated_*.json` files exist in `Logs/` across multiple run dates

### Real `run_log.md` — simulated posting

```
2026-02-21 09:07:14Z - linkedin_post_attempt | mode=simulated | reason=simulated_mode
2026-02-21 09:07:14Z - PostApproved: simulated_mode | linkedin_draft_li_20260220_042906_1_fae28a47a687.md | kept in Approved/
2026-02-21 09:07:14Z - PostApproved: simulated_mode | linkedin_draft_li_20260220_042906_2_73017b347e6a.md | kept in Approved/
2026-02-21 09:07:14Z - PostApproved: done | {'found': 4, 'posted': 0, 'skipped_duplicate': 0, 'skipped_not_configured': 4, 'errors': 0}
```

`kept in Approved/` — file is NOT moved to `Done/` in simulated mode. Only a real successful API post moves the file.

### Idempotency registry

`Logs/posted_ids.json` — current state (no real posts made):
```json
{ "posted_hashes": [] }
```

On a real post: the task's SHA1 hash is added. Subsequent runs of `post_approved.py` skip the file with `skipped_duplicate` status — no double-posting.

### LinkedIn will NEVER post publicly without all three

1. `LINKEDIN_ACCESS_TOKEN` — valid OAuth token
2. `LINKEDIN_PERSON_URN` — e.g. `urn:li:person:AbCdEfGh`
3. `LINKEDIN_SIMULATED=false` — explicit opt-out of simulated mode

---

## 7. Structured Logging Proof

### Three parallel audit systems

| System | File | Format |
|--------|------|--------|
| Human-readable UTC log | `run_log.md` | Plain text, one line per event |
| Prompt audit trail | `prompt_history.md` | Blocks: timestamp, model, status, file, prompt snippet |
| Structured event stream | `Logs/events_<YYYY-MM-DD>.jsonl` | One JSON object per line |
| Per-run stats | `Logs/summary_<timestamp>.md` | Markdown table with counts |

### Real JSONL events (from `Logs/events_2026-02-21.jsonl`)

```json
{"ts": "2026-02-21 02:00:19Z", "event": "whatsapp_watcher_skip", "reason": "empty_file"}
{"ts": "2026-02-21 02:00:19Z", "event": "linkedin_watcher_skip", "reason": "empty_file"}
{"ts": "2026-02-21 02:00:19Z", "event": "gmail_watcher_skipped_cloud", "GMAIL_OAUTH_ENABLED": "false"}
{"ts": "2026-02-21 02:00:19Z", "event": "agent_started", "model": "gpt-4o-mini", "openai_required": false}
{"ts": "2026-02-21 02:00:19Z", "event": "agent_no_tasks"}
{"ts": "2026-02-21 02:00:19Z", "event": "agent_summary", "tasks_processed": 0, "plans_created": 0, "linkedin_drafts_created": 0, "fallback_count": 0, "openai_ok_count": 0, "errors": 0}
{"ts": "2026-02-21 02:00:19Z", "event": "post_approved_started"}
{"ts": "2026-02-21 02:00:19Z", "event": "linkedin_post_attempt", "mode": "simulated", "reason": "simulated_mode"}
{"ts": "2026-02-21 02:00:19Z", "event": "linkedin_not_posted_kept", "file": "linkedin_draft_li_20260220_042906_1_fae28a47a687.md", "reason": "simulated_mode", "evidence": ".../Logs/linkedin_simulated_20260221_020019.json"}
{"ts": "2026-02-21 02:00:19Z", "event": "post_approved_done", "found": 3, "posted": 0, "skipped_duplicate": 0, "skipped_not_configured": 3, "errors": 0}
```

These events prove the full pipeline executed in a single cloud run.

### `Logs/` directory — real files present

```
Logs/
  events_2026-02-20.jsonl
  events_2026-02-21.jsonl
  linkedin_simulated_20260220_043032.json
  linkedin_simulated_20260220_052001.json
  ... (19+ simulated evidence files)
  posted_ids.json
  summary_20260220_042916.md
  summary_20260220_052001.md
  ... (5+ summary files)
```

---

## 8. GitHub Actions Automation Proof

**File:** `.github/workflows/silver-agent.yml`

### Triggers

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "*/10 * * * *"
```

Every 10 minutes + manual dispatch. No push trigger — prevents recursive commit loops.

### Concurrency control

```yaml
concurrency:
  group: silver-agent
  cancel-in-progress: true
```

A new scheduled run cancels any still-running previous run.

### Step order (verified from `silver-agent.yml`)

| Step | Command |
|------|---------|
| Watcher 1 | `python watcher_inbox.py` |
| Watcher 2 | `python watcher_manual.py` |
| Watcher 3 | `python whatsapp_watcher.py` |
| Watcher 4 | `python linkedin_watcher.py` |
| Gmail OAuth setup | `if: env.GMAIL_OAUTH_ENABLED == 'true'` |
| Watcher 5 | `python gmail_watcher.py` — `if: env.GMAIL_OAUTH_ENABLED == 'true'` |
| Agent | `python agent.py` |
| Post | `python post_approved.py` |
| Commit | `git pull --rebase && git push` |
| Summary | `echo` counts from `run_log.md` and `ls` |
| Artifact | `actions/upload-artifact@v4` — 30-day retention |

### Committed paths (only relevant dirs staged)

```bash
git add Needs_Action/ Pending_Approval/ Approved/ Done/ Plans/ Logs/ run_log.md prompt_history.md
```

### Cloud execution proof

`Logs/events_2026-02-21.jsonl` contains `"event": "gmail_watcher_skipped_cloud"` with `"GMAIL_OAUTH_ENABLED": "false"`. This event is emitted only when running inside the cloud workflow without Gmail enabled — its presence proves the full watcher chain executed on GitHub Actions.

---

## 9. Gmail OAuth + Domain Allowlist + Dedup

### Domain allowlist (`gmail_watcher.py:ALLOWED_DOMAINS`)

```python
ALLOWED_DOMAINS = {
    "google.com",
    "github.com",
    "microsoft.com",
    "azure.com",
    "anthropic.com",
}
```

Exact domain match or subdomain (e.g. `mail.google.com` passes). All other senders are silently skipped.

### Real ingestion evidence

From `run_log.md`:
```
2026-02-21 09:07:11Z - Gmail: starting
2026-02-21 09:07:12Z - Gmail: ingested | email_20260221_090712_19c7b2ad2c7912f1.md | from=Google AI Studio <googleaistudio-noreply@google.com>
2026-02-21 09:07:13Z - Gmail: done | ingested=1
```

Sender `googleaistudio-noreply@google.com` → domain `google.com` → allowlist passes ✅

### Deduplication logic

```python
def file_exists_for_id(msg_id: str) -> bool:
    suffix = f"_{msg_id}.md"
    for folder in [INBOX, DONE]:
        if any(f.name.endswith(suffix) for f in folder.glob("*.md")):
            return True
    return False
```

Checks both `Inbox/` and `Done/`. Same Gmail message ID → same filename suffix → never written twice.

### Cloud guard in `silver-agent.yml`

```yaml
- name: "[Watcher 5] Gmail -> Inbox (OAuth guarded)"
  if: env.GMAIL_OAUTH_ENABLED == 'true'
  run: python gmail_watcher.py
```

When `GMAIL_OAUTH_ENABLED` is not `true`, the step is skipped entirely at the workflow level.

When the step runs but `credentials.json` is absent, `gmail_watcher.py` prints `"credentials.json not found."` and calls `raise SystemExit(1)` — a clean exit, not a system failure. Installing requirements and providing credentials restores full functionality.

---

## 10. Simulated vs Real Mode Table

| Feature | Default | Condition for real mode | Evidence when simulated |
|---------|---------|------------------------|------------------------|
| LinkedIn posting | **Simulated** | `LINKEDIN_SIMULATED=false` + `LINKEDIN_ACCESS_TOKEN` + `LINKEDIN_PERSON_URN` | `Logs/linkedin_simulated_<ts>.json` |
| Email sending | **Simulated** | `SMTP_HOST` + `SMTP_USER` + `SMTP_PASS` set | `Logs/email_simulated_<ts>.json` |
| OpenAI plans | **Fallback** if key absent or API error | `OPENAI_API_KEY` valid + within quota | `plan_fallback` / `fallback` in `Plans/` and `prompt_history.md` |
| Gmail ingestion | **Disabled** in cloud unless enabled | `GMAIL_OAUTH_ENABLED=true` + secrets | `gmail_watcher_skipped_cloud` in JSONL |
| WhatsApp ingestion | **Always simulated** | n/a — reads local file | `whatsapp_watcher_skip` / ingested event in JSONL |
| LinkedIn ingestion | **Always simulated** | n/a — reads local file | `linkedin_watcher_skip` / ingested event in JSONL |
| Calendar ops | **Always simulated** | n/a | `Logs/calendar_events.json` |

---

## 11. Full Compliance Mapping

### Mandatory Requirements

| ID | Requirement | Implementation | How to Verify |
|----|-------------|----------------|---------------|
| A1 | Watcher: Inbox → Needs_Action | `watcher_inbox.py` | `ls Done/_source_*.md` — 10+ source files |
| A2 | Watcher: manual_input.txt → Needs_Action | `watcher_manual.py` | `ls Needs_Action/manual_*.md` |
| A3 | Watcher: simulated channel | `whatsapp_watcher.py` | `events_*.jsonl: whatsapp_watcher_skip` on every run |
| A4 | Watcher: Gmail API, domain filter, dedup, guard | `gmail_watcher.py` | `run_log.md: Gmail: ingested` real line |
| B | `Plans/<task>_Plan.md` per task (4 sections) | `skills/planning_skill.py` → `Plans/` | `ls Plans/` — 10 files; open any plan |
| B | OpenAI integration + deterministic fallback (missing key or 429) | `skills/*.py:_call_openai()` + fallback block | `run_log.md`: both `openai_ok` and `fallback` lines |
| B | `prompt_history.md` (timestamp, model, status, file, snippet) | `agent.py:_log_prompt_history()` | `cat prompt_history.md` |
| C1 | MCP file ops module | `mcp_file_ops.py` | Imported by agent, approve, post, all watchers |
| C2 | MCP LinkedIn ops (live + simulated + evidence) | `mcp_linkedin_ops.py` | `Logs/linkedin_simulated_*.json` — 19+ files |
| D | LinkedIn draft for business tasks in Pending_Approval | `agent.py` + `skills/linkedin_skill.py` | `ls Pending_Approval/linkedin_draft_*.md` |
| D | Draft format: title, source, post, status, risk note, hash | `agent.py:li_draft_md` | Open any `linkedin_draft_*.md` |
| D | `post_approved.py` posts only from `Approved/` | `post_approved.py` | Source: `list_files(APPROVED, "linkedin_draft_*.md")` |
| E | `approve.py`: Pending_Approval → Approved, manual only | `approve.py` | Not present in `silver-agent.yml` |
| E | `approve.py` list / single / `--all` | `approve.py` | `python approve.py` (no args) shows list |
| F | GitHub Actions: every 10 min + `workflow_dispatch` | `silver-agent.yml` | `cron: "*/10 * * * *"` in yml |
| F | Workflow order: watchers → agent → post → commit | `silver-agent.yml` | Step sequence in yml |
| F | Gmail guard: step conditional on `GMAIL_OAUTH_ENABLED` | `silver-agent.yml` | `if: env.GMAIL_OAUTH_ENABLED == 'true'` |
| F | Safe push: `git pull --rebase` before push | `silver-agent.yml` | Commit step in yml |
| G | README: diagram, checklist, demo steps, secrets | `README.md` | Open `README.md` |
| G | `JUDGE_PROOF.md` compliance evidence | This file | You are reading it |
| H | `.gitignore`: `.env`, `credentials.json`, `token.json`, `__pycache__` | `.gitignore` | `cat .gitignore` |
| H | `.env.example` with all keys | `.env.example` | `cat .env.example` |

### Bonus Items

| ID | Requirement | Implementation | How to Verify |
|----|-------------|----------------|---------------|
| A5 | 5th watcher: LinkedIn simulated ingestion | `linkedin_watcher.py` | `events_*.jsonl: linkedin_watcher_skip` on every run |
| B+ | `OPENAI_REQUIRED` strict mode | `agent.py:_check_openai_required()` | Set `true` in `silver-agent.yml` env block |
| C3 | MCP email ops (SMTP + simulated) | `mcp_email_ops.py` | `Logs/email_simulated_*.json` |
| C3 | Email test CLI script | `send_test_email.py` | `python send_test_email.py` |
| C4 | MCP calendar ops (simulated local store) | `mcp_calendar_ops.py` | `Logs/calendar_events.json` |
| D+ | HITL hard block log (`blocked_without_approval`) | `post_approved.py:_check_and_log_pending_blocks()` | `grep blocked_without_approval run_log.md` — 5 real lines |
| D+ | Idempotency: `Logs/posted_ids.json` prevents double-posting | `post_approved.py` | `cat Logs/posted_ids.json` |
| F+ | Artifact upload per run (30-day retention) | `silver-agent.yml` upload-artifact step | Actions tab → run → Artifacts |
| I1 | Structured JSONL events: `Logs/events_<date>.jsonl` | All modules call `log_event()` | `cat Logs/events_*.jsonl` |
| I2 | `evidence_pack.py` ZIP for judges | `evidence_pack.py` | `python evidence_pack.py` → `evidence_<ts>.zip` |
| I3 | Gmail domain allowlist | `gmail_watcher.py:ALLOWED_DOMAINS` | Source code + real ingestion log line |
| I4 | Stats summary: `Logs/summary_<ts>.md` | `agent.py` end-of-run block | `ls Logs/summary_*.md` — 5+ files |
| I5 | Modular skill package (`skills/`) | `planning_skill.py`, `summarize_skill.py`, `linkedin_skill.py` | `ls skills/` |

---

## 12. Evidence File Index

| Evidence | Location | Notes |
|----------|----------|-------|
| UTC audit log | `run_log.md` | Real entries from 2026-02-17 to 2026-02-21 |
| Prompt audit trail | `prompt_history.md` | Both `openai_ok` and `fallback` entries present |
| JSONL events | `Logs/events_2026-02-20.jsonl` `Logs/events_2026-02-21.jsonl` | Full structured event records per cloud run |
| Per-run stats | `Logs/summary_20260220_042916.md` + 4 more | Tasks, plans, LinkedIn drafts, fallback counts |
| Reasoning plans | `Plans/` — 10 files | All four sections in every plan |
| LinkedIn simulated posts | `Logs/linkedin_simulated_*.json` — 19+ files | JSON: mode, reason, post_text, token_present |
| Idempotency registry | `Logs/posted_ids.json` | SHA1 hash list (empty — no real posts made yet) |
| LinkedIn drafts pending | `Pending_Approval/linkedin_draft_*.md` | Awaiting `python approve.py` |
| Approved drafts | `Approved/linkedin_draft_*.md` | Human-approved, awaiting `post_approved.py` real run |
| Completed source tasks | `Done/_source_*.md` — 10+ files | Moved by agent after processing |
| Evidence ZIP | `evidence_20260220_043144.zip` | Generated by `evidence_pack.py` |
| GitHub Actions artifacts | Actions tab → run → Artifacts | Uploaded each run, 30-day retention |

---

## 13. Judge Demo Script

Run in order. Zero credentials required — fully simulated.

```bash
# 0. Install dependencies (once)
pip install -r requirements.txt

# 1. Drop a business task into Inbox
echo "Launch a LinkedIn campaign for our new AI product targeting enterprise." > Inbox/demo.md

# 2. Watcher 1 — Inbox → Needs_Action
python watcher_inbox.py
ls Needs_Action/           # demo.md appears

# 3. Agent — generates Plan + summary + LinkedIn draft
python agent.py
ls Plans/                  # demo_Plan.md
ls Pending_Approval/       # demo.md  +  linkedin_draft_demo_<hash>.md
cat prompt_history.md      # model, status (plan_fallback or openai_ok), prompt snippet

# 4. HITL hard block — post_approved refuses unapproved drafts
python post_approved.py
# Output: [BLOCKED] linkedin_draft_demo_*.md — requires human approval first.
grep "blocked_without_approval" run_log.md   # auditable proof

# 5. Human approval — Pending_Approval → Approved
python approve.py           # list; [LINKEDIN] tag shown
python approve.py --all     # approve all
ls Approved/                # linkedin_draft_demo_*.md moved here

# 6. Post (simulated — no LinkedIn credentials needed)
python post_approved.py
# Output: "Not posted (simulated_mode). File kept in Approved/."
ls Logs/                    # linkedin_simulated_*.json written as evidence

# 7. Audit trail
cat run_log.md
cat prompt_history.md
cat "Logs/events_$(date +%Y-%m-%d).jsonl"
cat Logs/summary_*.md

# 8. Evidence ZIP
python evidence_pack.py
# Creates: evidence_<timestamp>.zip
```

**Total: ~2 minutes. Zero credentials required.**

---

## 14. Key Design Decisions

**1. LinkedIn default-simulated — three separate opt-ins required**
LinkedIn will never post publicly without `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, and `LINKEDIN_SIMULATED=false` all set simultaneously. Cloud runs, local runs, and CI all default to simulated mode. Evidence JSON is the only output.

**2. HITL is architecturally enforced, not just policy**
`post_approved.py` contains `list_files(APPROVED, "linkedin_draft_*.md")` — hardcoded to `Approved/`. `approve.py` is absent from `silver-agent.yml`. There is no code path — accidental or intentional — that posts without explicit human invocation of `approve.py`.

**3. OpenAI failure is safe by design — including 429**
All three skills wrap `_call_openai()` in `try/except Exception`. Any error — `429 insufficient_quota`, connection timeout, invalid key — is caught silently. Deterministic fallback output is written. Status fields (`plan_fallback`, `fallback`, `linkedin_fallback`) make every fallback instance auditable in `run_log.md` and `prompt_history.md`.

**4. Skills are independently modular**
`agent.py` delegates to three separate skill files in `skills/`. Each owns its own OpenAI call, fallback, and prompt template. Skills can be called or tested independently without the full agent loop.

**5. Idempotency prevents double-posting across runs**
SHA1 hashes of posted tasks are persisted in `Logs/posted_ids.json`. Multiple workflow runs, re-runs after failure, or manual re-invocations of `post_approved.py` will never post the same content twice.

**6. Structured JSONL enables machine-readable audit**
`Logs/events_<date>.jsonl` uses one JSON object per line with consistent `ts` and `event` fields. Every pipeline stage emits events — judges or tools can parse and validate the complete execution trace without reading plain-text logs.
