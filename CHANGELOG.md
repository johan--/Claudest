# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-02-23

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
