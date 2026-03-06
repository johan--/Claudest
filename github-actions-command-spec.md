# setup-github-actions Command Spec

## Overview

A user-invoked command in the `claude-coding` plugin that analyzes a project's existing `.github/workflows/` directory and generates correct, production-ready GitHub Actions workflows using `anthropics/claude-code-action`. It is a recommender + YAML writer: it surfaces what's missing or broken, gets user confirmation on what to create, and writes the files directly.

## Decisions & Positions

**Type**: Command (not skill). User-invoked via `/setup-github-actions`. No auto-trigger needed — frontmatter description is kept short (`Set up GitHub Actions workflows for this repo`). No session-startup token cost.

**Scope**: Claude Code actions only (`anthropics/claude-code-action`). General CI (Dependabot, CodeQL, release automation) is out of scope.

**Auth**: Never touch auth configuration. `/install-github-app` handles it. All generated YAML uses `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}` verbatim.

**Broken default detection**: The default `claude.yml` from `/install-github-app` has read-only permissions and no `prompt` or `claude_args`. The command detects this pattern, shows a diff of what changes, and asks before overwriting.

**Workflow menu**: Project-adaptive. Scans existing workflows, identifies what's already correctly set up, offers only what's missing.

**`track_progress`**: Always `true` for review and analysis workflows. Revisit if users report it as noisy.

**CLAUDE.md in CI**: Out of scope.

## Key Themes

### Permission Model — Output-Driven

Permissions follow what Claude needs to *write to*, not the workflow category:

| What Claude produces | Permission |
|---|---|
| Pushes commits, modifies files | `contents: write` |
| Posts PR comments, inline reviews | `pull-requests: write` |
| Labels, closes, or comments on issues | `issues: write` |
| Reads CI/test failure logs | `actions: read` |
| OAuth token auth | `id-token: write` (always) |

The interactive `@claude` workflow (`claude.yml`) primarily needs `contents: write` and `pull-requests: write`. It does NOT need `issues: write` unless it explicitly labels/comments on issues — the user clarified that `claude.yml` mostly runs in the background making code changes and commits.

### Tool Scope — Capability-Driven

`--allowedTools` scoped to minimum capability needed per workflow type:

- **Interactive `@claude`**: `Edit,Write,Read,Glob,Grep,Bash(git:*),Bash(gh pr:*),Bash(gh issue:*)`
- **PR review**: `Read,Glob,Grep,Bash(gh pr diff:*),Bash(gh pr view:*),Bash(gh pr comment:*),mcp__github_inline_comment__create_inline_comment`
- **Issue triage**: `Bash(gh issue view:*),Bash(gh issue list:*),Bash(gh issue edit:*),Bash(gh label:*)`
- **CI/test failure fix**: `Edit,Write,Read,Glob,Grep,Bash(git:*),Bash(gh:*)`

### PR Review Prompt — Language-Agnostic Discovery

Never hardcode language-specific review criteria. Start every review prompt with stack discovery, then apply relevant criteria for the detected stack. This makes the prompt work correctly for any project without user customization.

## Constraints & Boundaries

- Does NOT generate general CI workflows (Dependabot, CodeQL, release automation)
- Does NOT generate or modify auth configuration
- Does NOT generate or modify CLAUDE.md
- Does NOT use broad tool wildcards (`Bash(gh:*)` only for CI-fix workflows where gh scope is legitimately broad)
- Scope: `anthropics/claude-code-action` workflows only

## Open Questions

- None remaining from the interview. All design decisions are settled.
