# CLAUDE.md - Agent Operations Guide

> **Note to Agents:** This file is the source of truth for this repository. Claude Code loads it at the start of every session; the agents in `.claude/agents/` and the skills in `.claude/skills/` build on it.

> **Decision records:** Notable structural decisions (and their justifications) are logged in [`ADR.md`](ADR.md) at the repo root, newest first. Consult it for the *why* behind the repo's setup, and **append a new entry** when you make or reverse a structural decision (never edit old entries; mark them `Superseded by ADR-XXXX`).

## 1. Repository Overview

This is a **knowledge base about [YOUR TOPIC]**: a modular, interconnected vault of concepts, patterns, techniques, workflows, and references. Notes are small, linked to each other with full-path wiki-links, and described by YAML frontmatter. A generated Map of Content (`index.md`) lets an agent find notes by meaning without embeddings or a search server.

> **Owner:** replace `[YOUR TOPIC]` above with one or two sentences on what this knowledge base covers and what it is for. Agents use that scope to decide what belongs here.

## 2. Directory Structure & Organization

### Core Buckets
- **`01_concepts/`**: Abstract principles and theories: the "why" behind the domain.
- **`02_patterns/`**: High-level strategies and repeatable approaches.
- **`03_techniques/`**: Tactical, actionable methods: specific steps, checklists, and copy-pasteable templates.
- **`04_workflows/`**: End-to-end applied workflows that compose concepts, patterns, and techniques into complete processes. This is the "put it all together" bucket.
- **`99_references/`**: External resources and reference material.
    - **`case_studies/`**: Real-world examples demonstrating concepts and patterns.
    - **`research_papers/`**: Academic and industry papers with LLM-generated summaries. Each paper gets its own subfolder holding the raw PDF and a structured summary note. A staging area, like `youtube_videos/`.
    - **`youtube_videos/`**: Distilled notes from YouTube videos on the topic. A staging area.

### Operational Folders
- **`_inbox/`**: Intake area for raw notes, brainstorms, and rough ideas. The **Iterate Raw Note** agent works exclusively here; content is never moved to the main vault directly from that agent.
- **`_archive/`**: Deprecated or superseded files.
- **`scripts/`**: Vault tooling: `build_index.py` (builds the Map of Content) and `check_links.py` (verifies wiki-links).

### Searching the Vault
Discover related content, in this order:
- **Use the `search-kb` skill** to find notes by meaning. It forks an isolated, read-only search that reasons over `index.md` (the generated Map of Content: one line per note with path, summary, status and tags), selects the conceptually relevant notes (catching ones whose wording differs from your query, which a keyword grep misses), and returns just the relevant `[[wiki-links]]`; the index's bulk never enters your context. Rebuild the map after adding or removing notes: `uv run scripts/build_index.py`.
- **Grep** for content/keyword matches and **Glob** for file-path/naming lookups, when you need an exact string the index doesn't surface.
- Follow **wiki-links** (`[[directory/filename]]`) to traverse connections between notes by hand. The `related:` frontmatter and `## Related Concepts` sections are the vault's link structure.

> For a user-facing **question** about the vault (an explained answer, not just links), the read-only `Ask the Codebase Questions` agent synthesizes a response grounded in the same index and notes.

### Custom Agents and Skills
Claude Code subagents live in `.claude/agents/`. These are **isolated agents** with their own context window, system prompt, and tool restrictions.

Available agents:
- **Ask the Codebase Questions**: Read-only query agent. Searches the vault and synthesizes answers. Never edits, creates, or deletes files.
- **Iterate Raw Note** (`Inbox_Agent`): Works only inside `_inbox/`. Refines raw notes and prepares them for integration, but never integrates into core buckets directly; it stops and hands off to the user or another agent.
- **Ingest YouTube Video**: Takes a YouTube URL or transcript and distills it into a structured reference note in `99_references/youtube_videos/`.
- **Decompose Inbox to Concepts**: Analyzes inbox notes and identifies concept-worthy material for promotion to `01_concepts/`.

