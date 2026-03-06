---
description: Set up GitHub Actions workflows for this repo
tools:
  - Read
  - Glob
  - Bash
  - Write
  - AskUserQuestion
---

# Setup GitHub Actions

Analyze the project's existing `.github/workflows/` and generate correct, production-ready GitHub Actions workflows using `anthropics/claude-code-action`.

## Principles

These govern every workflow generated. Apply them rather than copying templates.

### Permission Model — Output-Driven

Grant only the permissions Claude needs to write to. Never over-permission.

| What Claude produces | Permission required |
|---|---|
| Pushes commits, modifies files | `contents: write` |
| Posts PR comments, inline reviews, updates PR description | `pull-requests: write` |
| Labels, closes, or comments on issues | `issues: write` |
| Reads CI/test failure logs | `actions: read` |
| OAuth token auth | `id-token: write` (always required) |

The interactive `@claude` workflow (`claude.yml`) primarily needs `contents: write` and `pull-requests: write`. It does NOT need `issues: write` unless it explicitly labels or comments on issues — it mostly runs in the background making code changes and commits.

### Tool Scope — Capability-Driven

Scope `--allowedTools` to exactly the minimum tools needed. Never use broad wildcards unless the workflow legitimately needs broad access.

| Workflow type | Allowed tools |
|---|---|
| Interactive `@claude` (code changes + commits) | `Edit,Write,Read,Glob,Grep,Bash(git:*),Bash(gh pr:*),Bash(gh issue:*)` |
| PR review (read + post comments only) | `Read,Glob,Grep,Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh pr comment:*),mcp__github_inline_comment__create_inline_comment` |
| Issue triage (label + comment) | `Bash(gh issue view:*),Bash(gh issue list:*),Bash(gh issue edit:*),Bash(gh label:*)` |
| CI/test failure auto-fix | `Edit,Write,Read,Glob,Grep,Bash(git:*),Bash(gh:*)` |

### Auth

Always use `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`. Do not add, change, or generate auth configuration — it is set up separately by `/install-github-app`.

### PR Review Prompt — Language-Agnostic

Never hardcode language or framework-specific review criteria. Always begin the review prompt with stack discovery so the review applies correctly to any project:

```
First, identify the tech stack by reading package.json, pyproject.toml,
Cargo.toml, go.mod, or equivalent config files. Then perform a thorough
code review appropriate for that stack, covering: security, error handling,
performance, test coverage, and documentation — using the conventions of
the detected language/framework. Post inline comments for specific issues
and a top-level comment for overall assessment.
```

### Progress Tracking

Set `track_progress: true` for all review and analysis workflows.

## Workflow

### Step 1 — Analyze

Scan existing workflows:

```bash
ls .github/workflows/ 2>/dev/null
cat .github/workflows/*.yml 2>/dev/null
```

**Pre-check:** If `.github/workflows/` does not exist or contains no `.yml` files, stop. Tell the user:

> No GitHub Actions workflows were found. `/setup-github-actions` configures Claude Code workflows, but the GitHub App and initial workflow skeleton need to exist first. Run `/install-github-app` to complete that setup, then re-run `/setup-github-actions`.

Do not proceed past this point until the user has run `/install-github-app`.

For each `.yml` found, classify:
- **Broken default**: Uses `anthropics/claude-code-action@v1`, all permissions are `read`, no `prompt` or `claude_args` configured — this is the vanilla skeleton installed by `/install-github-app`. Flag it prominently.
- **Existing Claude Code workflow**: Already correctly configured for a specific purpose. Note what it covers.
- **Other CI**: Present but unrelated to Claude Code. Note as present, no action needed.

### Step 2 — Present Adaptive Menu

Tell the user:
1. What was found (existing workflows, broken default if detected)
2. What Claude Code workflow types are missing

If a broken default is detected, surface it first — it is the highest priority fix.

Use AskUserQuestion (multiSelect) to let the user pick which workflows to set up. Offer only what is NOT already correctly configured:

| Workflow | Trigger | What Claude does |
|---|---|---|
| **Interactive assistant** (`claude.yml`) | `@claude` mentions in issues/PRs/comments | Makes code changes, commits, responds to requests |
| **PR code review** (auto) | Every PR opened/updated | Reviews all PRs automatically on open/sync/reopen |
| **PR review — external contributors** | PRs from non-team members | Reviews only external/first-time contributor PRs |
| **PR review — filtered paths** | PRs touching specific file paths | Reviews only when specified files change |
| **Issue triage** | Issue opened | Auto-labels and categorizes new issues |
| **Issue deduplication** | Issue opened | Finds and flags duplicate issues |
| **CI failure auto-fix** | CI workflow fails | Creates a fix branch when CI breaks |
| **Test failure analysis** | Test run fails | Posts analysis of test failures as a PR comment |
| **Manual code analysis** | `workflow_dispatch` | On-demand analysis triggered manually from the Actions tab |

### Step 3 — Generate and Write

**For broken default upgrade**: Show the diff — what permissions change, what `claude_args` gets added. Ask for confirmation before overwriting.

**For each selected workflow**: Generate YAML applying the principles above, write to `.github/workflows/<name>.yml`.

Structural template — adapt permissions, tools, prompt, trigger, and job name per workflow:

```yaml
name: <Descriptive Name>

on:
  <trigger>:
    types: [<events>]

jobs:
  <job-name>:
    runs-on: ubuntu-latest
    permissions:
      contents: <read|write>        # write only if Claude pushes commits
      pull-requests: <read|write>   # write only if Claude posts PR comments/reviews
      issues: <read|write>          # write only if Claude labels or comments on issues
      id-token: write               # always required for OAuth token auth
      actions: read                 # only if Claude reads CI/test logs

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - name: <Action Name>
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          track_progress: true
          prompt: |
            <prompt — use language-agnostic discovery pattern for review workflows>
          claude_args: |
            --allowedTools "<minimum capability-scoped tools>"
```

### Step 4 — Summarize

After writing all files, list:
- What was created (filename, workflow name)
- What trigger activates each workflow
- What Claude is allowed to do in each (based on permissions + tools granted)
