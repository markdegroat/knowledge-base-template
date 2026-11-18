#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Parse a meeting transcript (.vtt) into `[HH:MM:SS] Speaker: text` lines.

Handles the WebVTT exports of Teams (`<v Speaker>text</v>` cues), Zoom and Webex
(`Speaker: text` cue text). Consecutive cues from the same speaker are merged into one
line that keeps the first cue's timestamp, unless --no-merge is given.

Standard library only. Prints to stdout and never writes files.

Usage:
    uv run .claude/skills/meeting-transcript/scripts/parse_transcript.py <file.vtt> [--no-merge]
"""

import argparse
import html
import re
import sys

TIMING_RE = re.compile(
    r"^\s*((?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\s+-->\s+((?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)"
)
VOICE_RE = re.compile(r"<v(?:\.[^\s>]*)?\s+([^>]+)>", re.IGNORECASE)
TAG_RE = re.compile(r"</?[^>]+>")
# Zoom/Webex style: "Speaker Name: text". Keep the name short to avoid matching sentences.
PREFIX_SPEAKER_RE = re.compile(r"^([^:\n]{1,60}?):\s+(.*)$", re.DOTALL)


def to_hms(stamp: str) -> str:
    """Normalize a VTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to HH:MM:SS."""
    stamp = stamp.replace(",", ".").split(".")[0]
    parts = [int(p) for p in stamp.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_cues(text: str):
    """Yield (timestamp, speaker, text) for each cue in a WebVTT document."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    if not text.lstrip().startswith("WEBVTT"):
        raise ValueError("not a WebVTT file (missing 'WEBVTT' header)")

    for block in re.split(r"\n\s*\n", text):
        lines = [ln for ln in block.split("\n") if ln.strip()]
        timing_idx = next((i for i, ln in enumerate(lines) if TIMING_RE.match(ln)), None)
        if timing_idx is None:
            continue  # header, NOTE, STYLE or REGION block
        start = to_hms(TIMING_RE.match(lines[timing_idx]).group(1))
        raw = "\n".join(lines[timing_idx + 1:])
        if not raw.strip():
            continue

        speaker = ""
        voice = VOICE_RE.search(raw)
        if voice:
            speaker = voice.group(1).strip()
        body = html.unescape(TAG_RE.sub("", raw))
        body = " ".join(body.split())
        if not speaker:
            m = PREFIX_SPEAKER_RE.match(body)
            if m:
                speaker, body = m.group(1).strip(), m.group(2).strip()
        if body:
            yield start, speaker, body


def format_lines(cues, merge: bool = True):
    out = []  # list of [timestamp, speaker, text]
    for start, speaker, body in cues:
        if merge and out and out[-1][1] == speaker:
            out[-1][2] += " " + body
        else:
            out.append([start, speaker, body])
    return [f"[{t}] {s}: {b}" if s else f"[{t}] {b}" for t, s, b in out]


def main():
    parser = argparse.ArgumentParser(description="Parse a .vtt meeting transcript")
    parser.add_argument("file", help="Path to the .vtt transcript (e.g. _transcripts/<file>.vtt)")
    parser.add_argument("--no-merge", action="store_true",
                        help="Keep one line per cue instead of merging a speaker's consecutive cues")
    args = parser.parse_args()

    # Speaker names often contain non-ASCII characters; Windows consoles default to cp1252.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        with open(args.file, encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
        lines = format_lines(parse_cues(text), merge=not args.no_merge)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not lines:
        print("Error: no cues found in the transcript", file=sys.stderr)
        sys.exit(1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
