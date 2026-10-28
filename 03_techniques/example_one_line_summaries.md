---
tags: [technique, fundamentals, knowledge-management, example]
related: ["[[01_concepts/example_atomic_notes]]"]
summary: "EXAMPLE NOTE (delete me): write a one-line summary in frontmatter so the Map of Content can describe the note accurately."
status: draft
---

# One-Line Summaries

> **Example note.** It shows the templates, frontmatter, links, and index working together. Delete it (and update `related:` links that point at it) once you have added your own notes.

## Overview

Give every note a single-sentence `summary:` in its frontmatter. The index builder copies it into `index.md`, which is what agents read to decide which notes to open.

## When to Use It

- Every time you create a note in a core bucket
- When the `summarize-notes` skill flags a note without a summary
- Not needed for `_inbox/` notes, which are not indexed

## Steps

1. **Read the note** and ask what a reader scanning the index needs to know to decide "is this the note I want?"
2. **Write one sentence**, up to about 160 characters, about what the note covers, not how it starts.
3. **Double-quote it** in the frontmatter, so a colon inside the sentence doesn't break YAML parsing.
4. **Rebuild the index** with `uv run scripts/build_index.py` and check the line it produced.

## Copy-Paste Template

```yaml
summary: "What this note covers and why a reader would open it, in one sentence."
```

## Example

Before: no summary, so the index falls back to the first sentence, "This came up in a meeting last week."
After: `summary: "Why one idea per note makes a knowledge base easier to link, search, and reuse."`

## Common Mistakes

- Leaving the value unquoted when it contains a colon: the note's frontmatter fails to parse.
- Summarizing what the note should say rather than what it does say.
- A summary that needs two sentences is a sign the note is not atomic.

## Related Concepts

- [[01_concepts/example_atomic_notes|Atomic Notes]]: why a note should be summarizable in one line
