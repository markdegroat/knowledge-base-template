---
name: summarize-notes
description: "Write a concise one-line `summary:` into the frontmatter of notes that lack one (or have a weak one), so the Map of Content (index.md) carries good, faithful summaries instead of a first-sentence fallback. Use when new notes are added, or as a periodic vault-quality pass before rebuilding the index."
---

# Summarize Notes

Populate the optional `summary:` frontmatter field on vault notes with a faithful, one-line
description of what each note is about. The index builder (`scripts/build_index.py`) prefers
`summary:` when present and only falls back to the note's first sentence when it is absent, so this
skill is what lifts the Map of Content from "first sentence" to "genuine summary", which improves
`search-kb` retrieval. The notes are the source of truth; you are enriching them, not the index.

## Critical format rules (the index parses strict YAML)
`build_index.py` parses frontmatter with PyYAML, which is **strict**. A bad `summary:` line breaks the
whole note's frontmatter. So every summary you write **must**:
- Be on a **single line** (no line breaks).
- Be wrapped in **double quotes**: `summary: "..."`.
- **Escape any internal double quotes** as `\"` (prefer rewording to avoid them).
- Stay at or under **about 160 characters** (the index truncates beyond that anyway).

## Faithfulness rules
- Summarize **only what the note actually says**; never invent claims it doesn't make.
- For a **stub / outline / `status: wip`** note, say so honestly: `summary: "Outline: <topic> (not yet written out)."`
- Capture the *what and why* in plain language, not the first sentence verbatim. Aim for what a reader scanning the index needs to decide "is this the note I want?"

## Workflow

### Step 1: Find notes missing a `summary:`
```bash
grep -rL "^summary:" 01_concepts 02_patterns 03_techniques 04_workflows 99_references --include="*.md" | grep -v TEMPLATE | sort
```
(To also refresh weak existing summaries, review notes whose current `summary:` is vague and redo them.)

### Step 2: For each note, read it and write a summary
1. Read the note (title, body) to understand what it actually covers.
2. Compose a faithful one-line summary following the format and faithfulness rules above.
3. Insert it into the frontmatter, conventionally right after `related:` (and before `status:` if present). Example:
   ```yaml
   ---
   tags: [concept, fundamentals, knowledge-management]
   related: ["[[03_techniques/some_technique]]"]
   summary: "Why one idea per note makes a knowledge base easier to link, search, and reuse."
   status: draft
   ---
   ```
4. Do **not** touch any other field.

### Step 3: Rebuild the index
```bash
uv run scripts/build_index.py
```
If the build prints `WARN: frontmatter failed to parse` for a note you just edited, your `summary:`
almost certainly has an unescaped quote or a stray line break. Fix it and rebuild.

### Step 4: Report
- How many notes got a new `summary:`.
- Any notes you flagged as stubs or outlines.
- Confirm the index rebuilt with no parse warnings.

## Notes
- Re-running only needs to touch notes still missing `summary:` (unless you are deliberately refreshing weak ones).
- This skill **writes** to notes (unlike the read-only `search-kb`). It pairs with `relate-notes` (which writes `related:`) as the two frontmatter-enrichment maintenance skills. See `ADR.md` (ADR-0002).
