#!/usr/bin/env bash
# PreToolUse hook (Bash tool): block `git commit` while the current branch is main or master.
# See CLAUDE.md section 8 (Git Workflow) and ADR-0003.
#
# Reads the hook JSON from stdin, extracts tool_input.command, and if it contains a
# `git commit` invocation while the repo is on main or master, explains why on stderr and exits 2
# (which blocks the tool call and feeds the message back to the agent). Otherwise exits 0.
#
# Testing: BLOCK_COMMIT_TEST_BRANCH=<name> overrides the detected branch.

set -u

input="$(cat)"

# --- Extract tool_input.command (jq preferred, sed fallback) ---
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)"
  hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)"
else
  cmd="$(printf '%s' "$input" | tr '\n' ' ' \
    | sed -nE 's/.*"command"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p')"
  hook_cwd="$(printf '%s' "$input" | tr '\n' ' ' \
    | sed -nE 's/.*"cwd"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p')"
fi

[ -z "$cmd" ] && exit 0

# --- Does the command invoke `git commit`? ---
# Matches `git commit`, `/path/to/git commit`, `git -C <path> commit`, `git commit` after `&&` or
# `;`, and git invoked through a shell variable (`$G commit`, `${G} -C <path> commit`).
# Does not match `git log`, `git merge`, or `git commit-tree`.
commit_re='(^|[^[:alnum:]_.-])(git|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?)([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit([^[:alnum:]_-]|$)'
printf '%s\n' "$cmd" | grep -Eq "$commit_re" || exit 0

# --- Resolve a working git binary ---
GIT=""
if command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then
  GIT="git"
fi

# --- Which repo? `git -C <path>` target, else the session cwd, else the project dir ---
repo_dir=""
c_path="$(printf '%s\n' "$cmd" \
  | sed -nE 's/.*(^|[^[:alnum:]_.-])(git|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?)[[:space:]]+-C[[:space:]]+([^[:space:]]+)[[:space:]]+commit.*/\3/p' \
  | head -n 1 | sed -E "s/^[\"']//; s/[\"']$//")"
if [ -n "$c_path" ]; then
  case "$c_path" in
    /*) repo_dir="$c_path" ;;
    *) repo_dir="${hook_cwd:-${CLAUDE_PROJECT_DIR:-$PWD}}/$c_path" ;;
  esac
fi
[ -z "$repo_dir" ] && repo_dir="${hook_cwd:-${CLAUDE_PROJECT_DIR:-$PWD}}"

# --- Current branch ---
if [ -n "${BLOCK_COMMIT_TEST_BRANCH:-}" ]; then
  branch="$BLOCK_COMMIT_TEST_BRANCH"
elif [ -n "$GIT" ]; then
  branch="$("$GIT" -C "$repo_dir" symbolic-ref --short -q HEAD 2>/dev/null)"
else
  exit 0  # no usable git; cannot tell, do not block
fi

if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  cat >&2 <<'MSG'
BLOCKED: direct commits on the default branch (main/master) are not allowed in this repo.

Create a short-lived branch first, then commit there:
  git switch -c <type>/<short-kebab-topic>
  (type = content | chore | fix, e.g. content/atomic-notes-concept)

Merging to main (git merge --no-ff <branch>) and pushing require the user's explicit
go-ahead. To finish a merge conflict, use `git merge --continue`, not `git commit`.
See CLAUDE.md section 8 (Git Workflow) and ADR-0003.
MSG
  exit 2
fi

exit 0