`docs/subagent_frontmatter_reference.md` is a reference catalog of every Claude Code subagent frontmatter field, written as a tiny example agent. It sits outside `.claude/agents/` so Claude Code does not load it; copy it there, renamed, when you write a new agent.

Skills live in `.claude/skills/`, one folder each:
- **`search-kb`**: semantic search over `index.md`, returns a list of wiki-links (read-only).
- **`relate-notes`**: fills empty `related: []` frontmatter using `search-kb`.
- **`summarize-notes`**: writes a one-line `summary:` into notes that lack one, so the index carries real summaries.
- **`youtube-transcript`**: fetches a YouTube transcript (used by the Ingest YouTube Video agent).

## 3. File & Naming Conventions

### File Naming
- **Format**: `snake_case.md` (e.g., `atomic_notes.md`, `weekly_review.md`).
- **Prefixes**:
    - `TEMPLATE_` for templates (e.g., `TEMPLATE_concept.md`). The index builder skips these.
    - Numbered prefixes (e.g., `01_`, `02_`) are **only for directories** to enforce sort order, NOT for individual files.

### YAML Frontmatter
Every note should include a frontmatter block with at minimum `tags` and `related`:
```yaml
---
tags: [concept, fundamentals, your-topic]
related: ["[[02_patterns/some_pattern]]", "[[03_techniques/some_technique]]"]
summary: "One-line description of what this note covers, used by the Map of Content (index.md)."
status: draft
---
```

- **`summary`** (optional but recommended): a single-line, **double-quoted** description (up to about 160 characters) of what the note covers. It feeds `index.md` for semantic retrieval; when absent, the builder falls back to the note's first sentence. **Keep it one line and double-quoted**: `build_index.py` parses frontmatter as strict YAML, so an unquoted value containing a colon (very common in summaries) breaks the parse. The `summarize-notes` skill populates this for notes that lack it.
- **`status`**: one of `wip`, `outline`, `draft`, `polished`. The index shows it, and agents prefer higher-status notes when several cover the same ground.

### Linking (Wiki-Links)

**CRITICAL: All wiki-links MUST use the full path from the repository root** (without `.md` extension). Never use bare filenames. Filenames can be duplicated across directories, and bare names do not resolve to clickable links when viewing notes as markdown.

**Format:** `[[directory/filename]]` or `[[directory/filename|Display Label]]`

**Examples:**
```markdown
# Correct: full path from repo root
[[01_concepts/atomic_notes]]
[[02_patterns/weekly_review]]
[[99_references/case_studies/team_wiki_migration|Wiki Migration Case Study]]
[[_inbox/rough_idea]]

# WRONG: bare filename (will break)
[[atomic_notes]]
[[weekly_review]]
```

**Rules:**
- Every `[[link]]` must contain at least one `/`; if it doesn't, the link is wrong.
- The target file **must exist** at the path specified. Do not link to files that don't exist. If a note is still in `_inbox/`, link to `_inbox/filename`, not to a hypothetical future location.
- No `.md` extension in wiki-links.
- No `../` relative paths; always use paths relative to the repository root.
- Labels are optional: `[[01_concepts/atomic_notes|Atomic Notes]]` renders as "Atomic Notes".
- **Placement**: Add a `## Related Concepts` section at the bottom of each note.
- **Validation**: Before finalizing any note, verify that every `[[link]]` target actually exists at that path. Run `python3 scripts/check_links.py`, or search the repository.

### Tagging

Use `kebab-case` tags in the frontmatter `tags` array. **Do NOT prefix tags with `#`**: the `#` symbol breaks YAML frontmatter parsing in Obsidian and other tools. Tags are plain strings inside the YAML array.

```yaml
# Correct:
tags: [concept, fundamentals, your-topic]

# WRONG: will break frontmatter
tags: [#concept, #fundamentals, #your-topic]
```

