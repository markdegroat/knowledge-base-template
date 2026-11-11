# Spec: Teams Call Ingestion, Meeting Series, and Conflict Handling

**Status:** Draft, not yet implemented
**Date:** 2026-11-11 (revised after design review)

## 1. Context and Goals

This repository is a **knowledge base template**. People clone it and run their own KB **locally**. The tooling (agents, skills, scripts, templates) lives in git; each adopter's notes and transcripts live on their machine. There is no shared multi-user vault.

**Goals:**

1. Digest recorded Microsoft Teams meetings into the KB by reusing the YouTube ingestion framework (agent + transcript skill + staging folder + template).
2. Include a **meeting summary** in every meeting note.
3. **Fetch transcripts automatically** for meetings the user organizes. Meetings they only attend are ingested **manually**: the user uploads the transcript and works through it with Claude.
4. Parse out **decisions, action items and open questions**, each with a timestamp citation so the user (or Claude, on request) can check it against the transcript.
5. **Check flagged items against the KB.** Flag decisions that conflict with existing notes, and open questions the KB already answers, for user review.
6. **Detect meeting series** (recurring or closely related meetings) and recommend grouping them in the KB.
7. Apply the same conflict checking to YouTube ingestion.

**Why not just use the Copilot recap?** A Copilot recap stays inside Teams. This feature links meeting knowledge into the user's KB, checks it against what the KB already says (including earlier meetings), and keeps it in the same place as the rest of their notes.

### Non-goals

- A shared, multi-user vault or deduplication across users.
- Committing raw transcripts or recordings to git.
- Deciding how adopters manage tasks downstream. The tool parses action items into the note; what happens to them next is the adopter's choice.
- Real-time or in-meeting processing.

## 2. Current State (YouTube Framework)

| Piece | Path | Role |
|---|---|---|
| Agent | `.claude/agents/ingest-youtube.md` | Fetches the title and transcript, distills one note per video |
| Skill | `.claude/skills/youtube-transcript/` | `get_transcript.py` pulls captions via `youtube-transcript-api` |
| Staging folder | `99_references/youtube_videos/` | One note per video, created as `status: draft` |
| Template | `99_references/youtube_videos/TEMPLATE_youtube_video.md` | Summary, Key Insights, Timestamps, Relevance |

**Known gaps:**

- The ingest agent reads only `index.md` (one line per note), so it notices overlap but misses claim-level contradictions.
- A conflict is recorded only in the new note's "Relevance" paragraph. The challenged note shows nothing.
- `decompose-inbox-to-concepts` reads only `_inbox/`, so nothing promotes staging-folder notes into the core buckets.
- Enrichment is add-only, so a contradiction is appended next to the original without linking the two.
- `date_published` is recorded but never used.
- Typo: `.claude/skills/youtube-transcript/SKILL.md` line 10 says `.agents/skills/...` where it should say `.claude/skills/...`.

## 3. Ingestion Modes

| | **Auto mode** | **Manual mode** |
|---|---|---|
| Applies to | Meetings the user **organized** | Meetings the user **attended** but didn't organize, or any transcript file |
| Transcript source | Microsoft Graph, fetched on a schedule | The user downloads the `.vtt`/`.docx` from Teams or Stream |
| Trigger | Scheduled task runs `claude -p` | The user asks Claude to ingest the file (interactive session) |
| Review | The user reads the **ingestion digest** (section 7), not every note | The user works through the note with Claude while it's created |

The split matters because auto mode only needs the **organizer's** delegated Graph access, which is the documented, supported path. Reading transcripts of meetings you only attended is not needed.

## 4. Teams Ingestion Components

### 4.1 Components

| YouTube | Teams equivalent |
|---|---|
| `ingest-youtube` agent | `ingest-teams-call` agent |
| `youtube-transcript` skill | `teams-transcript` skill: `parse_teams_transcript.py` |
| `99_references/youtube_videos/` | `99_references/meetings/` (+ series subfolders, section 6) |
| `TEMPLATE_youtube_video.md` | `TEMPLATE_meeting.md`, `TEMPLATE_meeting_series.md` |
| (none) | `scripts/fetch_teams_transcripts.py` (auto mode) |

