# claude-thinking

![v0.2.1](https://img.shields.io/badge/v0.2.1-blue?style=flat-square)

Structured thinking tools for Claude Code. Skills that use dialogue to help you clarify, stress-test, and articulate ideas — then produce a written artifact.

## Why

Some of the best thinking happens in conversation, but unstructured conversation wanders. These skills provide just enough framework to keep the dialogue productive: domain-calibrated questioning intensity, saturation detection so it knows when to stop, and structured output so the results are reusable. The goal is a thinking partner that adapts its approach to the domain rather than applying one interviewing style to everything.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-thinking@claudest
```

## Skills

### brainstorm

In-depth interview to clarify, stress-test, and articulate ideas. Calibrates questioning style to the domain — adversarial for strategy, gentle for personal decisions, Socratic for abstract topics. Produces a synthesis document (spec, brief, decision doc, reflection) with key themes, decisions, and open questions. No raw Q&A transcript — user quotes are woven into the synthesis where they're apt.

Triggers on: "interview me about", "help me clarify", "stress-test my idea", "let's explore this concept", "challenge my assumptions about", "probe my assumptions".

Domain calibration:

| Domain | Approach |
|--------|----------|
| Technical/coding | Moderate depth — focus on requirements, edge cases, architectural decisions |
| Creative projects | Explore vision, constraints, audience, emotional intent with more breadth |
| Business/strategy | Probe assumptions, market dynamics, risks, second-order effects. Challenge more. |
| Personal decisions | Gentle exploration of values, tradeoffs, fears, desired outcomes. Less adversarial. |
| Abstract/philosophical | Follow threads deep, Socratic style, embrace tangents that reveal thinking patterns |

Saturation detection: after 4+ rounds with no new theme, or 3+ rounds of consecutively shorter answers, the skill proposes closure with a summary of key themes and underexplored areas.

Output document: technical/coding topics land at `./[topic-slug]-spec.md` in the project root; personal/general topics at `~/interviews/[topic-slug].md`. The suffix adapts to content type — "spec" or "requirements" for features, "brief" or "vision" for creative work, "decision doc" or "analysis" for strategy, "reflection" or "exploration" for personal topics.

Runs on: Claude Opus. Tools: Read, Write, AskUserQuestion.

## Roadmap

Planned skills tracked in [`docs/skill-ideas.md`](docs/skill-ideas.md):

| Skill | Description |
|-------|-------------|
| decision-journal | Structured decision logging with revisitation and predicted-vs-actual tracking |
| rubber-duck | Explain-your-code dialogue that surfaces implicit assumptions and hidden complexity |
| pre-mortem | Prospective hindsight analysis — work backwards from failure to identify risks |
| steelman | Build the strongest counter-argument to stress-test your own position |

## License

MIT — see [LICENSE](../../LICENSE) if present, otherwise standard MIT terms apply.
