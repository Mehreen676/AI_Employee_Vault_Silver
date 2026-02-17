# Skill: process_task

## Purpose
Process a task note in the Obsidian vault by rewriting it into a structured “Processed Task” format, then moving it to Done.

## Input
- A markdown file located in: /Needs_Action/<task>.md

## Output
- The same file rewritten with:
  - Processed Task header
  - Original Content section
  - AI Summary section
  - Status: Completed
- Then the file moved to: /Done/<task>.md
- A run log entry appended to: /run_log.md

## Required Access (Claude Code)
- Read: /Needs_Action/*
- Write: /Needs_Action/*
- Move files: /Needs_Action → /Done
- Append: /run_log.md

## Steps
1. Find one pending task file in /Needs_Action (first .md).
2. Read its content fully.
3. Rewrite the file in the template below:
   - Keep original content in “Original Content”
   - Write a clear, professional “AI Summary” (bullets ok)
   - Set “Status: Completed”
4. Save the rewritten content back into the same file.
5. Move the processed file to /Done.
6. Append a log line into /run_log.md with timestamp + filename + TASK_COMPLETE.
7. Return: TASK_COMPLETE

## Template (must follow)
# Processed Task

## Original Content
<copy original content here>

## AI Summary
<your summary here>

Status: Completed
