# Spec: Teams Call Ingestion and Cross-Source Conflict Handling

**Status:** Draft, not yet implemented
**Date:** 2026-11-11

## 1. Goals

1. Digest recorded Microsoft Teams meetings into the knowledge base, reusing the YouTube ingestion framework (agent + transcript skill + staging folder + template).
2. Produce a **meeting summary** as part of every meeting note.
3. Optionally fetch transcripts **automatically** for every meeting the signed-in user can access, with each user authenticating as themselves.
4. Detect and track **conflicting or new information** across ingested sources (YouTube videos and meetings), and reconcile it into the core buckets under human control.

### Non-goals

- Storing raw transcripts or recordings in git.
- Real-time or in-meeting processing.
- Merging anything to `main` without human review.

## 2. Current State (YouTube Framework)

| Piece | Path | Role |
|---|---|---|
| Agent | `.claude/agents/ingest-youtube.md` | Fetches title + transcript, distills one note per video |
| Skill | `.claude/skills/youtube-transcript/` | `get_transcript.py` pulls captions via `youtube-transcript-api` |
| Staging folder | `99_references/youtube_videos/` | Holds one note per video, created as `status: draft` |
| Template | `99_references/youtube_videos/TEMPLATE_youtube_video.md` | Summary, Key Insights, Timestamps, Relevance |

**Known gaps:**

- The ingest agent reads only `index.md` (one line per note), so it notices that topics overlap but misses claim-level contradictions.
- A conflict is recorded only in the *new* note's "Relevance" paragraph. The older, challenged note shows nothing.
- `decompose-inbox-to-concepts` reads only `_inbox/`, so nothing automated promotes staging-folder notes into the core buckets.
- Enrichment rules are add-only ("do not restructure or rewrite existing content"), so a contradiction gets appended next to the original without linking the two.
- `date_published` is recorded but never used to judge recency.
- Minor fix: `.claude/skills/youtube-transcript/SKILL.md` line 10 says `.agents/skills/...` where it should say `.claude/skills/...`.

## 3. Teams Call Ingestion (Manual Mode)

### 3.1 Components

| YouTube | Teams equivalent |
|---|---|
| `ingest-youtube` agent | `ingest-teams-call` agent |
| `youtube-transcript` skill | `teams-transcript` skill: `parse_teams_transcript.py` |
| `99_references/youtube_videos/` | `99_references/meetings/` + `README.md` |
| `TEMPLATE_youtube_video.md` | `TEMPLATE_meeting.md` |

### 3.2 Input

- The user downloads the transcript from the recording in Teams or Stream (**Transcript → Download**), as `.vtt` or `.docx`.
- The file goes in a **gitignored** drop folder: `_inbox/teams_raw/`.
- `parse_teams_transcript.py` normalizes either format to `[MM:SS] Speaker: text`, the same shape as the YouTube script's `--timestamps` output. It uses the standard library only (plus `python-docx` for `.docx`).

### 3.3 Metadata rules

- Meeting title and date come from the transcript file's metadata or from the user. **Never infer them from the content.** This is the same rule as the YouTube title.
- Attendees come from the transcript's speaker labels and are listed by role where possible (see section 6).

### 3.4 What the agent extracts

- **Meeting Summary**: one paragraph covering purpose, outcome and main decisions.
- **Decisions**, with timestamps.
- **Action Items**: owner and due date.
- **Open Questions and Risks**.
- **Reusable Knowledge**: "how it works" and "why we do it this way" explanations, linked inline to existing notes with full-path wiki-links.
- **Agreements, Conflicts & New Information**: see section 5.
- **Ignored**: small talk, scheduling chatter, screen-sharing logistics.

### 3.5 Template frontmatter (`TEMPLATE_meeting.md`)

```yaml
---
tags: [reference, meeting, intermediate, your-topic]
meeting_title: "[Exact meeting title]"
date: YYYY-MM-DD
attendees: ["[Role or name]"]
recording_url: "[SharePoint/Stream link]"
date_ingested: YYYY-MM-DD
sensitivity: internal        # internal | confidential
related: []
conflicts: []                # notes this meeting contradicts or supersedes
summary: "One line on the meeting's main outcome for this knowledge base."
status: draft
---
```

Body sections: Meeting Summary, Decisions, Action Items, Open Questions & Risks, Reusable Knowledge, Agreements/Conflicts/New Information, Notable Timestamps, Related Concepts.

### 3.6 Agent constraints

- Writes only to `99_references/meetings/`.
- One note per meeting.
- No long verbatim passages and never the full transcript.
- Leaves out names, customer details and personal or health data unless strictly needed.

## 4. Automatic Fetching (Phase 2)

### 4.1 Approach: delegated Microsoft Graph access

Each user signs in as themselves, so the tool can never read more than that user already can.

| | Delegated (chosen) | Application (fallback) |
|---|---|---|
| Scope | What the signed-in user can access | Transcripts across the whole tenant |
| Setup | App registration + one-time admin consent; each user signs in | Admin consent + an application access policy set by IT |
| Fit for "meetings I'm in" | Natural fit | Overkill; the script has to filter to the user's meetings itself |

### 4.2 Fetch flow