Taxonomy (an example; the owner adapts the **Topic** row to the domain and may add dimensions):

| Dimension   | Valid Tags |
|-------------|-----------|
| **Type**    | `concept`, `pattern`, `technique`, `workflow`, `case-study`, `reference` |
| **Difficulty** | `fundamentals`, `intermediate`, `advanced` |
| **Topic**   | 4 to 8 tags for your domain's main themes (example: `knowledge-management`, `tooling`, `process`, `quality`) |

Every note must include tags for **type**, **difficulty**, and **topic**. Maturity goes in the `status:` field, not in tags.

## 4. Content Classification

Before creating a new file, decide which bucket it belongs in:

| If the content is... | Use bucket |
|--------------------|-----------|
| A theory, principle, or "why" explanation | `01_concepts/` |
| A repeatable high-level strategy or approach | `02_patterns/` |
| A specific, tactical method, checklist, or copy-pasteable template | `03_techniques/` |
| An end-to-end applied workflow composing concepts, patterns, and techniques | `04_workflows/` |
| A distilled summary of an academic or industry research paper | `99_references/research_papers/` |
| A distilled YouTube video | `99_references/youtube_videos/` |
| A real-world example | `99_references/case_studies/` |
| An external article, guide, or other reference material | `99_references/` |
| A raw idea that is not ready for any of the above | `_inbox/` |

## 5. Agent Workflows

### Discovery (Always Do This First)
1. **Find existing related notes with the `search-kb` skill.** For "does this already exist / what relates to X", it returns the notes most relevant to your topic by meaning (catching ones a keyword grep misses) as a compact list of `[[wiki-links]]`. Then supplement with Grep (keyword/content) and Glob (file paths) for anything exact the index doesn't surface. Follow wiki-links to find related notes.
2. Search existing folders to understand current content and avoid duplication.
3. Read the relevant template before creating anything:
   - `01_concepts/TEMPLATE_concept.md`
   - `02_patterns/TEMPLATE_pattern.md`
   - `03_techniques/TEMPLATE_technique.md`
   - `04_workflows/TEMPLATE_workflow.md`
   - `99_references/case_studies/TEMPLATE_case_study.md`
   - `99_references/research_papers/TEMPLATE_research_paper.md`
   - `99_references/youtube_videos/TEMPLATE_youtube_video.md`
   - `_inbox/TEMPLATE_inbox.md`

### Content Creation (The "Refinement Loop")
1. **Ingest**: Read raw notes from `_inbox/` or user input.
2. **Classify**: Use the Content Classification table above.
3. **Draft**: Create the file in the correct folder using the appropriate `TEMPLATE_*.md`.
4. **Link**: Add wiki-links to related files using full paths from repo root (Concepts, then Patterns and Techniques, then Workflows and Case Studies). **Verify each link target exists**; do not guess paths.
5. **Tag**: Add frontmatter with type, difficulty, and topic tags, a `summary`, and a `status`.
6. **Index**: Rebuild the Map of Content with `uv run scripts/build_index.py`.

### Refactoring
- When moving files, **update all incoming wiki-links**.
- Consolidate fragmentary content into existing concept or technique notes; don't create near-duplicates.
- Ensure every moved file has complete YAML frontmatter.

## 6. Common Agent Tasks

### Work with Inbox Notes
1. Read the raw note in `_inbox/`.
2. Clarify and structure the content.
3. Propose a decomposition into `01_concepts/`, `02_patterns/`, etc.
4. Create final notes in core buckets using templates.
5. Move the raw note to `_archive/` once integrated.

