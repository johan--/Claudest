# claude-claw

OpenClaw advisory and troubleshooting for Claude Code. One skill that answers OpenClaw questions, suggests optimal configuration, diagnoses issues, and guides design decisions using documentation and live state inspection.

## Why

OpenClaw configuration spans channels, gateways, providers, models, and automation rules across dozens of doc pages. Finding the right config key, understanding tradeoffs between setup options, and diagnosing why something isn't working requires cross-referencing multiple sources. This skill does that cross-referencing for you: it fetches the relevant docs via `clawdocs`, inspects live state via `openclaw` when available, and synthesizes a structured answer with exact config paths and CLI commands.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-claw@claudest
```

Requires `clawdocs` CLI for documentation lookups. `openclaw` CLI is optional but recommended for live state inspection and diagnostics.

## Skills

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

## License

MIT
