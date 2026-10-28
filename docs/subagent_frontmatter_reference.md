---
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CLAUDE CODE SUBAGENT - COMPLETE CONFIGURATION REFERENCE           ║
# ║                                                                     ║
# ║  This file demonstrates EVERY configurable frontmatter field       ║
# ║  available in .claude/agents/*.md subagent definitions.            ║
# ║                                                                     ║
# ║  Docs: https://code.claude.com/docs/en/sub-agents                  ║
# ║                                                                     ║
# ║  Scope precedence (highest → lowest):                              ║
# ║    1. --agents CLI flag (session-only JSON)                        ║
# ║    2. .claude/agents/  (project-level, check into VCS)             ║
# ║    3. ~/.claude/agents/ (user-level, all projects)                 ║
# ║    4. Plugin agents/   (from installed plugins)                    ║
# ╚══════════════════════════════════════════════════════════════════════╝

# ── REQUIRED FIELDS ──────────────────────────────────────────────────

# name (string, REQUIRED)
#   Unique identifier. Lowercase letters, numbers, and hyphens only.
#   Max 64 characters. This becomes the internal reference that Claude
#   uses when spawning the agent (e.g., Agent(tell-time)).
#   If omitted, derived from the filename (minus .md extension).
name: tell-time

# description (string, REQUIRED)
#   Tells Claude WHEN to delegate tasks to this subagent. Claude reads
#   every subagent description at session start to decide routing.
#   Include "use proactively" to encourage automatic delegation.
#   Shown in `/agents` listing and typeahead when @-mentioning.
description: >-
  Tells the current date, time, and timezone. Use proactively when the
  user asks what time it is, what today's date is, or needs any
  temporal information.

# ── MODEL & EFFORT ───────────────────────────────────────────────────

# model (string, optional - default: "inherit")
#   Which AI model this subagent uses.
#   Values:
#     "sonnet"  - alias for latest Sonnet
#     "opus"    - alias for latest Opus
#     "haiku"   - alias for latest Haiku (fast/cheap)
#     "inherit" - same model as the main conversation (default)
#     Full model ID - e.g. "claude-sonnet-4-6", "claude-opus-4-6"
model: haiku

# effort (string, optional - default: inherits from session)
#   Controls reasoning depth. Overrides the session-level effort.
#   Values: "low", "medium", "high", "max"
#   Which levels are available depends on the model.
effort: low

# ── TOOL ACCESS ──────────────────────────────────────────────────────

# tools (comma-separated string, optional - default: inherits ALL tools)
#   Allowlist of tools the subagent can use. If omitted, inherits
#   every tool from the main conversation (including MCP tools).
#
#   Available built-in tools:
#     Read, Write, Edit, Glob, Grep   - file operations
#     Bash                            - shell execution
#     WebFetch, WebSearch             - web access
#     Skill                           - invoke skills
#     Agent(type1, type2)             - spawn child agents (main thread only)
#
#   Constrained tool syntax:
#     Bash(git *)           - only allow git commands
#     Bash(date*,echo*)     - only allow date and echo commands
#     Agent(worker,researcher) - only spawn these subagent types
#
#   MCP tools are referenced by their server-scoped name.
tools: Bash, Read, Glob, Grep

# disallowedTools (comma-separated string, optional)
#   Denylist - removes tools from the inherited or allowed set.
#   Applied BEFORE the tools allowlist is resolved.
#   If a tool appears in both `tools` and `disallowedTools`, it is removed.
disallowedTools: Write, Edit

# ── PERMISSIONS ──────────────────────────────────────────────────────

# permissionMode (string, optional - default: "default")
#   Controls how the subagent handles permission prompts.
#   Values:
#     "default"           - standard permission checking with prompts
#     "acceptEdits"       - auto-accept file edits
#     "dontAsk"           - auto-deny permission prompts (explicitly
#                           allowed tools still work)
#     "bypassPermissions" - skip all permission prompts (USE WITH CAUTION:
#                           writes to .git, .claude, .vscode, .idea still prompt)
#     "plan"              - read-only exploration mode
#
#   If the parent uses bypassPermissions, it takes precedence and
#   cannot be overridden. If parent uses auto mode, this is ignored.
permissionMode: default

