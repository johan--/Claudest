# claude-claw ![v0.3.1](https://img.shields.io/badge/v0.3.1-blue?style=flat-square)

OpenClaw tools for Claude Code: advisory, troubleshooting, and skill authoring for OpenClaw. Two skills — one that answers OpenClaw questions, suggests configuration, diagnoses issues, and guides design decisions; another that generates well-structured OpenClaw skills and slash commands from scratch or by porting existing Claude Code skills.

## Why

OpenClaw configuration spans channels, gateways, providers, models, and automation rules across dozens of doc pages. Finding the right config key, understanding tradeoffs between setup options, and diagnosing why something isn't working requires cross-referencing multiple sources. This skill does that cross-referencing for you: it fetches the relevant docs via `clawdocs`, inspects live state via `openclaw` when available, and synthesizes a structured answer with exact config paths and CLI commands.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-claw@claudest
```

Requires `clawdocs` CLI for documentation lookups. `openclaw` CLI is optional but recommended for live state inspection and diagnostics.

## Skills

| Skill | Purpose |
|-------|---------|
| [claw-advisor](#claw-advisor) | Answer OpenClaw questions, diagnose issues, guide configuration |
| [create-claw-skill](#create-claw-skill) | Generate or port OpenClaw skills and slash commands |

### claw-advisor

Answer OpenClaw questions, suggest optimal configuration, diagnose issues, and guide design decisions. Uses two backends: `clawdocs` for documentation and `openclaw` for live state inspection.

Classifies questions into four types: focused (single topic, one doc fetch), broad (cross-cutting, parallel subagent research across multiple doc areas), troubleshooting (diagnostic plus docs, cross-referenced with `openclaw doctor` output), and design (architectural decisions with option comparison on the same dimensions). Broad questions spawn up to four parallel subagents to research different topic areas simultaneously, then reconverge into a single structured response.

Responses follow a consistent structure: direct answer first, then exact configuration with full dot-paths and CLI commands, context on why the configuration is recommended, gotchas from the docs, and source slugs for deeper reading. Never invents config keys or flags — only cites fetched documentation.

Triggers on: "how do I configure OpenClaw", "set up telegram in OpenClaw", "gateway configuration", "OpenClaw troubleshooting", "claw advisor", "what's the best way to set up OpenClaw", "OpenClaw docs", "help me with OpenClaw", "openclaw channel setup", "debug OpenClaw".

**Prerequisites:**

```bash
# Documentation (required)
# clawdocs CLI must be installed and on PATH

# Live state inspection (optional)
# openclaw CLI — needed for status, doctor, config, and health commands
```

### create-claw-skill

Generate well-structured OpenClaw skills or slash commands. Supports two modes: authoring new skills from scratch via an interview workflow, and porting existing Claude Code skills by translating tool names, path conventions, and frontmatter fields to the OpenClaw/pi-coding-agent spec.

Walks through four phases: requirements gathering (or automatic translation in port mode), generation with frontmatter validation and script scaffolding, delivery to workspace or managed skill directories, and quality evaluation. Includes helper scripts for directory initialization (`init_claw_skill.py`) and validation (`validate_claw_skill.py`), plus reference docs for frontmatter options, script patterns, and Claude Code-to-OpenClaw tool name mappings.

Triggers on: "create an OpenClaw skill", "make a claw skill", "build a skill for OpenClaw", "write a SKILL.md for openclaw", "port a skill to OpenClaw", "convert a Claude Code skill to claw", "generate openclaw skill frontmatter".

**Prerequisites:**

```bash
# Documentation (recommended)
# clawdocs CLI — used to fetch latest skill spec before generating

# Validation scripts included in plugin
# No additional dependencies beyond Python 3.7+ stdlib
```

## License

MIT
