# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-03-10

### Changed
- Patch version bump by auto-version hook after docs refresh commit

## [0.2.0] - 2026-03-10

### Added
- Add one-command installers for reddit-cli and brave-cli in run-research skill
- Add adaptive multi-round YouTube discovery pipeline with niche-first heuristics (search-youtube research mode)
- Improve yt_research.py to v0.2.0 with 11 agent-aware CLI fixes and well-defined exit codes
- Migrate deep-research and youtube-research skills into dedicated claude-research plugin

### Changed
- Rename skills to verb-first convention (run-research, search-youtube) for consistency across plugin
