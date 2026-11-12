# Spec: Meeting Transcript Ingestion

**Status:** Draft, not yet implemented
**Date:** 2026-11-12

## 1. Goal

Give the template a way to take **one meeting transcript** and digest it into a structured note in the KB. This mirrors the existing YouTube ingestion: an agent, a transcript skill, a staging folder and a template.

The user downloads a transcript from Teams (or any meeting tool that exports `.vtt`), saves it to `_transcripts/` in their KB, and asks Claude to ingest it. **No setup is needed**, the same as YouTube ingestion.

### Design principle: match the existing patterns

Adopters should set this up exactly like the rest of the template. So this feature adds **no new kinds of configuration**: no environment variables, no per-user settings files, no paths outside the repo. Every piece has a counterpart that already exists:

| This feature | Existing pattern it follows |
|---|---|
| `ingest-meeting` agent | `ingest-youtube` agent |
| `meeting-transcript` skill + script | `youtube-transcript` skill + script |
| `99_references/meetings/` + `README.md` + `TEMPLATE_meeting.md` | `99_references/youtube_videos/` + `README.md` + `TEMPLATE_youtube_video.md` |
| `_transcripts/`, an underscore-prefixed operational folder | `_inbox/`, `_archive/` |
| Folder contents gitignored, its README tracked | Machine-local paths already gitignored (`.claude/worktrees/`, `.claude/settings.local.json`) |
| Commit guard hook | `block_commit_on_main.sh` |
| Paths relative to the repo root | The wiki-link rule (full path from the repo root) |

### Non-goals

- Fetching transcripts automatically (no Microsoft Graph, sign-in or scheduler).
- Grouping meetings into series, digests, or a separate reconciliation agent.
- Committing raw transcripts to git.

These are listed in section 9 for later.

## 2. How It Works

```text
1. User downloads the transcript as .vtt (Teams: recording -> Transcript -> Download)
2. User saves it to _transcripts/ in their KB    (contents gitignored)
3. User: "Ingest the meeting transcript _transcripts/<file>"   (or pastes the text)
4. ingest-meeting agent:
     a. parses the file to [HH:MM:SS] Speaker: text
     b. asks for the meeting title and date if the file doesn't state them
     c. reads index.md and the most relevant notes
     d. writes one note to 99_references/meetings/
5. User reviews the note, rebuilds the index, commits on a branch
```

## 3. Components

| YouTube (existing) | Meetings (new) |
|---|---|
| `.claude/agents/ingest-youtube.md` | `.claude/agents/ingest-meeting.md` |
| `.claude/skills/youtube-transcript/` + `scripts/get_transcript.py` | `.claude/skills/meeting-transcript/` + `scripts/parse_transcript.py` |
| `99_references/youtube_videos/` + `README.md` | `99_references/meetings/` + `README.md` |
| `TEMPLATE_youtube_video.md` | `TEMPLATE_meeting.md` |

## 4. Transcript Handling

### 4.1 `_transcripts/`, a gitignored folder in the repo

- **Location:** a top-level `_transcripts/` folder, next to `_inbox/` and `_archive/`.
- **Gitignored contents, tracked README:**

  ```gitignore
  # Raw meeting transcripts: local only, never committed (see _transcripts/README.md)
  _transcripts/*
  !_transcripts/README.md
  ```

  The folder exists in every copy of the template. Its README explains what goes there and that nothing in it is committed, the same way every other folder documents itself.
- **Why not under `_inbox/`:** `_inbox/` belongs to `iterate-raw-note`, and `decompose-inbox-to-concepts` reads every note there.
- **Why not committed, unlike research PDFs:** `research_papers/` commits the raw PDF because papers are public. Meeting transcripts are internal and may contain sensitive data.

### 4.2 Guard against accidental commits

`.gitignore` already blocks ordinary `git add`. However, `git add -f`, or a copy where someone edited `.gitignore`, would get past it. So the template's existing `PreToolUse` hook gets a second check: it blocks a `git commit` when any staged file is under `_transcripts/` other than its `README.md`, and tells the agent to unstage it.

This uses the same hook, the same registration in `.claude/settings.json`, and the same "explain, exit 2" behavior as the block on committing to `main`. Like that rule, it applies to Claude Code sessions. People committing by hand are covered by `.gitignore` and the README.

### 4.3 Handling

- **Kept after ingestion**, so the user (or Claude, on request) can check a cited timestamp against what was actually said. Pruning is up to the user.
- **The note stores a repo-relative path**, `transcript_file: "_transcripts/<file>.vtt"`, so a committed note never contains an absolute path with a username.
- **Parser:** `parse_transcript.py` turns `.vtt` (`<v Speaker>text</v>` cues) into `[HH:MM:SS] Speaker: text` using the standard library only. It prints to stdout and never writes files, like `get_transcript.py`.
- **Formats at launch:** `.vtt` (Teams, Zoom and Webex all export it), plus **pasted text** as a fallback, the same way the YouTube agent accepts a pasted transcript. `.docx` (needed for Google Meet) is deferred.
- **Synced folders:** if the KB itself sits in OneDrive, Dropbox or iCloud, `_transcripts/` syncs with it. That's the same exposure as the rest of the KB, so the README points it out instead of the tool working around it.

## 5. The Meeting Note

### 5.1 Sections

The section names match the YouTube template where the meaning is the same. Every decision, action item and open question carries a `[HH:MM:SS]` citation into the transcript.

