# claude-skills

Skill authoring tools for Claude Code. Three complementary skills: one generates skills from scratch, one audits for structural correctness, one improves for effectiveness.

## Why

Writing a good Claude Code skill is harder than it looks. The description has to be precise enough to route reliably while being dense enough to not waste tokens on every session it doesn't trigger. The body has to be tight enough for consistent outcomes but not so prescriptive that it suppresses the model's ability to generalize. Workflow steps that should be deterministic scripts get left as inline prose that the model re-generates differently on each run. And most skills that "work" are missing infrastructure — reference files for domain-specific data, scripts for fragile operations, examples for outputs users will adapt — that would make them substantially better.

These three skills exist to close that gap: `create-skill` generates skills with these properties built in, `repair-skill` diagnoses structural violations, and `improve-skill` tests effectiveness against user goals.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-skills@claudest
```

No dependencies. Both skills work with whatever Claude model is running.

## Skills

### create-skill

Generate a new skill or slash command from requirements. Triggers on phrases like "create a skill", "make a command", "write a slash command", "add a skill to a plugin", "improve skill description", or "write skill frontmatter".

The skill interviews you about requirements (or reads them from `$ARGUMENTS`), fetches the latest Claude Code documentation before generating, and works through a structured generation process:

Phase 1 gathers requirements: primary objective, trigger scenarios, inputs and outputs, complexity, and execution needs. Phase 2 generates the skill with correct frontmatter, description principles (third-person framing, verbatim trigger phrases, `>` scalar, density over coverage), body structure, and progressive disclosure. Before finalizing, it runs a script opportunity scan across every workflow step: five signal patterns identify steps that should be proper CLI tools — parameterized scripts designed for both Claude invocation and direct terminal use — rather than inline code blocks re-generated on each run. When a step has a clear enough interface to write `--help` text for, it delegates to the `create-cli` skill for interface design, then scaffolds the script. Phase 3 delivers the skill to the correct path and explains every design decision.

### repair-skill

Audit and improve an existing skill against a gold standard. Triggers on phrases like "repair a skill", "audit a skill", "fix my skill", "improve an existing skill", "review skill quality", "check if my skill is well-written", or "what's wrong with this skill". Accepts a path to a skill directory or SKILL.md file as an argument.

The skill loads two reference files before auditing — the skill anatomy gold standard and the frontmatter options catalog — then runs seven audit dimensions:

**D1 — Frontmatter Quality.** Description person and framing, scalar type, trigger phrase authenticity and coverage, token density. Also flags missing `argument-hint` when the skill reads positional arguments.

**D2 — Execution Modifiers.** Model selection, context isolation, tool scope. Checks for both over-configuration (unrestricted `Bash`, dead tool entries, `opus` for tasks `sonnet` handles) and under-configuration (missing `AskUserQuestion` for interactive workflows, missing `context: fork` for heavy-output skills, `@$1` injection opportunities that a `Read` tool call is currently blocking).

**D3 — Intensional vs Extensional Instruction.** Identifies instruction blocks that teach by example when a stated rule would generalize better. An example requires two reasoning hops: infer the rule, then apply it. A stated rule is one hop, and it covers edge cases the examples didn't anticipate.

**D4 — Agentic vs Deterministic Split.** Applies the five script signal patterns (repeated generation, unclear tool choice, rigid contract, dual-use potential, consistency-critical operations) to every workflow step. Also flags judgment steps with no outcome criteria, and scripts that exist but aren't actionably referenced.

**D5 — Verbosity and Context Efficiency.** Redundant prose, hedging language, code blocks that collapse to one intensional rule, routing guidance in the body (dead tokens on every invocation since the body only loads post-trigger), headers deeper than H3, body exceeding 500 lines, extraneous documentation files.

**D6 — Workflow Clarity.** Phase structure, entry and exit conditions, half-thought steps, missing delivery format.

**D7 — Anatomy Completeness.** Compares the skill's directory structure against the correct tier (simple/standard/complex) and identifies absent infrastructure: missing `scripts/` for deterministic operations, missing `references/` when SKILL.md is too large, missing `examples/` for skills that produce user-adaptable output, unreferenced resource files that Claude won't load.

The output separates violations (something wrong) from gaps (something absent), each with the specific fix or addition needed. Confirmed repairs are applied in severity order with explicit reasoning for each change.

### improve-skill

Increase the effectiveness of an existing skill. Where `repair-skill` checks structural correctness against fixed rules, `improve-skill` asks whether the skill accomplishes what users actually need. Triggers on phrases like "improve a skill", "make this skill better", "add features to a skill", "what's missing from this skill", "the skill doesn't do X", or "improve how the skill works step by step".

The skill starts by understanding user intent via AskUserQuestion — establishing the specific complaint or running a full effectiveness audit if the user is unsure. It then runs four sub-analyses: mental simulation (walk through the skill as Claude with a real request, documenting stuck points, divergence points, dead ends, and friction), live doc validation (verify every factual claim — frontmatter field names, tool behavior, API parameters — against current documentation), feature adjacency scan (identify capabilities that are absent but adjacent, complementary, or needed to close end-to-end gaps), and UX flow review (check whether user interaction is placed at optimal points and consequential decisions are surfaced rather than made silently).

Findings are presented grouped by outcome type — new features, UX improvements, accuracy fixes, efficiency gains — and the user selects which to apply before any edits are made.

## Reference Library

All three skills share a `references/` library that they load during their workflows.

`skill-anatomy.md` defines the gold standard at each complexity tier, the three-level loading model (metadata always loaded, SKILL.md on trigger, resources on demand), directory type definitions with when-to-use criteria, the Degrees of Freedom table mapping task fragility to instruction specificity, and a Gap Analysis Checklist for identifying what a skill would benefit from adding.

`frontmatter-options.md` is the complete catalog of valid frontmatter fields, all valid values per field, the full tool list with blast-radius notes, and a tool selection framework with tier table and rationale. Loaded before any frontmatter or execution modifier audit.

`script-patterns.md` covers the five signal patterns for recognizing script and CLI candidates, CLI design conventions for skill context (argument structure, output format, exit codes, help text), five script archetypes (init/validate/transform/package/query) with canonical argument patterns, the Python script template, wiring rules for referencing scripts from SKILL.md, and the delegation pattern to `create-cli` for non-trivial interface design.

## Architecture Note

The skills in this plugin are regular directories shipped with the plugin. No symlinks or external sync needed — updates are delivered through the plugin version.

## License

MIT