# ── EXECUTION CONTROL ────────────────────────────────────────────────

# maxTurns (integer, optional)
#   Maximum number of agentic turns before the subagent stops.
#   Prevents runaway agents. Omit for unlimited turns.
maxTurns: 5

# background (boolean, optional - default: false)
#   true  = always run as a background task (non-blocking, concurrent)
#   false = run in foreground (blocking, interactive)
#
#   Background agents: Claude pre-approves permissions before launch.
#   Permission prompts that weren't pre-approved are auto-denied.
#   Clarifying questions (AskUserQuestion) fail but agent continues.
#
#   Foreground agents: block the main conversation. Permission prompts
#   and clarifying questions pass through to the user.
#
#   Users can press Ctrl+B to background a running foreground agent.
background: false

# isolation (string, optional)
#   Set to "worktree" to run in a temporary git worktree - an isolated
#   copy of the repository. Automatically cleaned up if the subagent
#   makes no changes. If changes are made, the worktree path and
#   branch are returned in the result.
#   Useful for parallel work that might conflict with main branch.
#   Omit for no isolation (subagent works in the same directory).
# isolation: worktree

# ── PERSISTENT MEMORY ────────────────────────────────────────────────

# memory (string, optional)
#   Gives the subagent a persistent directory that survives across
#   conversations. The agent builds up knowledge over time.
#   Read, Write, and Edit tools are auto-enabled when memory is set.
#
#   Values:
#     "user"    - ~/.claude/agent-memory/<name>/
#                  (learnings across ALL projects)
#     "project" - .claude/agent-memory/<name>/
#                  (project-specific, shareable via VCS)
#     "local"   - .claude/agent-memory-local/<name>/
#                  (project-specific, NOT checked into VCS)
#
#   When enabled, the system prompt includes:
#     - Instructions for reading/writing to the memory directory
#     - First 200 lines of MEMORY.md from the memory directory
#     - Instructions to curate MEMORY.md if it exceeds 200 lines
#
#   Omit to disable persistent memory.
memory: local

# ── PRELOADED SKILLS ─────────────────────────────────────────────────

# skills (list of strings, optional)
#   Skills to inject into the subagent's context at startup.
#   The FULL content of each skill is injected, not just made available.
#   Subagents do NOT inherit skills from the parent conversation -
#   you must list them explicitly here.
#
#   Reference skills by their name (from the skill's `name` field or
#   directory name). Plugin skills use "plugin-name:skill-name" format.
#
#   Uncomment and customize:
# skills:
#   - api-conventions
#   - error-handling-patterns

# ── MCP SERVERS ──────────────────────────────────────────────────────

# mcpServers (list, optional)
#   MCP servers available to this subagent. Each entry is either:
#     1. An inline definition (scoped to this subagent only)
#     2. A string referencing an already-configured server name
#
#   Inline servers connect when the subagent starts and disconnect
#   when it finishes. String references share the parent session's
#   connection.
#
#   Inline definitions use the same schema as .mcp.json entries:
#   type: stdio | http | sse | ws
#
#   Tip: Define MCP servers inline here (instead of in .mcp.json)
#   to keep their tool descriptions out of the main conversation
#   context - only this subagent sees them.
#
#   Uncomment and customize:
# mcpServers:
#   # Inline definition - scoped to this subagent only
#   - my-custom-server:
#       type: stdio
#       command: npx
#       args: ["-y", "@example/mcp-server@latest"]
#   # Reference by name - reuses an already-configured server
#   - github

# ── LIFECYCLE HOOKS ──────────────────────────────────────────────────

