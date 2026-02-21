# JUDGE_PROOF — AI Employee Vault Silver Tier

Evidence guide for Hackathon 0 judges. Everything here is verifiable from the repository.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER (5 watchers)                  │
│                                                                  │
│  Inbox/     manual_input.txt  whatsapp_input.txt  linkedin_input │
│     │              │                 │                 │         │
│ [watcher_  [watcher_manual]  [whatsapp_watcher]  [linkedin_      │
│  inbox]                                           watcher]       │
│      \            \               /              /               │
│       ╰────────────╴─────────────╴─────────────╯                 │
│                         │                                        │
│                  Needs_Action/                                   │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     AGENT LAYER (agent.py)                       │
│                                                                  │
│  Skill routing:                                                  │
│    skills/planning_skill.py   → Plans/<task>_Plan.md             │
│    skills/summarize_skill.py  → Pending_Approval/<task>.md       │
│    skills/linkedin_skill.py   → Pending_Approval/linkedin_draft_ │
│                                                                  │
│  MCP tools:                                                      │
│    mcp_file_ops.py      (list / read / write / move)             │
│    mcp_linkedin_ops.py  (LinkedIn UGC Post API + simulated)      │
│    mcp_email_ops.py     (SMTP email + simulated)                 │
│    mcp_calendar_ops.py  (calendar events, simulated)             │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│               HITL LAYER (Human-in-the-Loop)                     │
│                                                                  │
│  Pending_Approval/                                               │
│       │                                                          │
│  [approve.py]   ← MANUAL ONLY — human must run this             │
│       │                                                          │
│  Approved/                                                       │
│       │                                                          │
│  [post_approved.py]  ← posts ONLY from Approved/                │
│    ├── LinkedIn API (or simulated evidence)                      │
│    └── moves to Done/                                            │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     EVIDENCE LAYER                               │
│                                                                  │
│  run_log.md            — human-readable UTC audit log            │
│  prompt_history.md     — full prompt audit trail                 │
│  Logs/events_<date>.jsonl — structured JSONL events             │
│  Logs/summary_<ts>.md  — per-run stats                          │
│  Logs/linkedin_simulated_*.json — simulated post evidence        │
│  Logs/posted_ids.json  — idempotency tracking                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Compliance Mapping

### Mandatory Silver Requirements

| ID | Requirement | Implementation | Status |
|----|-------------|----------------|--------|
| A1 | Watcher: Inbox → Needs_Action | `watcher_inbox.py` | ✅ |
| A2 | Watcher: manual_input.txt → Needs_Action | `watcher_manual.py` | ✅ |
| A3 | Watcher: simulated channel | `whatsapp_watcher.py` (whatsapp_input.txt) | ✅ |
| A4 | Watcher: Gmail API with domain filter + dedup + cloud guard | `gmail_watcher.py` | ✅ |
| B  | Plan.md per task (analysis, steps, risks, checklist) | `skills/planning_skill.py` → `Plans/` | ✅ |
| B  | OpenAI integration + deterministic fallback | `skills/*.py` all have `_call_openai` | ✅ |
| B  | prompt_history.md (timestamp, model, status, file, snippet) | `agent.py:_log_prompt_history()` | ✅ |
| C1 | MCP file ops module | `mcp_file_ops.py` | ✅ |
| C2 | MCP LinkedIn ops (live + simulated + evidence) | `mcp_linkedin_ops.py` | ✅ |
| D  | LinkedIn draft in Pending_Approval for business tasks | `agent.py` + `skills/linkedin_skill.py` | ✅ |
| D  | LinkedIn draft format (title, source, post, status, risk, hash) | `agent.py:li_draft_md` | ✅ |
| D  | post_approved.py posts only from Approved/ | `post_approved.py` | ✅ |
| E  | approve.py: Pending_Approval → Approved (manual only) | `approve.py` | ✅ |
| E  | approve.py list / single / --all | `approve.py` | ✅ |
| F  | GitHub Actions: every 10 min + workflow_dispatch | `.github/workflows/silver-agent.yml` | ✅ |
| F  | Workflow order: watchers → agent → post_approved → commit | `silver-agent.yml` | ✅ |
| F  | Gmail guard: GMAIL_OAUTH_ENABLED | `gmail_watcher.py`, `silver-agent.yml` | ✅ |
| F  | Safe push: git pull --rebase | `silver-agent.yml` | ✅ |
| G  | README: diagram, checklist, demo steps, secrets | `README.md` | ✅ |
| H  | .gitignore: .env, credentials, token, __pycache__ | `.gitignore` | ✅ |
| H  | .env.example with all keys | `.env.example` | ✅ |

### Bonus Items

| ID | Requirement | Implementation | Status |
|----|-------------|----------------|--------|
| A5 | 5th watcher: LinkedIn simulated ingestion | `linkedin_watcher.py` | ✅ BONUS |
| B+ | OPENAI_REQUIRED strict mode (local-only flag) | `agent.py:_check_openai_required()` | ✅ BONUS |
| C3 | MCP email ops (SMTP + simulated + SMTP_FROM) | `mcp_email_ops.py` | ✅ BONUS |
| C3 | Test email CLI script | `send_test_email.py` | ✅ BONUS |
| C4 | MCP calendar ops (simulated local store) | `mcp_calendar_ops.py` | ✅ BONUS |
| D+ | HITL hard block log (blocked_without_approval) | `post_approved.py:_check_and_log_pending_blocks()` | ✅ BONUS |
| D+ | Idempotency: posted_ids.json prevents double-posting | `post_approved.py` | ✅ BONUS |
| F+ | Artifact upload: evidence ZIP per run | `silver-agent.yml` upload-artifact step | ✅ BONUS |
| I1 | Structured event logging: Logs/events_<date>.jsonl | All modules | ✅ BONUS |
| I2 | evidence_pack.py: zip for judges | `evidence_pack.py` | ✅ BONUS |
| I3 | Gmail domain allowlist | `gmail_watcher.py:ALLOWED_DOMAINS` | ✅ BONUS |
| I4 | Stats summary: Logs/summary_<ts>.md | `agent.py` | ✅ BONUS |
| I5 | Skill modules (planning / linkedin / summarize) | `skills/` package | ✅ BONUS |

