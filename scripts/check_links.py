#!/usr/bin/env python3
"""Check that every [[wiki-link]] in the vault points at a file that exists.

Scans every Markdown file in the repo (skipping .git) and checks each [[target]] or
[[target|label]] against the rules in CLAUDE.md section 3:
  - the target contains at least one "/" (full path from the repo root, never a bare name)
  - no ".md" extension and no "../" relative path
  - <target>.md (or <target> itself) exists

Links inside fenced code blocks, inline code spans and HTML comments are ignored, so
templates and instruction files can show example links without tripping the check.

    python3 scripts/check_links.py        # exit 0 if clean, 1 if any problem

Standard library only.
"""

from __future__ import annotations

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

FENCE = re.compile(r"^\s*(```|~~~)")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"\[\[([^\]\n]+)\]\]")


def strip_ignored(text: str) -> str:
    """Blank out fenced code blocks, HTML comments and inline code, keeping line numbers."""
    text = COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    out, in_fence = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else INLINE_CODE.sub("", line))
    return "\n".join(out)


def check_link(raw: str) -> str | None:
    """Return a problem description for one link, or None if it is fine."""
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    if "/" not in target:
        return "bare filename (use the full path from the repo root)"
    if target.startswith(("../", "./", "/")):
        return "relative or absolute path (use the path from the repo root)"
    if target.endswith(".md"):
        return "drop the .md extension"
    full = os.path.join(REPO_ROOT, target)
    if os.path.isfile(full + ".md") or os.path.isfile(full):
        return None
    return "target does not exist"


def main() -> int:
    problems = 0
    checked = 0
    for dirpath, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
            with open(path, encoding="utf-8") as fh:
                text = strip_ignored(fh.read())
            for lineno, line in enumerate(text.split("\n"), start=1):
                for m in LINK.finditer(line):
                    checked += 1
                    issue = check_link(m.group(1))
                    if issue:
                        problems += 1
                        print(f"{rel}:{lineno}: [[{m.group(1)}]]: {issue}")
    print(f"{checked} wiki-links checked, {problems} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
