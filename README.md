# Knowledge Base Template

A starting point for a personal or team knowledge base kept as plain Markdown in git, built to be read and maintained by people and Claude Code together, using only Claude Code's own building blocks: `CLAUDE.md`, subagents, skills and a hook. It holds no content of its own, apart from two small example notes to delete.

## The idea

**Buckets.** Notes are sorted by what kind of knowledge they hold, not by project or date:

| Folder | Holds |
|--------|-------|
| `01_concepts/` | Principles and theories: the "why" |
| `02_patterns/` | Repeatable high-level strategies |
| `03_techniques/` | Tactical methods, checklists, copy-pasteable templates |
| `04_workflows/` | End-to-end processes that compose the above |
| `99_references/` | External material: `case_studies/`, `research_papers/`, `youtube_videos/` |
| `_inbox/` | Raw, unrefined notes waiting to be worked on |
| `_archive/` | Superseded notes, kept for history |

Each bucket has a `TEMPLATE_*.md` to copy when you add a note.

**Small notes, linked by full path.** One idea per note, in a `snake_case.md` file. Notes link to each other with wiki-links that always spell out the path from the repo root, such as `[[01_concepts/atomic_notes]]`, never a bare `[[atomic_notes]]`. Full paths stay unambiguous when two folders hold files with the same name, and they work in Obsidian, in editors and for agents alike. Every link must point at a file that exists; `python3 scripts/check_links.py` checks that.

**Frontmatter.** Every note starts with YAML: `tags` (type, difficulty, topic), `related` (wiki-links), a one-line double-quoted `summary`, and a `status` (`wip`, `outline`, `draft`, `polished`).

**A generated Map of Content instead of embeddings.** `scripts/build_index.py` reads every note's frontmatter and writes `index.md`: one line per note with its path, title, summary, status and tags. To find notes, an agent reads that map and picks the relevant ones by meaning, which catches notes a keyword search would miss. There is no vector store, search server or app to run; the index is a committed file you rebuild after changing notes. This holds up to a few hundred notes; beyond that, revisit it (see `ADR.md`).

**An inbox and a refinement loop.** Raw ideas land in `_inbox/`. An agent helps refine them through conversation, then the material is decomposed into the right buckets with templates, linked, tagged, indexed, and the raw note is archived.

**Agents and skills for search and upkeep.**

| Name | Kind | What it does |
|------|------|--------------|
| Ask the Codebase Questions | agent | Answers questions about the vault, read-only, citing notes |
| Iterate Raw Note | agent | Refines a raw note in `_inbox/` with you; never writes outside it |
| Decompose Inbox to Concepts | agent | Proposes which inbox ideas become concept notes, then writes them once you approve |
| Ingest YouTube Video | agent | Turns a video into a reference note in `99_references/youtube_videos/` |
| `search-kb` | skill | Finds notes by meaning from `index.md`, returns a list of links |
| `relate-notes` | skill | Fills empty `related:` fields using `search-kb` |
| `summarize-notes` | skill | Writes missing `summary:` lines so the index stays useful |
| `youtube-transcript` | skill | Fetches a video transcript (used by the ingest agent) |

**Instructions and decisions.** `CLAUDE.md` carries the rules (naming, frontmatter, links, tags, where things go, the git workflow). `ADR.md` logs the structural decisions and why they were made; it is append-only, newest first.

**Git workflow.** Every unit of work goes on a short-lived branch (`content/...`, `chore/...`, `fix/...`); agents commit freely there and ask before merging to `main` or pushing. In Claude Code, a hook (`.claude/hooks/block_commit_on_main.sh`) blocks commits made directly on `main`.

## Getting started

Prerequisites: git, Python 3.10 or later, and [uv](https://docs.astral.sh/uv/) (it installs the index builder's one dependency, PyYAML, on the fly).

1. **Copy the template** into a new folder and start a fresh history:
   ```bash
   cp -R knowledge-base-template my-knowledge-base
   cd my-knowledge-base && rm -rf .git && git init -b main
   ```
   (Or clone it, or use it as a GitHub template repository.)
2. **Name your topic.** Replace `[YOUR TOPIC]` in section 1 of `CLAUDE.md` with a sentence or two on what the knowledge base covers. Retitle this README.
3. **Adapt the tag taxonomy.** In section 3 of `CLAUDE.md`, replace the example **Topic** tags with 4 to 8 themes from your domain. Add dimensions if you need them.
4. **Adjust the buckets** if your domain needs it (for example, drop `youtube_videos/` or add another `99_references/` subfolder). Update `CLAUDE.md` and `BUCKETS` in `scripts/build_index.py` to match.
5. **Delete the example notes** (`01_concepts/example_atomic_notes.md` and `03_techniques/example_one_line_summaries.md`) once you have read them, and add your first notes from the templates.
6. **Rebuild the index and check links:**
   ```bash
   uv run scripts/build_index.py
   python3 scripts/check_links.py
   ```
7. **Commit** your first notes on a branch and merge it.

## Using it with Claude Code

Open the folder and start `claude`. `CLAUDE.md` is loaded automatically, and the hook in `.claude/settings.json` is active.

- Ask a question: "Use the ask-the-codebase-questions agent: what do we know about X?" (or @-mention the agent).
- Search: `/search-kb onboarding new team members` returns the relevant notes as links.
- Capture an idea: "Use the iterate-raw-note agent to help me shape this idea: ..."
- Promote inbox material: "Run decompose-inbox-to-concepts."
- Ingest a video: "Use ingest-youtube on https://www.youtube.com/watch?v=..." Fetching the transcript is best-effort: YouTube sometimes blocks it. If it fails, paste the transcript into the chat and the agent works from that.
- Upkeep: `/summarize-notes`, then `/relate-notes`, then rebuild the index.

`docs/subagent_frontmatter_reference.md` is a commented reference of every subagent frontmatter field. It lives outside `.claude/agents/` so it does not load as an agent; copy it there, renamed, when you write your own.

## Maintenance checklist

After adding or changing notes:

1. `summarize-notes` for notes without a `summary:`
2. `relate-notes` for notes with `related: []`
3. `uv run scripts/build_index.py`
4. `python3 scripts/check_links.py`
5. Commit `index.md` with the notes

## License

MIT. See [LICENSE](LICENSE).