### 4.2 Transcript handling

- Raw transcripts go in a **gitignored** drop folder: `_inbox/teams_raw/`.
- They are **kept after ingestion**, so the user or Claude can check citations later.
- `parse_teams_transcript.py` normalizes `.vtt` and `.docx` to `[HH:MM:SS] Speaker: text`, matching the YouTube `--timestamps` shape. It uses the standard library, plus `python-docx` for `.docx`.
- Each note's frontmatter records `transcript_file:` (a path in the drop folder) so verification knows where to look.

### 4.3 Metadata rules

- The meeting title and date come from Graph metadata (auto mode) or from the transcript file or the user (manual mode). **Never infer them from the content.**
- Attendees come from the transcript's speaker labels.

### 4.4 What the agent extracts

Each of the following **must carry a timestamp citation** `[HH:MM:SS]` pointing into the transcript:

- **Meeting Summary**: one paragraph covering purpose, outcome and main decisions. This is the summary the user reads.
- **Decisions**: what was decided and by whom. Something that was only discussed is *not* a decision. If it's unclear whether something was decided, record it as an open question.
- **Action Items**: owner, task, due date (if stated). Adopters decide what to do with them downstream.
- **Open Questions**: things raised and left unresolved.
- **Reusable Knowledge**: explanations of how something works or why it's done a certain way, linked inline to existing notes with full-path wiki-links.
- **Flags for Review**: the output of the KB check (section 5).
- **Ignored**: small talk, scheduling chatter, screen-sharing logistics.

### 4.5 Template frontmatter (`TEMPLATE_meeting.md`)

```yaml
---
tags: [reference, meeting, intermediate, your-topic]
meeting_title: "[Exact meeting title]"
date: YYYY-MM-DD
organizer: "[Name]"
attendees: ["[Name]"]
series: ""                    # series slug if grouped (section 6), else empty
meeting_id: ""                # Graph onlineMeeting ID (auto mode); prevents re-ingestion
recording_url: "[Teams/Stream link]"
transcript_file: "_inbox/teams_raw/[file]"
date_ingested: YYYY-MM-DD
related: []
conflicts: []                 # notes whose claims this meeting contradicts
review_status: pending        # pending | reviewed
summary: "One line on the meeting's main outcome."
status: draft
---
```

Body sections: Meeting Summary, Decisions, Action Items, Open Questions, Reusable Knowledge, Flags for Review, Notable Timestamps, Related Concepts.

### 4.6 Agent constraints

- Writes only to `99_references/meetings/` (including series subfolders).
- One note per meeting.
- Short excerpts only, never the full transcript.

## 5. Checking Against the KB

These rules run on every ingestion: meetings, and YouTube videos where they apply.

### 5.1 Process

1. Collect every **decision**, **open question** and notable **claim** from the new source.
2. For each one, run `search-kb`, then read the 3 to 5 most relevant notes **in full**. That includes earlier meetings in the same series, and the series hub note if there is one.
3. Classify each item:

   | Result | Applies to | Flag |
   |---|---|---|
   | **Conflict** | Decision/claim | It contradicts an existing note: *"Decided X [00:12:30]; `[[01_concepts/foo]]` says Y."* |
   | **Supersedes** | Decision | It reverses an earlier meeting's decision: *"Reverses decision in `[[99_references/meetings/...]]`."* |
   | **Answered by KB** | Open question | The KB already has the answer: *"Raised [00:20:05]; `[[03_techniques/bar]]` covers this."* |
   | **Resolves** | Decision | It answers an open question left in an earlier meeting note |
   | **New** | Any | Nothing in the KB covers it. Not flagged; listed as new information. |

4. Write the results to the note's **Flags for Review** section. Each flag cites both sides: the transcript timestamp and the KB note.
5. Add any conflicting notes to the `conflicts:` frontmatter, so `index.md` surfaces the conflict from the new note's side.

