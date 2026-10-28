# Architecture Decision Record

A running log of notable decisions for this repository. **Newest first.** Each entry
records *why* a decision was made, not just *what* changed, so future agentic sessions
(and new contributors) have the context behind the repo's structure.

**Conventions**
- Entries are numbered in creation order (`ADR-0001`, `ADR-0002`, ...); the highest
  number is the most recent and appears at the top.
- The log is append-only. A decision is never edited away. When a decision is reversed or
  replaced, add a **new** entry and change only the old entry's status line to
  `Status: Superseded by ADR-XXXX`.
- Keep each entry to **Context** (the why), **Decision** (what was chosen), and
  **Consequences** (what it costs, what it enables, how to reverse it).
- The three entries below are seed decisions that come with the template. Keep them if
  they hold for your vault; supersede them with new entries if you change course.

**Template for a new entry** (copy it above the newest entry):

```markdown
## ADR-XXXX - Short decision title
**Date:** YYYY-MM-DD  **Status:** Accepted

**Context.** What problem or pressure led to this decision? What constraints apply?

**Decision.** What was chosen, specifically enough that someone could check it.

**Consequences.** What this costs, what it enables, and how to reverse it.
```

---

## ADR-0003 - Branch per unit of work, with a human gate at merge and push
**Date:** YYYY-MM-DD  **Status:** Accepted

**Context.** Agentic sessions and people both write to the vault. When everyone commits
straight to the default branch, work from several sessions piles up in one working tree and
history does not show which changes belong together. Agents also need a simple rule for when
they may commit on their own and when they must ask.

**Decision.** Every unit of work happens on a short-lived branch off `main`, named
`<type>/<short-kebab-topic>` (`content`, `chore`, `fix`). On the branch, agents commit freely
at logical checkpoints (`Verb: Description`). Merging to `main` and pushing always require
the user's explicit go-ahead in that session. Before merging, rebuild `index.md` if notes
changed and verify wiki-links. Merge with `git merge --no-ff` so history shows the grouping,
then delete the branch. Parallel sessions use separate worktrees. A Claude Code `PreToolUse`
hook (`.claude/hooks/block_commit_on_main.sh`) blocks `git commit` while on `main` or
`master`. The full procedure is section 8 of `CLAUDE.md`.

**Consequences.** A little ceremony per unit of work (branch, ask, merge, delete) and one
hook to maintain. In return, history groups each unit of work under one merge commit, agents
checkpoint without prompting, and parallel sessions stay apart. The hook is a pragmatic regex
and can miss exotic invocations (aliases, scripts that commit internally), so the instruction
remains the primary rule. To reverse: remove the hook and its entry in
`.claude/settings.json`, revert section 8 in both instruction files, and add a new ADR.

---

## ADR-0002 - A generated Map of Content instead of a vector store or graph server
**Date:** YYYY-MM-DD  **Status:** Accepted

**Context.** Keyword search (grep) misses notes where the idea is present but the searched
word is not. The usual fixes are an embedding index (a vector store) or a graph-query server
over the vault. Both add a runtime dependency to install, host and keep working, and a
third-party integration can break the vault's search when it changes upstream. For a vault of
up to a few hundred notes, the path, title, summary, status and tags of every note fit in an
agent's context, so the model itself can select relevant notes by meaning.

**Decision.** `scripts/build_index.py` generates `index.md`, a one-line-per-note Map of
Content over the five core buckets. It parses frontmatter with PyYAML, declared as an inline
(PEP 723) dependency so `uv run scripts/build_index.py` provisions it with no system install.
The index is a derived, committed, rebuildable artifact; the notes stay the source of truth.
Retrieval is done by agents reading the index:
- The `search-kb` skill runs in a forked, read-only context (`context: fork`), reasons over
  `index.md`, reads only the strongest candidates and returns a short list of wiki-links. The
  fork absorbs the index's bulk so the calling thread stays clean.
- The `Ask the Codebase Questions` agent uses the same index to answer a person's question
  with an explained answer.
- `summarize-notes` and `relate-notes` enrich the notes' own frontmatter (`summary:`,
  `related:`), so the index improves without baking model output into the derived file.

**Consequences.** Semantic discovery with nothing running at query time: no server, no
embeddings, no app. Costs: no graph algorithms (clustering, centrality); retrieval quality
depends on agents actually consulting the index; and the index must be rebuilt after vault
changes (kept manual on purpose). **Upgrade trigger:** when `index.md` outgrows a subagent's
comfortable context (several hundred to low thousands of notes) or retrieval quality drops,
consider a local embedding index in a new ADR.

---

## ADR-0001 - Build on Claude Code's own primitives only
**Date:** YYYY-MM-DD  **Status:** Accepted

**Context.** The vault is maintained with Claude Code. Supporting several agent tools means
mirrored instruction files and agent folders that drift apart, for no gain to one team that
uses one tool.

**Decision.** Use only Claude Code's built-in building blocks: `CLAUDE.md` for the rules,
subagents in `.claude/agents/`, skills in `.claude/skills/` (one folder each), and hooks
registered in `.claude/settings.json`. Scripts the skills and hooks call live in `scripts/`
or inside the skill's folder.

**Consequences.** One place to change each rule, agent or skill. Another tool would need its
own configuration; adding one is a new ADR.