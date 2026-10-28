---
name: search-kb
description: Search the knowledge base for notes relevant to a topic or content, by meaning rather than keywords (it catches notes whose wording differs from the query, which a grep misses). Returns a compact, relevance-ordered list of full-path wiki-links. Use for discovery before authoring, answering a question about the vault, or finding related notes to link. Runs in an isolated subagent context so the calling thread stays clean.
argument-hint: [topic or note content to search for]
model: inherit
context: fork
agent: Explore
---

# Search the Knowledge Base

Find the vault notes that are *conceptually* relevant to a query, including notes whose wording
differs from the query (which a keyword `grep` misses), and return them as a compact link list.

Because this skill declares `context: fork`, it runs in an **isolated, read-only subagent context**
(the built-in `Explore` agent): that context absorbs the full `index.md` and any irrelevant note
bodies, so only the final link list returns to the calling thread. That isolation is the point.
This is the single, reusable "search the KB" handle, so instruction files and other skills say
*"use the `search-kb` skill"* rather than re-describing the procedure.

**Query:** $ARGUMENTS

## Do this
1. Load `index.md` (the Map of Content) at the repo root: one line per note with path, summary, status, tags.
2. Reason over it to select the notes whose *meaning* best matches the query above. Read only the
   strongest candidates to confirm relevance; follow their `related:` links if that sharpens the set.
3. **Return only** a relevance-ordered list of `[[directory/filename]]` wiki-links (full path from the
   repo root, no `.md`), each with an optional reason of up to six words. No prose, no quotes, no index
   dump. An **empty list is a valid answer**; do not force weak matches.
4. Verify every link you return resolves to a real file (it appears in `index.md`).

## Notes
- **Read-only**: this skill only finds notes; it never edits them. (The `relate-notes` skill consumes
  these results to write `related:` links.)
- If `index.md` is missing or looks stale, rebuild it with `uv run scripts/build_index.py` from a
  normal (non-read-only) context, then search again. The notes are the source of truth; the index is
  derived. See `ADR.md` (ADR-0002) for why this replaces an embedding index or graph server.
