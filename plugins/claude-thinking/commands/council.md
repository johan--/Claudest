---
description: Run a multi-perspective deliberation council
allowed-tools: [Agent, Read, Glob, Grep, AskUserQuestion]
argument-hint: "<question> [--quick|--full|--deep] [--include name,name] [--exclude name,name]"
---

# /council

Run a council of cognitive personas to deliberate on a question. Each persona investigates relevant codebase files before forming a position. Results are synthesized into an opinionated verdict.

## Flag Reference

| Flag | Effect |
|------|--------|
| `--quick` | 2 perspectives (fastest, cheapest) |
| (default) | 4 perspectives |
| `--full` | All 6 perspectives |
| `--deep` | Use Opus model for agents instead of Sonnet |
| `--include name,name` | Force-include specific personas |
| `--exclude name,name` | Force-exclude specific personas |

Persona names: architect, skeptic, pragmatist, innovator, advocate, strategist.

## Execution

Parse `$ARGUMENTS` for the question and any flags listed above. Then execute the council workflow:

1. Load classification rules from `${CLAUDE_PLUGIN_ROOT}/skills/council/references/classification.md`
2. Classify the question type by matching keywords and intent
3. Load persona definitions from `${CLAUDE_PLUGIN_ROOT}/skills/council/references/perspectives.md`
4. Select the top N personas for the classified type (N from flags). Advocate always included unless `--exclude advocate`
5. Announce the council composition to the user (question type, members, size) — 3-4 lines max
6. Build each agent's prompt: full persona definition + the user's question + research-first instruction ("use Read, Glob, Grep to investigate relevant codebase files before forming your position") + output requirements (300-500 words, H/M/L confidence)
7. Launch ALL agents in a single message for parallel execution using the Agent tool. Use `model: "sonnet"` (or `"opus"` if `--deep`)
8. After all agents return, synthesize using `${CLAUDE_PLUGIN_ROOT}/skills/council/references/synthesis.md`
9. Format the report using `${CLAUDE_PLUGIN_ROOT}/skills/council/references/output-format.md` (template matching council size)
10. Ask the user if they want to act on the top recommendation
