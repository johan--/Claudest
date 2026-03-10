# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-10

### Changed
- Patch version bump by auto-version hook after docs refresh commit

## [0.3.0] - 2026-03-10

### Changed
- Refresh README with current version badge and rebuild CHANGELOG with entries for 0.1.0–0.2.1

## [0.2.1] - 2026-02-27

### Added
- Port mode in create-claw-skill: translates existing Claude Code skills to OpenClaw spec automatically (frontmatter, tool names, path conventions)
- Tool name translation table (Claude Code → OpenClaw) in references/claw-patterns.md
- Validation checklist and quality scoring rubric (Phase 4 evaluate)

### Changed
- Aligned create-claw-skill with pi-coding-agent / OpenClaw AgentSkills spec

## [0.2.0] - 2026-02-24

### Added
- create-claw-skill: generate well-structured OpenClaw skills and slash commands from scratch or by porting existing Claude Code skills
- Four-phase workflow: requirements gathering, generation, delivery, quality evaluation
- Helper scripts: init_claw_skill.py (directory scaffolding), validate_claw_skill.py (frontmatter/structure validation)
- Reference docs: frontmatter-options.md, script-patterns.md, claw-patterns.md
- Example minimal command in examples/sample-command/SKILL.md

## [0.1.0] - 2026-02-23

### Added
- Initial release with claw-advisor skill
- Answer OpenClaw questions, diagnose issues, guide configuration decisions
- Two backends: clawdocs CLI (documentation) and openclaw CLI (live state inspection)
- Four question types: focused, broad, troubleshooting, design
- Parallel subagent research for broad questions (up to 4 agents)
- Topic routing via references/topic-routing.md
