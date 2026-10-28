---
name: relate-notes
description: "Discover and populate related links for notes missing them. Uses the `search-kb` skill (over the Map of Content, index.md) to find connections, then updates each note's frontmatter `related` field. Use when new notes have been added, when the user asks to link or relate notes, or when running periodic vault maintenance."
---

# Relate Notes

Find semantically related notes for any vault files that have an empty `related: []` field in their
YAML frontmatter, then populate those fields with wiki-links to the best matches. Discovery uses the
vault's **Map of Content** (`index.md`) and the model's own reasoning: fully local, no server, no
embeddings (see `ADR.md` ADR-0002).

## Workflow

### Step 0: Refresh the Map of Content

If notes have been added or changed since `index.md` was last built, rebuild it so candidates are current:

```bash
uv run scripts/build_index.py
```

### Step 1: Find notes with empty related fields

```bash
grep -rl "^related: \[\]" 01_concepts 02_patterns 03_techniques 04_workflows 99_references --include="*.md" | grep -v TEMPLATE | sort
```

If no files are returned, all notes are already linked. Report this and stop.

### Step 2: Find related content by MEANING, not by filename

**For each file with empty `related: []`:**

1. Read the note's own content (title, summary, body) so you know what it is actually *about*. Never match on the filename alone.
2. **Find candidates with the `search-kb` skill.** Pass it the note's content; it forks an isolated read-only search over `index.md`, selects the conceptually closest notes (concepts it builds on, techniques it applies, case studies that demonstrate it, workflows that compose it), and returns a compact list of wiki-links, keeping its search noise out of your context.
3. From the candidates:
   - **Exclude** the note itself.
   - **Exclude** anything outside the core buckets (`01_concepts/ 02_patterns/ 03_techniques/ 04_workflows/ 99_references/`).
   - **Prefer** higher-`status` notes (`polished` > `draft` > `outline` > `wip`) among near-equivalent matches.
   - **Take the top 3-5** genuinely related notes. Do not force links; fewer real links beat padding with weak ones.

If no genuinely related notes exist, fall back to **structural relationships**:
- A folder's `README.md` relates to the key notes in that folder
- Notes in the same subfolder (for example, one paper's folder under `research_papers/`) relate to each other
- A case study relates to the concepts and patterns it demonstrates

### Step 3: Update the related field

Replace `related: []` with the discovered links:

```yaml
related: ["[[path/to/related_note]]", "[[path/to/another_note]]"]
```

**Wiki-link format rules:**
- No `.md` extension
- Full path from repo root (e.g., `[[01_concepts/some_concept]]`)
- Every link must contain at least one `/`
- **Verify every link target exists** before writing it (the path appears in `index.md`, or the file is on disk)

Where it helps the reader, also add the links to the note's `## Related Concepts` section.

### Step 4: Verify and report

Run `python3 scripts/check_links.py`, then report:
- How many notes were updated
- How many notes had no matches (remained `related: []`; this should be rare)
- Each updated file and the links added

## Notes

- Idempotent: running it again only processes files that still have `related: []`.
- If a file has no YAML frontmatter at all, add it first:
  ```yaml
  ---
  tags: [type-tag, difficulty-tag, topic-tag]
  related: []
  status: draft
  ---
  ```
- If a file uses `related-concepts` instead of `related`, rename it to `related` for consistency.