### 5.2 Rules

- **Flag, don't resolve.** The agent never edits the challenged note. The user decides.
- **Uncertain counts as a flag.** If the agent can't tell whether two claims conflict, it flags the pair and explains why.
- **State recency.** Mention dates when they matter ("the KB note is from a 2023 video; this meeting is 2026"), but don't treat newer as automatically right.

### 5.3 Resolution

- The user resolves flags interactively: "show me the open flags", "check this decision against the transcript", "update the concept note with this decision".
- When a resolution updates a core note, the core note cites both sources.
- Extend `decompose-inbox-to-concepts`, or add a `reconcile-flags` agent, to also read `99_references/youtube_videos/` and `99_references/meetings/`, so promoting notes and resolving conflicts happen in one pass.

### 5.4 Checking on request

The user can ask Claude to check any item: "did we actually decide X?" Claude opens `transcript_file`, reads around the cited timestamp, and reports exactly what was said. The citations exist so this lookup is fast and anyone can repeat it.

## 6. Meeting Series Grouping

### 6.1 Detection signals

When a meeting is ingested, the agent checks whether it belongs with others:

- **Recurrence**: the Graph `seriesMasterId`, or the same join URL (auto mode). This is the strongest signal.
- **Title stem**: "Weekly Platform Sync", "Platform Sync – Nov 11".
- **Attendee overlap** with existing meeting notes.
- **Topic similarity**: `search-kb` hits concentrated on earlier meeting notes.

### 6.2 Behavior

- The agent **recommends** a grouping. It never reorganizes on its own. In manual mode it asks in the session; in auto mode the recommendation goes in the ingestion digest.
- A recommendation lists the proposed series name, the meetings it would include, and the signals that matched.
- On approval:
  - Create `99_references/meetings/<series_slug>/`.
  - Move the member notes into it and **update all incoming wiki-links** (`CLAUDE.md` refactoring rule).
  - Create a series hub note, `<series_slug>/series_overview.md`, from `TEMPLATE_meeting_series.md`.
  - Set `series:` in each member's frontmatter.
- Once a series exists, future meetings that match it are filed into it directly and the hub note is updated.

### 6.3 Series hub note (`TEMPLATE_meeting_series.md`)

- **Purpose** of the series, and who attends.
- **Running decision log**: a dated list of decisions, linking to each meeting. Superseded decisions are struck through, with a link to the meeting that replaced them.
- **Carried-forward open questions**: still open, or marked resolved with a link to the meeting that resolved them.
- **Meetings**: a list linking to each member note.

The hub is the first note checked in section 5.1 step 2 for a meeting in the series. That's how "conflicts with previous meetings" gets caught reliably.

## 7. Auto Mode

### 7.1 Graph access (delegated, organizer scope)

- The user registers an app (or uses one their organization provides) and signs in with the MSAL **device-code flow**. Tokens are cached locally.
- Permission: `OnlineMeetingTranscript.Read.All` (delegated). This may require admin consent, plus tenant-level Graph access to transcripts. The adopter's IT team decides.
- Fetch flow:

```text
Calendar events organized by the user that ended since the last run
  -> resolve onlineMeeting from joinWebUrl
  -> GET /me/onlineMeetings/{id}/transcripts
  -> GET .../transcripts/{id}/content?$format=text/vtt
  -> save the file to _inbox/teams_raw/
  -> record meeting_id in the local state file (skip if already ingested)
```

- `getAllTranscripts` is not used, because it does not support delegated permissions.

### 7.2 Runtime

- A scheduled task (Windows Task Scheduler, cron or launchd) runs the fetcher, then `claude -p` with `ingest-teams-call` for each new transcript, on a `content/meetings-YYYY-MM-DD` branch. It commits the notes and rebuilds `index.md`.
- It runs under the user's own OS login and Claude Code sign-in. **No API keys in scripts.**
- **Skip rules** in a local config: title keywords, attendee lists or meeting types to exclude.

