#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Build index.md - the vault's Map of Content for subagent-mediated retrieval.

Scans the core buckets, reads each note's frontmatter (tags, status, optional summary)
and title, and emits a single `index.md` grouped by bucket. The index is a derived,
disposable artifact: rerun this to rebuild it from the notes, which are the source of truth.

Frontmatter is parsed with PyYAML, declared as an inline (PEP-723) dependency, so:

    uv run scripts/build_index.py        # auto-provisions PyYAML, writes ./index.md

(Running under bare `python3` works only if PyYAML is already importable.)
See `ADR.md` (ADR-0002) for why this exists instead of an embedding or graph-server layer.
"""

from __future__ import annotations

import os
import re
import sys

try:
    import yaml
except ModuleNotFoundError:
    sys.stderr.write(
        "PyYAML is required. Run via:  uv run scripts/build_index.py\n"
        "(or install PyYAML into the active environment).\n"
    )
    sys.exit(1)

# Buckets scanned, in display order. 99_references is walked recursively (it has subdirs).
BUCKETS = ["01_concepts", "02_patterns", "03_techniques", "04_workflows", "99_references"]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(REPO_ROOT, "index.md")

SUMMARY_MAX = 160  # chars


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body).

    frontmatter_dict is {} when there is no frontmatter, or **None** when a frontmatter
    block exists but fails to parse (so the caller can warn + fall back to body extraction).
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end]
    body = text[end + 4 :]
    try:
        fm = yaml.safe_load(block)
    except yaml.YAMLError:
        return None, body
    if not isinstance(fm, dict):
        fm = {}
    return fm, body


def norm_tags(raw) -> list[str]:
    """Normalise a frontmatter `tags` value (YAML list, or a comma string) to a clean list."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.strip().lstrip("[").rstrip("]")
        return [t.strip().strip("'\"") for t in raw.split(",") if t.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(t).strip() for t in raw if str(t).strip()]
    return [str(raw).strip()]


def clean_summary(s: str) -> str:
    """Strip markdown emphasis/links, collapse whitespace, take the first sentence, truncate."""
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]*)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]*)\*", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    # First sentence if it ends cleanly and isn't trivially short; else keep the run.
    m = re.match(r"^(.*?[.!?])(?:\s|$)", s)
    if m and len(m.group(1)) >= 30:
        s = m.group(1)
    if len(s) > SUMMARY_MAX:
        # Truncate on a word boundary, never mid-word.
        s = s[:SUMMARY_MAX].rsplit(" ", 1)[0].rstrip(",;:- ") + "…"
    return s


def derive(text: str) -> tuple[str, list[str], str, str, bool]:
    """Return (title, tags, status, summary, parse_failed) for a note's raw text."""
    fm, body = split_frontmatter(text)
    parse_failed = fm is None
    fm = fm or {}

    tags = norm_tags(fm.get("tags"))
    status = str(fm.get("status")).strip() if fm.get("status") else ""
    summary = str(fm.get("summary")).strip() if fm.get("summary") else ""

    title = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if not title:
                title = stripped.lstrip("#").strip()
            continue  # headings never become the summary
        if stripped.startswith((">", "<!--", "![", "|", "```", "---")):
            continue  # skip blockquotes/callouts, comments, images, tables, fences, rules
        if not summary:
            summary = clean_summary(stripped)
        if title and summary:
            break

    return title, tags, status, summary, parse_failed


def collect(bucket: str) -> list[tuple[str, str, list[str], str, str]]:
    """Walk a bucket; return sorted (relpath, title, tags, status, summary), skipping templates."""
    rows = []
    for dirpath, _dirs, files in os.walk(os.path.join(REPO_ROOT, bucket)):
        for name in files:
            if not name.endswith(".md") or name.startswith("TEMPLATE"):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, REPO_ROOT).replace(os.sep, "/")
            try:
                text = open(full, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError) as e:
                sys.stderr.write(f"WARN: skipping unreadable {rel}: {e}\n")
                continue
            title, tags, status, summary, failed = derive(text)
            if failed:
                sys.stderr.write(
                    f"WARN: frontmatter failed to parse for {rel}; using body-only extraction\n"
                )
            rows.append((rel, title or name[:-3], tags, status, summary))
    rows.sort(key=lambda r: r[0])
    return rows


def main() -> int:
    lines: list[str] = [
        "---",
        "tags: [reference, index]",
        "status: generated",
        "---",
        "",
        "# Vault Map of Content (index)",
        "",
        "> **Generated file - do not edit by hand.** Rebuild with `uv run scripts/build_index.py`. "
        "This is the vault's Map of Content: one line per note (path, summary, status, tags). The "
        "`search-kb` skill loads this to select relevant notes by meaning before reading them. The "
        "notes are the source of truth; this index is a derived, rebuildable artifact. See "
        "`ADR.md` (ADR-0002).",
        "",
    ]

    total = 0
    for bucket in BUCKETS:
        rows = collect(bucket)
        if not rows:
            continue
        lines.append(f"## {bucket}")
        lines.append("")
        for rel, title, tags, status, summary in rows:
            stem = rel[:-3]  # drop .md for the wiki-link
            entry = f"- [[{stem}]] - **{title}**"
            if summary:
                entry += f": {summary}"
            meta = []
            if status:
                meta.append(f"status: {status}")
            if tags:
                meta.append(f"tags: {', '.join(tags)}")
            if meta:
                entry += "  ·  " + "  ·  ".join(f"_{m}_" for m in meta)
            lines.append(entry)
            total += 1
        lines.append("")

    lines.append(f"<!-- {total} notes indexed -->")
    lines.append("")

    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"Wrote {OUTPUT} - {total} notes indexed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