```
Calendar events (online meetings that ended since the last run)
  -> resolve onlineMeeting from joinWebUrl
  -> GET /onlineMeetings/{id}/transcripts
  -> GET /transcripts/{id}/content?$format=text/vtt
  -> write the file to _inbox/teams_raw/
  -> record the meeting ID in a local state file, so nothing is ingested twice
```

- **Permission:** `OnlineMeetingTranscript.Read.All` (delegated). Requires admin consent, and requires the tenant to enable Graph access to transcripts.
- **Not usable:** `getAllTranscripts` covers only meetings the user organized, and it does not support delegated permissions.

### 4.3 Open question (blocking)

It is unconfirmed whether delegated access returns transcripts for meetings the user **attended but did not organize**.

**Spike:** sign in, take one past meeting organized by someone else, and attempt the transcript download.

- If it works, delegated access covers the goal.
- If it doesn't, delegated access covers only organized meetings. The rest would need the application route, or organizers running the tool themselves.

### 4.4 Runtime

- **Auth:** MSAL device-code flow (the user enters a code at microsoft.com/devicelogin). Tokens are cached locally and refresh silently.
- **Scheduler:** Windows Task Scheduler, nightly or hourly. It runs locally rather than in the cloud because the token cache lives on the laptop. Polling on a schedule avoids webhooks, which would need a public HTTPS endpoint.
- **Ingestion:** for each new transcript, run `claude -p` with the `ingest-teams-call` agent on a `content/meetings-YYYY-MM-DD` branch, then commit the notes and rebuild `index.md`.
- **Review gate:** merging to `main` requires human approval (`CLAUDE.md` section 8).
- **Skip rules:** configurable exclusions by title keyword, attendee list, or meeting type (1:1s, HR, customer calls).

### 4.5 Alternative to evaluate

The claude.ai Microsoft 365 connector may already be able to reach transcripts. It needs to be authorized before this can be checked, and if it works it could replace the custom fetcher.

## 5. Conflict and New-Information Handling

These rules apply to every ingest agent (YouTube and Teams).

1. **Claim-level comparison at ingest.** Run `search-kb`, read the 3 to 5 most relevant notes in full, and fill a new **"Agreements, Conflicts & New Information"** section. Example entry: *"Claims X (at [12:30]); [[01_concepts/foo]] says Y. Disagrees / is newer / is more specific."*
2. **Mark the challenged note.** Add a `conflicts:` frontmatter list and/or a `contested` tag to the new note. The index surfaces it, so the conflict can be found from either side.
3. **Reconciliation step.** Either extend `decompose-inbox-to-concepts` to also read `99_references/youtube_videos/` and `99_references/meetings/`, or add a separate `reconcile-conflicts` agent. For each conflict it presents both claims, their sources and dates, and a recommendation. The user decides. The resolved core note cites both sources.
4. **Recency is a factor, not a rule.** Consider `date_published` or the meeting `date`, and say so when it's used.
5. **Meetings supersede each other.** When a decision is reversed, the new meeting note records "supersedes the decision in [[99_references/meetings/...]]" explicitly.

## 6. Data Flow and Security

| Data | Where it goes | Notes |
|---|---|---|
| File contents Claude reads, prompts, tool outputs | Anthropic API (the model provider behind Claude Code) | Covered by the organization's agreement with Anthropic |
| YouTube transcript fetch | YouTube, directly from the laptop | Only the video ID is sent |
| Web searches / page fetches | Search provider / target site, via Claude Code tools | Query text only |
| Graph calls (Phase 2) | Microsoft 365, under the user's own token | Stays inside the Microsoft tenant |
| Meeting transcripts during ingestion | Anthropic API, for summarization | Requires confirming the agreement covers this data class (see below) |
| Git push | The configured remote | Only when a push is explicitly approved |

**Requirements before automatic ingestion:**

- Confirm with IT/security which Anthropic agreement covers Claude Code use: data retention, training use, and whether zero-data-retention applies.
- Confirm that meeting content, which may include PHI or customer data, is approved for processing under that agreement.
- Keep raw transcripts out of git, and keep the remote private and internal.
- Inform regular meeting partners that meeting content is digested into a knowledge base.

## 7. Implementation Plan

| Phase | Deliverable | Branch |
|---|---|---|
| 0 | Fix the `SKILL.md` path typo | `fix/youtube-skill-path` |
| 1 | Conflict handling in `ingest-youtube` + template section + `conflicts:` field | `chore/conflict-handling` |
| 2 | Manual Teams ingest: agent, parser skill, template, folder, `.gitignore`, `CLAUDE.md` + ADR | `chore/teams-call-ingest` |
| 3 | Reconciliation agent, or extend the decompose agent's scope | `chore/reconcile-conflicts` |
| 4 | Graph spike (attendee access) | `chore/graph-transcript-spike` |
| 5 | Automated fetcher + scheduler + skip rules | `chore/teams-auto-fetch` |

Phases 1, 2, 3 and 5 are structural changes and each gets an ADR entry.

## 8. Open Questions

1. Which transcript format is used most: `.vtt` or `.docx`?
2. Are action items tracked in the note, or only knowledge?
3. Is attendee (non-organizer) transcript access possible with delegated Graph access? (Spike, phase 4.)
4. Which Anthropic agreement covers this use, and is meeting content approved under it?
5. Where should this fork live (an internal HCHB GitHub org vs. a personal account), and with what visibility?