### 7.3 Ingestion digest

The digest replaces reviewing every note. Each auto-mode run writes `99_references/meetings/_digests/YYYY-MM-DD.md` (excluded from `index.md`), containing:

- Meetings ingested, each with its one-line summary and a link.
- **All flags for review** from the run (conflicts, supersessions, answered questions), with links.
- Series grouping recommendations.
- Action items extracted, grouped by owner.
- Meetings skipped, and why (skip rule, no transcript, already ingested).

The user reads the digest, follows up on the flags that matter, and approves the merge.

## 8. Data Flow and Security

| Data | Where it goes |
|---|---|
| File contents, prompts and tool output in Claude sessions | Anthropic, via the user's own Claude Code sign-in |
| YouTube transcript fetch | YouTube, directly (video ID only) |
| Graph calls (auto mode) | Microsoft 365, under the user's own token |
| Raw transcripts | Local, gitignored drop folder |
| Git push | The user's configured remote, only when the user pushes |

**Adopter guidance (for the README):**

- Confirm that your organization's AI agreement and data policies allow meeting content (which may include customer or regulated data) to be processed by Claude.
- Raw transcripts stay out of git, but if your KB folder is synced (OneDrive, Dropbox, iCloud), the drop folder syncs too. Make sure that location is approved.
- Copying transcript content into notes can outlive your organization's Teams retention policy. Check whether that matters for you.
- Review `.claude/settings.json` for `env` or `apiKeyHelper` entries when pulling template updates. They can redirect Claude Code to a different key or endpoint.

## 9. Implementation Plan

| Phase | Deliverable | Branch |
|---|---|---|
| 0 | Fix the `SKILL.md` path typo | `fix/youtube-skill-path` |
| 1 | KB check + Flags for Review for `ingest-youtube` (section 5) | `chore/conflict-handling` |
| 2 | Manual-mode Teams ingest: agent, parser skill, `TEMPLATE_meeting.md`, folder README, `.gitignore`, `CLAUDE.md` + ADR | `chore/teams-call-ingest` |
| 3 | Series grouping: detection, `TEMPLATE_meeting_series.md`, move + relink | `chore/meeting-series` |
| 4 | Reconciliation: extend the decompose agent's scope, or add `reconcile-flags` | `chore/reconcile-flags` |
| 5 | Auto mode: fetcher, device-code auth, scheduler, skip rules, digest, `build_index.py` excludes `_digests/` | `chore/teams-auto-fetch` |

Phases 1 to 5 are structural changes and each gets an ADR entry.

## 10. Open Questions

1. Support both `.vtt` and `.docx` from day one, or start with `.vtt` (simpler to parse, and what Graph returns)?
2. Series grouping thresholds: how much attendee overlap or title similarity triggers a recommendation?
3. Should the digest also be printed or sent as a notification when a run finishes, or is the file enough?
4. Raw transcript retention: keep them indefinitely for verification, or prune after N days with notes keeping only the citations?

## 11. Resolved Decisions (Design Review, 2026-11-11)

| Question | Decision |
|---|---|
| Why not the Copilot recap? | The value is in linking into the KB, catching conflicts with earlier meetings, and living alongside the KB |
| Where does it live? | Tooling in git as a template; each adopter's KB is local |
| Synced folder for raw transcripts? | Acceptable for the author; adopters get the guidance in section 8 |
| KB topic scope | Left to adopters (`CLAUDE.md` section 1) |
| Too many low-value meetings | Series grouping (section 6) plus skip rules |
| Review burden | Auto mode only for meetings the user organizes, reviewed through the digest; attended meetings are manual and interactive |
| Action items | Always parsed into the note; downstream handling is the adopter's choice |
| Multi-user sharing / dedup / attendee Graph access | Out of scope: local KB per user, organizer-only auto mode |
| Accuracy | The user is responsible; every item cites a timestamp; Claude can check items against the transcript on request |
| Conflict authority | Flag, don't resolve: decisions and open questions are checked against the KB, and conflicts or existing answers go to the user |
