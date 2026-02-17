# Bronze Tier – Foundation (Hackathon 0)

Reference: Personal AI Employee Hackathon 0 PDF

## Objective
Build a minimum viable Personal AI Employee using:
- Obsidian (Memory / GUI)
- Claude Code (Reasoning Engine)
- One Watcher Script (Perception Layer)

---

## ✅ Completed Requirements

### 1. Obsidian Vault Setup
- Vault Name: AI_Employee_Vault
- Files:
  - Dashboard.md
  - Company_Handbook.md

### 2. Folder Structure
- /Inbox
- /Needs_Action
- /Done

### 3. One Working Watcher
- Implemented: File System Watcher (Python)
- Function: Moves .md files from /Inbox to /Needs_Action

### 4. Claude Code Integration
- Claude Code installed (v2.1.42)
- Runs in vault directory
- Reads tasks from /Needs_Action
- Writes processed output back to vault

### 5. AI Processing
- Processor script generates:
  - Task summary
  - Status update
- Moves completed tasks to /Done

---

## Architecture Overview

Perception → Reasoning → Action

Watcher (Python)
    ↓
/Needs_Action (Vault)
    ↓
Claude Code Processing
    ↓
/Done (Vault)

---

## Status

Bronze Tier: In Progress (Final Claude Skill Integration Pending)
