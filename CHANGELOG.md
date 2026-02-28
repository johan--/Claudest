# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Add "Editing Failure Modes" section to generate-image editing-guide covering color label drift, high-contrast swap targets, Gemini camera move limitation, multi-pass editing, and base scene contamination (claude-content v0.3.1)
- Add "Fashion & Garment Editing" section to generate-image capability-patterns with base selection criteria, garment swap prompt patterns, texture rendering, and multi-step edit workflows
- Add "Working from Video References" section to generate-image capability-patterns with two-pass ffmpeg frame extraction and scene detection guidance

### Changed
- Expand generate-image i2i pre-generation checklist with three new guards: color label conflicts, accessory contamination, and single-change-per-prompt discipline (claude-content v0.3.1)
- Extend generate-image thinking mode guidance to cover i2i multi-reference composition (3+ images), text/sign placement, and complex spatial edits

### Added
- Add discovery validation, edge case testing, and description quality rules to skill-lint in claude-skills (v0.2.0)
- Add repair-agent skill to claude-skills for auditing and improving agent SKILL.md files
- Add create-claw-skill to claude-claw for OpenClaw ecosystem skill authoring with full OpenClaw adaptation

### Changed
- Refactor create-skill and create-agent workflows: remove live documentation fetching, establish reference files as authoritative sources, restructure phases and delivery steps, replace brainstorm delegation with user interviews
- Update Bash tool scopes in clean-branches to restrict to git and python3 operations
- Add context:fork to update-readme skill for isolated parallel research workflow

### Fixed
- Remove context:fork rule from improve-skill Phase 2d (structural configuration belongs in repair-skill)
- Remove redundant agent:general-purpose defaults from commit, make-changelog, and update-readme skills
- Correct context:fork and agent: frontmatter semantics in repair-skill and create-skill documentation

---

### Added
- Add create-agent skill to claude-skills with scripts, references, and examples (v0.1.9)
- Add language selection to create-cli skill (claude-skills v0.1.8)
- Add one-command installers for reddit-cli and brave-cli in run-research skill
- Add claude-claw plugin (v0.1.0) with claw-advisor skill for OpenClaw configuration, troubleshooting, and guidance
- Add create-cli skill for structured agent-aware command-line application design
- Add update-readme skill for automated README refresh using codebase state and git history
- Overhaul youtube-research with adaptive multi-round discovery pipeline featuring parallel Task agents and niche-first heuristics
- Add improve-skill to claude-skills alongside create-skill and repair-skill (v0.1.4)
- Add make-changelog skill and rename skills to make-* convention in claude-coding (v0.1.8)
- Add readme-maker skill to claude-coding (v0.1.5)
- Migrate deep-research and youtube-research into dedicated claude-research plugin
- Add claude-content plugin with ffmpeg-based content creation skills (compress-video, convert-video, make-gif, share-social, extract-audio, generate-image)
- Add claude-thinking plugin with brainstorm skill
- Add updateclaudemd skill to claude-coding (v0.1.4)
- Add push-pr skill with multi-PR scope analysis and PR body script to claude-coding
- Add commit and clean-branches skills to claude-coding git workflow plugin
- Add claude-skills plugin with create-skill and repair-skill
- Add past-conversations and extract-learnings skills to claude-memory for conversation recall and knowledge synthesis
- Add branch-level full-text search index for improved session search performance
- Add tool usage tracking and reporting in conversation memory (v0.3.0)
- Add cross-platform FTS fallback support for improved compatibility
- Add claude-utilities plugin with convert-to-markdown skill
- Add extract-learnings skill for distilling conversation learnings into persistent memory (v0.6.0)
- Add comprehensive test suite for claude-memory with pytest

### Changed
- Rename all skills and commands to verb-first convention for consistent imperative naming across plugins (recall-conversations, manage-memory, convert-to-markdown, brainstorm, run-research, search-youtube, generate-image, compress-video, convert-video, make-gif, share-social, extract-audio)
- Improve create-cli with agent-aware design patterns
- Implement security hardening and performance improvements in claude-memory (v0.7.0)
- Migrate to v3 schema with branch-aware conversation storage for better context tracking
- Filter teammate messages and task notifications from injected context to reduce noise (v0.7.1)
- Refactor past-conversations skill with reference extraction and improved formatting
- Repair and improve multiple skills per audit findings (extract-learnings, web-to-markdown, skill-creator, skill-repair, thinking-partner, clean-branches, commit)
- Split memory_utils into modular package structure (db.py, content.py, parsing.py, formatting.py)
- Add shared utilities, settings, and logging support to claude-memory

### Fixed
- Repair YAML frontmatter parse errors in brainstorm, clean-branches, and create-skill skills (claude-thinking 0.1.5, claude-coding 0.1.10, claude-skills 0.1.6)
- Fix foreign key crash on conversation reimport and add versioned data migrations (v0.7.2)
- Handle None channel gracefully in YouTube research format_entry
- Escape dynamic syntax pattern in skill documentation to prevent parsing errors
- Remove redundant name field from skill frontmatter

## [2026-02-23]

### Changed
- Rename all skills and commands to verb-first convention across 5 plugins: recall-conversations, manage-memory, convert-to-markdown, brainstorm, run-research, search-youtube, generate-image, compress-video, convert-video, make-gif, share-social, extract-audio

### Added
- Add YouTube research skill with yt-dlp integration to claude-utilities
- Add claude-content plugin with content creation skills (ffmpeg suite)
- Add claude-thinking plugin with thinking-partner skill
- Add claude-research plugin with deep-research and youtube-research capabilities
- Add updateclaudemd skill to claude-coding for maintaining CLAUDE.md files
- Add readme-maker skill to claude-coding for automated documentation generation
- Add commit, push-pr, and clean-branches skills to claude-coding for git workflows
- Add skill-creator and skill-repair skills to claude-skills plugin
- Add past-conversations and extract-learnings skills to claude-memory for conversation recall and knowledge synthesis
- Add branch-level full-text search index for improved session search performance
- Add tool usage tracking and reporting in conversation memory

### Changed
- Standardize claude-coding skills to make-* naming convention
- Repair and improve multiple skills per audit findings (extract-learnings, past-conversations, web-to-markdown, skill-creator, skill-repair, thinking-partner)
- Refactor past-conversations skill with reference extraction and improved formatting
- Implement security hardening and performance optimizations in claude-memory (v0.7.0)
- Add cross-platform support with FTS fallback for improved compatibility
- Migrate to v3 schema with branch-aware conversation storage for better context tracking
- Filter teammate messages and task notifications from injected context to reduce noise

### Fixed
- Handle None channel gracefully in YouTube research format_entry
- Prevent foreign key constraint crash on conversation reimport
- Remove redundant name field from skill frontmatter
- Escape dynamic syntax pattern in skill documentation to prevent parsing errors