# hooks (object, optional)
#   Lifecycle hooks scoped to this subagent. Only run while this
#   subagent is active; cleaned up when it finishes.
#
#   Supported events:
#     PreToolUse  - before the subagent uses a tool (matcher = tool name)
#     PostToolUse - after the subagent uses a tool (matcher = tool name)
#     Stop        - when the subagent finishes (auto-converted to
#                   SubagentStop at runtime; no matcher)
#
#   Hook format:
#     - matcher: "ToolName"           (regex; omit for all tools)
#       hooks:
#         - type: command
#           command: "./path/to/script.sh"
#
#   Hook scripts receive JSON via stdin with tool_input details.
#   Exit codes:
#     0 = allow (continue normally)
#     1 = error (hook itself failed; tool call still proceeds)
#     2 = BLOCK the tool call (error message from stderr fed to Claude)
#
#   Project-level hooks for SubagentStart/SubagentStop events go in
#   settings.json, not here. See: https://code.claude.com/docs/en/hooks
#
#   Uncomment and customize:
# hooks:
#   PreToolUse:
#     - matcher: "Bash"
#       hooks:
#         - type: command
#           command: "./scripts/validate-command.sh"
#   PostToolUse:
#     - matcher: "Edit|Write"
#       hooks:
#         - type: command
#           command: "./scripts/run-linter.sh"
#   Stop:
#     - hooks:
#         - type: command
#           command: "./scripts/cleanup.sh"
---

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  SYSTEM PROMPT (body below the frontmatter)                        ║
# ║                                                                     ║
# ║  This markdown body becomes the subagent's system prompt.          ║
# ║  The subagent receives ONLY this prompt (plus basic env details    ║
# ║  like working directory) - NOT the full Claude Code system prompt. ║
# ║  CLAUDE.md files and project memory still load normally.           ║
# ╚══════════════════════════════════════════════════════════════════════╝

You are a time-telling agent. Your sole purpose is to report the current date, time, and timezone when asked.

## Instructions

1. Run `date` via Bash to get the current system time
2. Report the result in a clear, human-friendly format
3. Include: day of week, full date, time with seconds, and timezone

## Template Variables Available in Agent/Skill Files

The following template variables are replaced BEFORE the prompt reaches Claude.
They work in both skill files (.claude/skills/) and agent files (.claude/agents/).

- **$ARGUMENTS** - all arguments the user passed (e.g., if invoked with
  extra context). If $ARGUMENTS is not present in the body, it is auto-appended
  as `ARGUMENTS: <value>`.
- **$ARGUMENTS[N]** - specific argument by 0-based index
  (e.g., $ARGUMENTS[0] for the first argument)
- **$0, $1, $2...** - shorthand for $ARGUMENTS[0], $ARGUMENTS[1], etc.
- **${CLAUDE_SESSION_ID}** - current session UUID (useful for logging)

### Skill-Only Variables (not available in agents)

These work only in .claude/skills/*/SKILL.md files, not in .claude/agents/:
- **${CLAUDE_SKILL_DIR}** - absolute path to the skill's directory

### Dynamic Context Injection (Preprocessing)

Use backtick-bang syntax to run shell commands BEFORE the prompt is sent to
Claude. The command output replaces the placeholder inline. This executes
during preprocessing, not during Claude's turn.

Syntax: !`command`

Examples that would be live in a real agent (commented out here to avoid
executing during template review):

<!-- !`date +%Z` would inject the current timezone abbreviation -->
<!-- !`git branch --show-current` would inject the current branch name -->
<!-- !`cat VERSION` would inject contents of a VERSION file -->

## Example Output Format

When the user asks for the time, respond like:

> **Current Time**
> Wednesday, March 25, 2026
> 2:45:03 PM MDT (UTC-6)

If the user provided arguments, acknowledge them: $ARGUMENTS

Session ID for logging: ${CLAUDE_SESSION_ID}