| Section | Contents | YouTube equivalent |
|---|---|---|
| **Summary** | One paragraph: purpose, outcome, main decisions | Summary |
| **Decisions** | What was decided, and by whom. Something only discussed is not a decision; if it's unclear, list it as an open question. | (new) |
| **Action Items** | Owner, task, due date if stated. What the user does with them afterwards is up to them. | (new) |
| **Open Questions** | Things raised and left unresolved | (new) |
| **Key Insights** | "How it works" and "why we do it" explanations, with inline full-path wiki-links to existing notes | Key Insights |
| **Notable Timestamps** | Short quotes or paraphrases worth finding again | Notable Quotes / Timestamps |
| **Relevance to Knowledge Base** | What's new, plus **flags for review** from the KB check (section 6) | Relevance to Knowledge Base |
| **Related Concepts** | Wiki-links, per the `CLAUDE.md` convention | (in `CLAUDE.md`) |

Ignored: small talk, scheduling chatter, screen-sharing logistics. No long verbatim passages and never the full transcript.

### 5.2 Frontmatter (`TEMPLATE_meeting.md`)

The keys match the YouTube template where the meaning is the same (`title`, `source_url`, `date_ingested`).

```yaml
---
tags: [reference, meeting, intermediate, your-topic]
title: "[Exact meeting title]"
date_held: YYYY-MM-DD
attendees: ["[Name]"]
source_url: ""                          # optional: recording link
transcript_file: "_transcripts/[file].vtt"   # repo-relative; empty if pasted
date_ingested: YYYY-MM-DD
related: []
summary: "One line on the meeting's main outcome."
status: draft
---
```

The meeting title and date come from the file or the user, **never inferred from the content**. This is the same rule as the YouTube title.

### 5.3 Filename

`snake_case_short_title_YYYY_MM_DD.md`, for example `platform_sync_2026_11_12.md`. Like YouTube, the name is derived from the title. The date goes **at the end** because recurring meetings share a title, and `CLAUDE.md` reserves numeric prefixes for directories.

## 6. Checking Against the KB

A light check. The agent flags issues and never edits other notes.

1. For each decision and open question, find the relevant notes (`index.md`, then read the strongest 3 to 5 in full).
2. Under **Relevance to Knowledge Base**, record a flag when:
   - a **decision conflicts** with an existing note. Example: *"Decided X [00:12:30]; `[[01_concepts/foo]]` says Y."*
   - an **open question is already answered** in the KB. Example: *"Raised [00:20:05]; `[[03_techniques/bar]]` covers this."*
3. If it's unclear whether two things conflict, flag it anyway and say why.

The user decides what to do with each flag.

## 7. Agent Constraints

- Writes only to `99_references/meetings/`. It reads `_transcripts/` and the rest of the vault, and never writes to `_transcripts/`.
- One note per meeting.
- Full-path wiki-links only, and every target must exist.

## 8. Repo Changes

| File | Change |
|---|---|
| `.claude/agents/ingest-meeting.md` | New |
| `.claude/skills/meeting-transcript/SKILL.md` + `scripts/parse_transcript.py` | New |
| `99_references/meetings/README.md`, `TEMPLATE_meeting.md` | New |
| `_transcripts/README.md` | New (the only tracked file in the folder) |
| `.gitignore` | `_transcripts/*` and `!_transcripts/README.md` |
| `.claude/hooks/block_commit_on_main.sh` | Add the staged-transcripts check (section 4.2) |
| `CLAUDE.md` | Section 2: `_transcripts/` under Operational Folders, plus the new agent and skill. Section 4: a classification row. Section 8: mention the hook's second check. |
| `README.md` | Folder table, agent/skill table and a "Using it" line. No new setup step. |
| `ADR.md` | ADR-0004: meeting ingestion; raw transcripts kept in a gitignored folder with a commit guard |

The YouTube framework is unchanged, apart from two fixes to `.claude/skills/youtube-transcript/SKILL.md` that are worth doing anyway:

- Line 10 says `.agents/skills/...` where it should say `.claude/skills/...`.
- Line 43 says to save the transcript as `<video_id>-transcript.txt` when no output file is given. That would put an untracked file in the repo root. It should say the transcript isn't saved unless a path is requested.

After it's built, the ADR and README carry the decisions, and this spec moves to `_archive/`.

### 8.1 Privacy notes for the README

- **Session logs.** Everything Claude reads in a session, including the full transcript, is also kept in Claude Code's local session logs (`~/.claude/projects/`). They are deleted after about 30 days by default; the `cleanupPeriodDays` setting changes that. This applies to YouTube ingestion too.
- **Model provider.** Transcript content is sent to Anthropic during ingestion. Check that your organization's agreement covers meeting content.
- **Your copy's remote.** Meeting notes (summaries, decisions, short excerpts) are committed. If you push your copy to GitHub, check its visibility: a repo made from a public template can still be public.

## 9. Deferred (Possible Later Additions)

- **Automatic fetching** from Microsoft Graph, using delegated sign-in for meetings the user organizes.
- **Meeting series**: detecting recurring meetings, plus a hub note with a running decision log.
- **Index scaling**: an `index: false` flag if meeting volume pushes `index.md` past ADR-0002's limit.
- **Reconciliation**: an agent that works through open flags, and extending the decompose agent to staging folders.
- **The same KB check for YouTube** ingestion.
- **`.docx` input**, for Google Meet and Teams `.docx` downloads.

The full design for these is in the template repo's git history (the commits before the rename to `spec_meeting_transcript_ingest.md`). Adopters who copy the template with a fresh `git init` won't have that history.

## 10. Resolved

| Question | Decision |
|---|---|
| Formats at launch | `.vtt` plus pasted text; `.docx` deferred |
| Transcript retention | Kept after ingestion for verification; pruning is up to the user |
| Where transcripts live | `_transcripts/` in the repo, contents gitignored, guarded by the commit hook. This replaces an earlier outside-the-repo design, which would have added a per-user configuration step that no other part of the template needs. |
