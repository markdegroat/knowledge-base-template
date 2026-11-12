# Spec: Meeting Transcript Ingestion

**Status:** Draft, not yet implemented
**Date:** 2026-11-12

## 1. Goal

Give the template a way to take **one meeting transcript** and digest it into a structured note in the KB. This mirrors the existing YouTube ingestion: an agent, a transcript skill, a staging folder and a template.

The user downloads a transcript from Teams (or any meeting tool that exports `.vtt`), saves it to a transcripts folder **outside the repo**, and asks Claude to ingest it.

### Non-goals

- Fetching transcripts automatically (no Microsoft Graph, sign-in or scheduler).
- Grouping meetings into series, digests, or a separate reconciliation agent.
- Committing raw transcripts to git.

These are listed in section 9 for later.

## 2. How It Works

```text
1. User downloads the transcript as .vtt (Teams: recording -> Transcript -> Download)
2. User saves it to their transcripts folder ($KB_TRANSCRIPTS_DIR, outside the repo)
3. User: "Ingest the meeting transcript <file>"   (or pastes the transcript text)
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
| `.claude/skills/youtube-transcript/` + `get_transcript.py` | `.claude/skills/meeting-transcript/` + `parse_transcript.py` |
| `99_references/youtube_videos/` + `README.md` | `99_references/meetings/` + `README.md` |
| `TEMPLATE_youtube_video.md` | `TEMPLATE_meeting.md` |

## 4. Transcript Handling

### 4.1 Transcripts live outside the repo

Raw transcripts are stored in a folder **outside the KB repo**, so they can't be committed by accident, can't leak through a push, and aren't read by the vault's other agents. This is a deliberate difference from `research_papers/`, which commits the raw PDF: meeting transcripts are internal and may contain sensitive data.

**Why outside the repo, not a gitignored folder inside it:** adopters **copy** the template (fresh `git init`, a clone, or a GitHub template repository). They don't fork it, so they won't receive fixes from upstream. A gitignored folder inside the repo is only safe as long as every copy keeps that `.gitignore` line. A folder outside the repo stays safe whatever the adopter does to their copy.

### 4.2 Configuring the location (per user, never committed)

Each user sets the path in `.claude/settings.local.json`. That file is already gitignored, is per-user, and Claude Code applies it without the workspace-trust step:

```json
{
  "env": {
    "KB_TRANSCRIPTS_DIR": "C:/Users/<you>/AppData/Local/kb-transcripts/<kb-name>"
  },
  "permissions": {
    "additionalDirectories": ["C:/Users/<you>/AppData/Local/kb-transcripts/<kb-name>"]
  }
}
```

- `env.KB_TRANSCRIPTS_DIR` is the one setting the parser script and the agent read.
- `permissions.additionalDirectories` lets Claude read files in that folder without asking each time. It grants file access only; nothing in that folder is loaded as configuration.
- The template ships `.claude/settings.local.example.json` with these two keys and placeholder paths. Claude Code doesn't load that file; users copy it to `settings.local.json`.
- **If it's not set**, the agent asks for the transcript's full path, or accepts pasted text. Ingestion works without any configuration; the folder is a convenience.

### 4.3 Recommended default location

Pick somewhere that is **not cloud-synced**, with one subfolder per KB (in case someone keeps several):

| OS | Suggested path |
|---|---|
| Windows | `%LOCALAPPDATA%\kb-transcripts\<kb-name>` |
| macOS | `~/Library/Application Support/kb-transcripts/<kb-name>` |
| Linux | `~/.local/share/kb-transcripts/<kb-name>` |

On Windows, avoid `Documents` and `Desktop`. Corporate machines often redirect them to OneDrive (Known Folder Move), so the transcripts would sync without you noticing. Use an organization-approved location if your policy requires one.

### 4.4 Handling

- **Kept after ingestion**, so the user (or Claude, on request) can check a cited timestamp against what was actually said. Pruning is up to the user.
- **The note stores a relative path.** `transcript_file:` is relative to `KB_TRANSCRIPTS_DIR`, so a committed note never contains an absolute path with a username, and it still resolves on another machine.
- **Parser:** `parse_transcript.py` turns `.vtt` (`<v Speaker>text</v>` cues) into `[HH:MM:SS] Speaker: text` using the standard library only. It accepts an absolute path, or a path relative to `KB_TRANSCRIPTS_DIR`.
- **Formats at launch:** `.vtt` (Teams, Zoom and Webex all export it), plus **pasted text** as a fallback, the same way the YouTube agent accepts a pasted transcript. `.docx` (needed for Google Meet) is deferred.

## 5. The Meeting Note

### 5.1 Sections

Every decision, action item and open question carries a `[HH:MM:SS]` citation into the transcript.

| Section | Contents |
|---|---|
| **Meeting Summary** | One paragraph: purpose, outcome, main decisions |
| **Decisions** | What was decided, and by whom. Something only discussed is not a decision; if it's unclear, list it as an open question. |
| **Action Items** | Owner, task, due date if stated. What the user does with them afterwards is up to them. |
| **Open Questions** | Things raised and left unresolved |
| **Reusable Knowledge** | "How it works" and "why we do it" explanations, with inline full-path wiki-links to existing notes |
| **Flags for Review** | Results of the KB check (section 6) |
| **Related Concepts** | Wiki-links, per the template convention |

Ignored: small talk, scheduling chatter, screen-sharing logistics. No long verbatim passages and never the full transcript.

### 5.2 Frontmatter (`TEMPLATE_meeting.md`)

```yaml
---
tags: [reference, meeting, intermediate, your-topic]
meeting_title: "[Exact meeting title]"
date: YYYY-MM-DD
attendees: ["[Name]"]
recording_url: ""                       # optional
transcript_file: "[file].vtt"            # relative to KB_TRANSCRIPTS_DIR; empty if pasted
date_ingested: YYYY-MM-DD
related: []
summary: "One line on the meeting's main outcome."
status: draft
---
```

The meeting title and date come from the file or the user, **never inferred from the content**. This is the same rule as the YouTube title.

## 6. Checking Against the KB

A light check. The agent flags issues and never edits other notes.

1. For each decision and open question, find the relevant notes (`index.md`, then read the strongest 3 to 5 in full).
2. Record a flag in **Flags for Review** when:
   - a **decision conflicts** with an existing note. Example: *"Decided X [00:12:30]; `[[01_concepts/foo]]` says Y."*
   - an **open question is already answered** in the KB. Example: *"Raised [00:20:05]; `[[03_techniques/bar]]` covers this."*
3. If it's unclear whether two things conflict, flag it anyway and say why.

The user decides what to do with each flag.

## 7. Agent Constraints

- Writes only to `99_references/meetings/`. It reads the transcripts folder and the rest of the vault, and never writes to the transcripts folder.
- One note per meeting. The filename is `YYYY-MM-DD_short_title.md` (snake_case).
- Full-path wiki-links only, and every target must exist.

## 8. Repo Changes

| File | Change |
|---|---|
| `.claude/agents/ingest-meeting.md` | New |
| `.claude/skills/meeting-transcript/SKILL.md` + `scripts/parse_transcript.py` | New |
| `99_references/meetings/README.md`, `TEMPLATE_meeting.md` | New |
| `.claude/settings.local.example.json` | New: placeholder `KB_TRANSCRIPTS_DIR` + `additionalDirectories` |
| `CLAUDE.md` | Sections 2 and 4: new folder, agent and skill; a row in the classification table |
| `README.md` | Agent/skill table, a "Using it" line, and a setup step ("set your transcripts folder") |
| `ADR.md` | ADR-0004: meeting ingestion; raw transcripts kept outside the repo, configured per user |

The YouTube framework is unchanged, apart from two fixes to `.claude/skills/youtube-transcript/SKILL.md` that are worth doing anyway:

- Line 10 says `.agents/skills/...` where it should say `.claude/skills/...`.
- Line 43 says to save the transcript as `<video_id>-transcript.txt` when no output file is given. That would put an untracked file in the repo root. It should say the transcript isn't saved unless a path is requested.

### 8.1 Privacy notes for the README

- **Session logs.** Everything Claude reads in a session, including the full transcript, is also kept in Claude Code's local session logs (`~/.claude/projects/`). They are deleted after about 30 days by default; the `cleanupPeriodDays` setting changes that. This applies to YouTube ingestion too.
- **Model provider.** Transcript content is sent to Anthropic during ingestion. Check that your organization's agreement covers meeting content.
- **Your copy's remote.** Meeting notes (summaries, decisions, short excerpts) are committed. If you push your copy to GitHub, check its visibility: a repo made from a public template can still be public.

After it's built, the ADR and README carry the decisions, and this spec moves to `_archive/`.

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
| Where transcripts live | Outside the repo, in a per-user folder set in `.claude/settings.local.json` (section 4) |
