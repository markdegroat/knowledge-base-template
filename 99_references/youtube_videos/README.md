---
tags: [reference, fundamentals, knowledge-management]
related: []
summary: "Folder guide for the YouTube digests staging area: one auto-generated note per video, later reviewed and decomposed into the core buckets."
status: draft
---

# YouTube Video Digests

Distilled notes from YouTube videos on this knowledge base's topic.

## Purpose

Video creators produce a lot of useful material. This folder captures it in a form that can be curated and later decomposed into the core buckets.

## How Notes Get Here

The **Ingest YouTube Video** agent:
1. Takes a YouTube URL (it fetches the transcript with the `youtube-transcript` skill) or a pasted transcript
2. Distills the knowledge relevant to this knowledge base's scope
3. Adds inline full-path wiki-links to existing notes where the content overlaps
4. Saves the result here using `TEMPLATE_youtube_video.md`

## This Is a Staging Area

These notes are **machine-generated summaries**, noisier and less curated than the core buckets. Expect duplication across videos, conflicting claims, and varying quality. That is intentional: each video gets exactly one note, and curation into the core buckets is a separate, human-directed step.

## File Naming

`snake_case_short_title.md`, derived from the video title and kept short.

## Status Flow

1. **Created** by the ingest agent: `status: draft`
2. **Reviewed** by a person (optional)
3. **Decomposed** into core-bucket notes: move to `_archive/` or keep as a reference
