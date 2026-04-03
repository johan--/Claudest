---
name: get-pr-comments
description: >
  This skill should be used when the user says "get PR comments", "show PR feedback",
  "what comments on my PR", "PR review comments", "show me the review", "what did
  reviewers say", or asks about feedback on a pull request. Not for creating PRs or
  responding to comments.
allowed-tools:
  - Bash(gh:*)
  - Bash(python3:*)
  - Read
  - Grep
  - AskUserQuestion
argument-hint: "[PR number or URL]"
---

# Get PR Comments

Fetch, organize, and present all comments on a GitHub pull request — issue-level
comments, review bodies, and inline review comments — grouped by human vs bot,
with actionable items (must-fix, optional) extracted from structured reviews
and inline comments. Deduplicates repeated items across iterative review rounds.

## Pre-Flight Context

- Current branch: `!git rev-parse --abbrev-ref HEAD`
- Repo: `!gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || echo "unknown"`

## Workflow

### 1. Identify the PR

Parse `$ARGUMENTS` for a PR number or URL. If present, use it directly.

If no arguments provided, attempt to detect from the current branch:

```bash
gh pr view --json number,title --jq '"\(.number) — \(.title)"' 2>/dev/null
```

If that succeeds, use the detected PR. If it fails (no PR for current branch), list
open PRs and ask the user to pick:

```bash
gh pr list --state open --limit 10 --json number,title,headRefName --jq '.[] | "\(.number)\t\(.title)\t(\(.headRefName))"'
```

Present options via AskUserQuestion. If only one open PR exists, use it directly.

### 2. Fetch comments

Run the fetch script with the resolved PR number:

```bash
python3 $SKILL_DIR/scripts/fetch_pr_comments.py <PR_NUMBER> --output json
```

Exit 0 = proceed. Exit 2 = `gh` auth or network error — report to user.

### 3. Present results

Parse the JSON output. Present in this order:

**Summary line**: PR number, total comment count, human vs bot breakdown.

**Actionable items first** (if any extracted from review bodies or inline comments):
- Must-fix items with source reviewer, content, and `file:line` if from inline comment
- Optional suggestions with source reviewer and content
- Items are deduplicated across review rounds — repeated carry-forwards are collapsed

**Human comments**: grouped chronologically. For inline comments, include
`file:line` reference for navigation.

**Bot comments**: in a separate section. For inline comments, include
`file:line` reference. For review bodies, include the review state
(APPROVED, CHANGES_REQUESTED, COMMENTED).

### 4. Suggest next steps

After presenting comments, offer context-appropriate actions:

- If must-fix items exist: "Want me to address these must-fix items?"
- If inline comments reference specific files: "Want me to read the referenced
  files and check if these issues are already resolved?"
- If the PR is the user's: "Want me to respond to any of these comments?"
