# Spec: Meeting Transcript Ingestion

**Status:** Draft, not yet implemented
**Date:** 2026-11-12

## 1. Goal

Give the template a way to take **one meeting transcript** and digest it into a structured note in the KB. This mirrors the existing YouTube ingestion: an agent, a transcript skill, a staging folder and a template.

The user downloads a transcript from Teams (or any meeting tool that exports `.vtt` or `.docx`), drops it in a folder, and asks Claude to ingest it.

### Non-goals

- Fetching transcripts automatically (no Microsoft Graph, sign-in or scheduler).
- Grouping meetings into series, digests, or a separate reconciliation agent.
- Committing raw transcripts to git.

These are listed in section 9 for later.

## 2. How It Works

```text
1. User downloads the transcript (Teams: recording -> Transcript -> Download)
2. User saves it to _transcripts/            (gitignored)
3. User: "Ingest the meeting transcript _transcripts/<file>"
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

- **Location:** `_transcripts/` at the repo root, added to `.gitignore`.
  - It sits outside `_inbox/` because the inbox agents read every note there.
  - Raw sources stay out of git on purpose: unlike the research PDFs in `research_papers/`, meeting transcripts are internal and may contain sensitive data.
- **Kept after ingestion**, so the user (or Claude, on request) can check a cited timestamp against what was actually said.
- **Parser:** `parse_transcript.py` turns `.vtt` (`<v Speaker>text</v>` cues) and `.docx` (speaker + time lines) into `[HH:MM:SS] Speaker: text`. It uses the standard library for `.vtt` and `python-docx` for `.docx`, declared inline (PEP 723) so `uv run` installs it, like `build_index.py` does.

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
transcript_file: "_transcripts/[file]"
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

- Writes only to `99_references/meetings/`. It reads `_transcripts/` and the rest of the vault.
- One note per meeting. The filename is `YYYY-MM-DD_short_title.md` (snake_case).
- Full-path wiki-links only, and every target must exist.

## 8. Repo Changes

| File | Change |
|---|---|
| `.claude/agents/ingest-meeting.md` | New |
| `.claude/skills/meeting-transcript/SKILL.md` + `scripts/parse_transcript.py` | New |
| `99_references/meetings/README.md`, `TEMPLATE_meeting.md` | New |
| `.gitignore` | Add `_transcripts/` |
| `CLAUDE.md` | Sections 2 and 4: new folder, agent and skill; a row in the classification table |
| `README.md` | Agent/skill table and a "Using it" line |
| `ADR.md` | ADR-0004: meeting ingestion; raw transcripts kept out of git |

The YouTube framework is unchanged, apart from one typo fix that's worth doing anyway: in `.claude/skills/youtube-transcript/SKILL.md`, line 10 says `.agents/skills/...` where it should say `.claude/skills/...`.

After it's built, the ADR and README carry the decisions, and this spec moves to `_archive/`.

## 9. Deferred (Possible Later Additions)

- **Automatic fetching** from Microsoft Graph, using delegated sign-in for meetings the user organizes.
- **Meeting series**: detecting recurring meetings, plus a hub note with a running decision log.
- **Index scaling**: an `index: false` flag if meeting volume pushes `index.md` past ADR-0002's limit.
- **Reconciliation**: an agent that works through open flags, and extending the decompose agent to staging folders.
- **The same KB check for YouTube** ingestion.

The full design for these is in this file's git history (commits before the rename to `spec_meeting_transcript_ingest.md`).

## 10. Open Questions

1. Support `.docx` at launch, or `.vtt` only?
2. Keep raw transcripts indefinitely, or leave pruning to the user?
