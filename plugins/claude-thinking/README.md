# claude-thinking

Structured thinking tools for Claude Code. Skills that use dialogue to help you clarify, stress-test, and articulate ideas — then produce a written artifact.

## Why

Some of the best thinking happens in conversation, but unstructured conversation wanders. These skills provide just enough framework to keep the dialogue productive: domain-calibrated questioning intensity, saturation detection so it knows when to stop, and structured output so the results are reusable. The goal is a thinking partner that adapts its approach to the domain rather than applying one interviewing style to everything.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-thinking@claudest
```

## Skills

### thinking-partner

In-depth interview to clarify, stress-test, and articulate ideas. Calibrates questioning style to the domain — adversarial for strategy, gentle for personal decisions, Socratic for abstract topics. Produces a synthesis document (spec, brief, decision doc, reflection) with key themes, decisions, and open questions. No raw Q&A transcript — user quotes are woven into the synthesis where they're apt.

Triggers on: "interview me about", "help me clarify", "stress-test my idea", "let's explore this concept", "deep dive into", "probe my assumptions".