### Create New Content
- **Concept**: Use `01_concepts/TEMPLATE_concept.md`. Focus on definition, core claims, and examples.
- **Pattern**: Use `02_patterns/TEMPLATE_pattern.md`. Focus on "when to use", "how to apply", and worked examples.
- **Technique**: Use `03_techniques/TEMPLATE_technique.md`. Focus on concrete steps and copy-pasteable material.
- **Workflow**: Use `04_workflows/TEMPLATE_workflow.md`. Focus on end-to-end processes that compose concepts, patterns, and techniques.
- **Case Study**: Use `99_references/case_studies/TEMPLATE_case_study.md`. Focus on context, challenge, and results.

### Vault Maintenance
- Notes missing a `summary:`: run the `summarize-notes` skill.
- Notes with `related: []`: run the `relate-notes` skill.
- After either, rebuild the index and run `python3 scripts/check_links.py`.
- Only update `CLAUDE.md` for structural changes; don't list individual notes here.

## 7. Quality Standards

- **Completeness**: Use the provided templates. Don't leave required sections empty.
- **Linkage**: When creating or editing a note, search the repository for all notes that are directly related and link every one of them. Do not force links: if no existing notes are genuinely related, zero links is acceptable. The goal is completeness and accuracy, not hitting a minimum count. All links must use full paths from repo root and must point to files that actually exist (see Linking rules above).
- **Link Validation**: Before finishing any create or edit task, verify that every `[[link]]` in the file points to a real file (`python3 scripts/check_links.py`). Never assume a path is correct without checking. If a referenced note only exists in `_inbox/`, link to the `_inbox/` path, not to a hypothetical future location.
- **Tagging**: Always include type, difficulty, and topic tags.
- **No Duplication**: Link to source files instead of copy-pasting content.
- **Headings**: Use H1 for the title only; use H2/H3 for structure within the note.

## 8. Git Workflow

**Branch per unit of work.** Every unit of work (agentic session or human) happens on a short-lived branch off `main`. Direct commits on `main` are not allowed. See `ADR.md` ADR-0003 for the rationale.

### Branch Naming

Format: `<type>/<short-kebab-topic>`

| Type | Use for |
|------|---------|
| `content` | Notes in the core buckets or `_inbox/` |
| `chore` | Index rebuilds, tooling, config, ADRs, repo instructions |
| `fix` | Broken links, frontmatter, small corrections |

Examples: `content/atomic-notes-concept`, `chore/rebuild-index`, `fix/broken-links`.

### Session Lifecycle

1. **Branch.** From an up-to-date `main`: `git switch -c <type>/<topic>`.
2. **Commit.** Commit freely at logical checkpoints without asking: one commit per logical change, `Verb: Description` format.
3. **Rebuild the index.** If any note was added, removed, or had its `summary`, `status` or `tags` changed, run `uv run scripts/build_index.py` and commit `index.md` on the branch. Verify wiki-links per section 3.
4. **Ask.** Merging to `main` and pushing to the remote ALWAYS require the user's explicit go-ahead in that session. Stop and ask.
5. **Merge.** From `main`: `git merge --no-ff <branch>` so history shows the grouping. If a merge conflict needs resolving, finish with `git merge --continue`, not `git commit`.
6. **Delete the branch.** `git branch -d <branch>`. Push only if the user said to.

A pull request is optional; open one when the change should be reviewed (for a shared team vault, make it the norm).

**Parallel sessions** use separate worktrees (`git worktree add <path> -b <type>/<topic>`) so they do not fight over one index; each worktree carries its own branch.

**Enforcement.** A Claude Code `PreToolUse` hook (`.claude/hooks/block_commit_on_main.sh`, registered in `.claude/settings.json`) blocks any Bash `git commit` while the current branch is `main` or `master` and tells the agent to create a branch first. It does not block `git merge`, `git log`, or other git commands. The hook applies to Claude Code sessions; other tools follow this rule by instruction.

### Commit Messages

Commit messages use the format `Verb: Description`:
- `Add: atomic_notes.md`
- `Update: clarify examples in weekly_review.md`
- `Refactor: move case studies to references`
- `Fix: broken links in README`

Keep commits focused on a single logical change.
