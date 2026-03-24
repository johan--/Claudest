# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3] - 2026-03-24

### Changed
- Reverted plugin name from claude-minds back to claude-thinking to avoid cache migration issues for existing users

## [0.3.0] - 2026-03-24

### Added
- council skill: multi-perspective deliberation with 6 cognitive personas (Architect, Skeptic, Pragmatist, Innovator, Advocate, Strategist)
- Adaptive question classification maps question type to most relevant personas
- Research-first instruction — agents investigate codebase files before forming positions
- Dialectical synthesis: consensus mapping, tension resolution, blind spot detection, confidence map
- /council command with flags: --quick (2), default (4), --full (6), --deep (Opus), --include/--exclude
- Reference files: perspectives.md, classification.md, synthesis.md, output-format.md

### Changed
- Renamed plugin from claude-thinking to claude-minds (reverted in 0.3.3)
- Updated description to reflect both brainstorm and council capabilities
- Version bump 0.2.2 → 0.3.0 (breaking: install command changes)

## [0.2.2] - 2026-03-10

### Changed
- Patch version bump by auto-version hook after version-badge correction commit

## [0.2.1] - 2026-03-10

### Changed
- Patch version bump by auto-version hook after docs refresh commit

## [0.2.0] - 2026-03-10

### Changed

- Version bump alongside all plugins; add auto-version hook support to plugin ecosystem
- Refresh README with current version badge

## [0.1.5] - 2026-02-23

### Fixed

- Add missing `name` field to brainstorm SKILL.md YAML frontmatter

## [0.1.4] - 2026-02-23

### Changed

- Rename skill from `thinking-partner` to `brainstorm` (verb-first convention)
- Expand README with domain calibration table, saturation detection docs, and output document placement details
- Update trigger phrases: replace "deep dive into" with "challenge my assumptions about"

## [0.1.2] - 2026-02-23

### Changed

- Expand README with installation instructions and Why section

## [0.1.1] - 2026-02-22

### Fixed

- Repair thinking-partner skill frontmatter and prompt structure

## [0.1.0] - 2026-02-22

### Added

- Initial release with thinking-partner skill
- Domain-calibrated interview questioning (technical, creative, business, personal, philosophical)
- Saturation detection after 4+ rounds with no new theme
- Synthesis document output with key themes, decisions, and open questions