---

## Simulated vs Real

| Feature | Mode | When Real Fires | Evidence When Simulated |
|---------|------|-----------------|------------------------|
| LinkedIn posting | **SIMULATED by default** | `LINKEDIN_SIMULATED=false` + token + URN set | `Logs/linkedin_simulated_*.json` |
| Email sending | **SIMULATED by default** | `SMTP_HOST` + `SMTP_USER` + `SMTP_PASS` set | `Logs/email_simulated_*.json` |
| OpenAI plans | **Fallback by default** | `OPENAI_API_KEY` set | `plan_fallback` status in Plans/ + prompt_history.md |
| Gmail ingestion | **Disabled in cloud** | `GMAIL_OAUTH_ENABLED=true` + credentials.json | `gmail_watcher_skipped_cloud` in run_log.md |
| WhatsApp ingestion | **Always simulated** | n/a (reads local file) | `whatsapp_input.txt` clears after ingestion |
| LinkedIn ingestion | **Always simulated** | n/a (reads local file) | `linkedin_input.txt` clears after ingestion |
| Calendar ops | **Always simulated** | n/a | `Logs/calendar_events.json` |

**LinkedIn will NEVER post publicly without:**
1. `LINKEDIN_ACCESS_TOKEN` set
2. `LINKEDIN_PERSON_URN` set
3. `LINKEDIN_SIMULATED=false` explicitly

---

## Where to Find Evidence Files

| Evidence | Path |
|----------|------|
| Full audit log (UTC) | `run_log.md` |
| Prompt audit trail | `prompt_history.md` |
| Structured events (JSONL) | `Logs/events_<YYYY-MM-DD>.jsonl` |
| Per-run stats | `Logs/summary_<timestamp>.md` |
| LinkedIn simulated posts | `Logs/linkedin_simulated_*.json` |
| Email simulated sends | `Logs/email_simulated_*.json` |
| Idempotency registry | `Logs/posted_ids.json` |
| Reasoning plans | `Plans/<taskname>_Plan.md` |
| LinkedIn drafts (pending) | `Pending_Approval/linkedin_draft_*.md` |
| Approved items | `Approved/` |
| Completed tasks | `Done/` |
| GitHub Actions artifact | Download from Actions tab → run → Artifacts |

---

## 2-Minute Judge Demo Script

Run these commands in order. Everything works without credentials (simulated mode).

```bash
# 0. Install deps (once)
pip install -r requirements.txt

# 1. Drop a business task into Inbox
echo "Launch a LinkedIn campaign for our new AI product targeting enterprise." > Inbox/demo.md

# 2. Run Watcher 1 — moves Inbox → Needs_Action
python watcher_inbox.py
# Verify: ls Needs_Action/

# 3. Run Agent — generates Plan + Pending_Approval + LinkedIn draft
python agent.py
# Verify:
#   ls Plans/              → demo_Plan.md
#   ls Pending_Approval/   → demo.md  +  linkedin_draft_demo_*.md
#   cat prompt_history.md  → timestamp, model, status, file, prompt snippet

# 4. Show HITL hard block — post_approved refuses unapproved drafts
python post_approved.py
# Log output shows: "blocked_without_approval | linkedin_draft_demo_*.md"
# Verify: cat run_log.md  → "blocked_without_approval" line

# 5. Human approval — moves Pending_Approval → Approved
python approve.py
# Shows list of pending files with [LINKEDIN] tag
python approve.py --all
# Verify: ls Approved/  → linkedin_draft_demo_*.md now here

# 6. Post (simulated — no credentials needed)
python post_approved.py
# Output: "Not posted (simulated_mode). Evidence: Logs/linkedin_simulated_*.json"
# Verify: cat Logs/linkedin_simulated_*.json

# 7. View audit trail
cat run_log.md
cat prompt_history.md
cat Logs/events_$(date +%Y-%m-%d).jsonl
cat Logs/summary_*.md

# 8. Pack evidence for judges
python evidence_pack.py
# Creates evidence_<timestamp>.zip — share this file
```

**Total: ~2 minutes. Zero credentials required.**

---

## Key Design Decisions (Judge Notes)

1. **LinkedIn is ALWAYS simulated by default** — prevents accidental public posts in cloud runs or during demos. Requires explicit opt-in via three separate env vars.

2. **HITL is architecturally enforced** — `post_approved.py` physically only scans `Approved/`. Files in `Pending_Approval/` are logged as `blocked_without_approval`. The two directories are separate; there is no code path that bypasses `approve.py`.

3. **Skills are modular** — `agent.py` routes to `skills/planning_skill.py`, `skills/summarize_skill.py`, `skills/linkedin_skill.py`. Each skill is self-contained with its own OpenAI call and fallback.

4. **No credentials = full functionality** — every feature degrades gracefully: OpenAI → deterministic fallback plan, LinkedIn → JSON evidence file, Email → JSON evidence file, Gmail → clean skip with log.

5. **Idempotency** — `Logs/posted_ids.json` tracks SHA1 hashes of all posted tasks. Re-running `post_approved.py` never double-posts.
