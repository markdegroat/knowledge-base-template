---
tags: [reference, fundamentals, knowledge-management]
related: []
summary: "Folder guide for meeting notes: one auto-generated note per meeting transcript, with cited decisions, action items, open questions and KB conflict flags."
status: draft
---

# Meeting Notes

Distilled notes from meeting transcripts.

## Purpose

Meetings are where many decisions are made and much "why we do it this way" knowledge is explained out loud, then lost. This folder captures that in a form that can be checked against the rest of the vault and later decomposed into the core buckets.

## How Notes Get Here

1. Download the meeting transcript as `.vtt` (Teams: open the recording, then Transcript, then Download; Zoom and Webex also export `.vtt`).
2. Save it to `_transcripts/` at the repo root. Nothing in that folder is committed (see `_transcripts/README.md`).
3. Ask Claude: "Use ingest-meeting on `_transcripts/<file>.vtt`", or paste the transcript into the chat.

The **Ingest Meeting** agent then:
1. Parses the transcript with the `meeting-transcript` skill
2. Asks for the meeting title and date if the filename doesn't make them clear
3. Extracts decisions, action items, open questions and key insights, each cited by `[HH:MM:SS]`
4. Checks decisions and open questions against existing notes and **flags** conflicts (it never edits other notes)
5. Saves the result here using `TEMPLATE_meeting.md`

## This Is a Staging Area

These notes are **machine-generated summaries**. Check the decisions and action items against the transcript before relying on them; the timestamps make that quick. Each meeting gets exactly one note. Acting on the flags and curating insights into the core buckets are separate, human-directed steps.

## File Naming

`snake_case_short_title_YYYY_MM_DD.md`, for example `platform_sync_2026_11_12.md`. The date held goes at the end because recurring meetings share a title.

## Status Flow

1. **Created** by the ingest agent: `status: draft`
2. **Reviewed** by a person against the transcript
3. **Decomposed** into core-bucket notes where useful: then move to `_archive/` or keep as a reference
