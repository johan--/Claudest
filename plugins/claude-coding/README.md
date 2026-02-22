# claude-coding

Git workflow skills for Claude Code. Three skills covering the full coding commit loop: stage and commit with conventional format, push and open a PR with smart branch handling, and safely prune merged or stale branches.

## Why

Git operations during a coding session have a lot of small decisions that slow you down: which files belong in the same commit, whether to split concerns into separate commits, whether you're on the right branch before pushing, what base branch to target. These skills encode the right defaults so Claude handles those decisions consistently — and asks when it genuinely can't.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-coding@claudest
```

Requires `git` and `gh` CLI (for push-pr). Both must be authenticated.

## Skills

### commit

Analyze and commit changes with intelligent file grouping and conventional commits. Reads `git status` and `git diff`, groups files by purpose rather than directory, validates if a linter is configured, and writes a conventional commit message (`feat`, `fix`, `docs`, etc.). Handles temporary file exclusion, multi-concern splits, and optional push in one flow.

Triggers on: "commit my changes", "commit this", "git commit", "save my work", "stage and commit", "create a commit", "commit what I've done".

### push-pr

Push commits and create or update pull requests with automatic branch management. Detects if you're on `main` with unpushed commits and cuts a feature branch before pushing. Creates new PRs or comments on existing ones. Calls the `commit` skill first if there are uncommitted changes.

Triggers on: "push this", "push my changes", "create a PR", "open a pull request", "make a PR", "submit for review", "send this up", "open PR", "pr please".

### clean-branches

Safely remove merged and stale git branches with confirmation. Finds branches already merged into main and branches with no commits in 30+ days, shows them categorized, and asks before deleting anything. Never touches protected branches. Remote deletion requires explicit confirmation.

Triggers on: "clean up branches", "delete merged branches", "prune stale branches", "git branch cleanup", "remove old branches".
