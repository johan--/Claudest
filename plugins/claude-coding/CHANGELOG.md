# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-03-10

### Changed
- Patch version bump by auto-version hook after docs refresh commit

## [0.2.0] - 2026-03-10

### Added
- Add `update-readme` skill to refresh existing README files against current codebase state, git history, and changelog content
- Add `make-readme` skill (renamed from `readme-maker`) for generating professional READMEs through a structured interview
- Add `make-changelog` skill for creating or updating CHANGELOG.md from git history using Keep-a-Changelog format
- Add `update-claudemd` skill to audit and optimize project CLAUDE.md files
- Add `push-pr` skill with multi-PR scope analysis, automatic branch management, and PR body generation
- Add `commit` skill for intelligent file grouping and conventional commit message generation
- Add `clean-branches` skill for safely removing merged and stale git branches with confirmation
- Add `setup-github-actions` command to analyze existing workflows and generate production-ready Claude Code GitHub Actions workflows

### Changed
- Rename skills to `make-*` convention (e.g. `readme-maker` → `make-readme`, `changelog-maker` → `make-changelog`) for consistency
- Rename all skills and commands to verb-first convention
- Improve `update-claudemd` skill with more accurate codebase verification and rewrite logic
- Repair `commit` skill per audit findings and fix script paths
- Repair `clean-branches` skill YAML frontmatter and execution modifiers
- Bump version to 0.2.0 to reflect new `setup-github-actions` command and accumulated feature additions

### Fixed
- Fix YAML frontmatter issues across `clean-branches` and other skills
- Fix script path references in commit skill after directory restructuring
- Fix non-destructive branch management and use origin-based comparisons in `push-pr` (v0.1.12)
- Fix Bash tool scoping and add `context:fork` to `update-readme`
- Fix YAML frontmatter and add haiku model constraint with `AskUserQuestion` guard across skills
