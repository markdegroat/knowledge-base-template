---
name: meeting-transcript
description: Parse a meeting transcript exported as WebVTT (.vtt, from Teams, Zoom or Webex) into readable `[HH:MM:SS] Speaker: text` lines. Use when the user points at a .vtt file, usually under _transcripts/, or asks to read or ingest a meeting transcript.
---

# Meeting Transcript

Turn a `.vtt` meeting transcript into `[HH:MM:SS] Speaker: text` lines, one per speaker turn. Standard library only, so it needs no setup.

## Usage

Run from the repo root:

```bash
uv run .claude/skills/meeting-transcript/scripts/parse_transcript.py "_transcripts/<file>.vtt"
```

By default, consecutive cues from the same speaker are merged into one line that keeps the first cue's timestamp. Teams splits speech into many short cues, so merging makes the output much shorter. Add `--no-merge` to get one line per cue.

## Supported Input

- **Teams**: `<v Speaker Name>text</v>` cues (Teams recording, then Transcript, then Download as `.vtt`)
- **Zoom / Webex**: cue text in the form `Speaker Name: text`
- Cues with no speaker are printed as `[HH:MM:SS] text`

Not supported: `.docx` downloads (Google Meet, some Teams exports). Ask the user for a `.vtt` file, or have them paste the text into the chat.

## Output

- CRITICAL: YOU MUST NEVER MODIFY THE RETURNED TRANSCRIPT. Cite its timestamps as they are.
- The script prints to stdout and never writes files. Do not save the parsed transcript anywhere unless the user asks for a specific path.
- Exits with status 1 and a message on stderr if the file is missing, isn't WebVTT, or has no cues.

## Notes

- Raw transcripts belong in `_transcripts/`. That folder's contents are gitignored and must never be committed (see `_transcripts/README.md`).
