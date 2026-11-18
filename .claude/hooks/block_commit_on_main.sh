#!/usr/bin/env bash
# PreToolUse hook (Bash tool): guard `git commit`. Two checks:
#   1. Block while the current branch is main or master (CLAUDE.md section 8, ADR-0003).
#   2. Block when a raw meeting transcript under _transcripts/ (anything but its README.md)
#      is staged, or the command itself names one, which catches `git add -f ... && git commit`
#      (ADR-0004, _transcripts/README.md).
#
# Reads the hook JSON from stdin, extracts tool_input.command, and if it contains a
# `git commit` invocation that fails a check, explains why on stderr and exits 2
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

# --- Check 2: raw meeting transcripts must never be committed ---
transcript_hit=""
# Paths the command names directly, e.g. `git add -f _transcripts/x.vtt && git commit ...`.
# Glob characters are excluded so a message such as "ignore _transcripts/*" does not match.
if printf '%s\n' "$cmd" | grep -oE '_transcripts/[^[:space:]"'"'"';|&)*?]+' \
    | grep -vqx '_transcripts/README\.md'; then
  transcript_hit="the command names a file under _transcripts/"
fi
# Paths already staged in the index.
if [ -z "$transcript_hit" ] && [ -n "$GIT" ]; then
  staged="$("$GIT" -C "$repo_dir" diff --cached --name-only -- '_transcripts/' 2>/dev/null \
    | grep -vx '_transcripts/README\.md')"
  [ -n "$staged" ] && transcript_hit="staged: $(printf '%s' "$staged" | tr '\n' ' ')"
fi
if [ -n "$transcript_hit" ]; then
  cat >&2 <<MSG
BLOCKED: raw meeting transcripts in _transcripts/ must never be committed
($transcript_hit).

Unstage them and commit again:
  git restore --staged _transcripts/
  git add _transcripts/README.md   (only if you changed the README)

Transcripts stay local; meeting notes in 99_references/meetings/ refer to them by path.
See _transcripts/README.md and ADR-0004.
MSG
  exit 2
fi

# --- Check 1: current branch ---
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
