---
tags: [reference, fundamentals, knowledge-management]
related: ["[[99_references/meetings/README]]"]
summary: "Local-only drop folder for raw meeting transcripts (.vtt) awaiting ingestion; its contents are gitignored and never committed."
---

# Transcripts

A drop folder for **raw meeting transcripts** waiting to be ingested by the `ingest-meeting` agent. The resulting notes go to [[99_references/meetings/README|99_references/meetings/]].

## Nothing Here Is Committed

Everything in this folder except this README is **gitignored**. Meeting transcripts are internal and may contain sensitive information, so they stay on your machine. In Claude Code sessions, a hook (`.claude/hooks/block_commit_on_main.sh`) also blocks any commit that stages a file from here, which catches `git add -f`. If you commit by hand, `.gitignore` is the only guard, so don't force-add files from this folder.

## What Goes Here

- `.vtt` transcript downloads from Teams, Zoom or Webex
- Keep the downloaded filename: Teams names it after the meeting, which helps the agent fill in the title

## After Ingestion

Transcripts are **kept** after ingestion so you (or Claude, on request) can check a timestamp cited in a meeting note against what was actually said. Delete them when you no longer need them; nothing else depends on them.

## Things to Know

- **Synced folders.** If this knowledge base sits in OneDrive, Dropbox or iCloud, this folder syncs with it, like the rest of the vault.
- **Session logs.** Claude Code keeps what it reads in a session, including a transcript, in its local session logs (`~/.claude/projects/`) for about 30 days by default (the `cleanupPeriodDays` setting).
- **Model provider.** Transcript content is sent to Anthropic during ingestion. Check that your organization's agreement covers meeting content.
