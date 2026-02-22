# Claudest

A curated Claude Code plugin marketplace. Everything here is something I personally use, build, and iterate on across real projects. If it's in this marketplace, it works.

## Installation

Add the marketplace, then install any plugin:

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-memory@claudest
```

To enable auto-updates, run `/plugin`, go to the Marketplaces tab, and toggle auto-update for Claudest.

## Plugins

### claude-memory

Conversation memory for Claude Code. Recall what happened yesterday, last week, or three weeks ago.

LLMs don't carry anything forward between sessions. Every conversation starts blank. Claude Code gives agents core memory (CLAUDE.md files loaded every session), procedural memory (skills and tool definitions), and archival memory (auto memory notes the agent writes for itself). What was missing: recall memory. The ability to search and retrieve actual past conversations.

That's what claude-memory provides. It stores every session in a SQLite database with full-text search (FTS5, BM25 ranking, zero external dependencies) and makes past conversations available to the agent in two ways.

First, automatic context injection. On every session start, a hook queries recent sessions and injects the most recent meaningful one into context. The agent already knows what you worked on last time before you say a word. This is what makes the plan-in-one-session, implement-in-the-next workflow possible.

Second, on-demand search. A past-conversations skill lets the agent (or you) search conversation history by keywords, browse recent sessions, or run structured analyses like retrospectives and gap-finding. Ask "what did we decide about the API design?" and the agent searches your history.

The search works because the agent constructs the queries, not you. When you ask about "the database migration," the agent extracts the right keywords, sends them to FTS5, and iterates if the first results aren't good enough. The agent compensates for the simplicity of the storage layer. No vector database, no embedding pipeline, no external dependencies. Just SQLite and Python's standard library.

The plugin also includes an extract-learnings skill, a route from recall into archival memory. It reads past conversations, identifies non-obvious insights and gotchas worth preserving, and proposes placing them at the right layer in the memory hierarchy (CLAUDE.md, MEMORY.md, or topic files) with diffs and rationale. Learnings that would otherwise evaporate when context resets get distilled into persistent knowledge.

For the full story behind the architecture, I wrote about the design decisions and what I learned about how agents actually use memory: [What I Learned Building a Memory System for My Coding Agent](https://www.reddit.com/r/ClaudeCode/comments/1r1w397/comment/o5294lk/).

```
/plugin install claude-memory@claudest
```

---

### claude-utilities

Useful tools that don't fit in a specific plugin.

Currently includes **web-to-markdown**, which converts any webpage to clean markdown, stripping ads, navigation, popups, and cookie banners. Uses [ezycopy](https://github.com/gupsammy/EzyCopy) under the hood.

```bash
# Prerequisite
curl -sSL https://raw.githubusercontent.com/gupsammy/EzyCopy/main/install.sh | sh
```

Triggers on "convert this page to markdown", "extract this webpage", "save this article", "grab content from URL", "scrape this page".

```
/plugin install claude-utilities@claudest
```

---

### claude-skills

Skill authoring tools for Claude Code. Two complementary skills: one that generates new skills and commands from scratch, one that audits and improves existing ones.

Writing a good skill is harder than it looks. The description has to route correctly without being verbose — it's loaded on every session regardless of whether the skill fires, so every token costs something. The body has to be precise enough to produce consistent outcomes but loose enough that the model isn't re-generating boilerplate that should be a script. The agentic and deterministic parts of the workflow should be deliberately separated, not accidentally mixed. Most skills that feel "fine" are underspecified, over-verbose, or missing infrastructure they'd benefit from.

`skill-creator` interviews you about requirements (or reads them from arguments), fetches the latest Claude Code documentation, and generates a skill or slash command with correct frontmatter, trigger phrases, progressive disclosure structure, and a script opportunity scan. It checks your workflow for steps that should be proper CLI tools — parameterized, dual-use, designed for both Claude invocation and direct terminal use — and either scaffolds them or delegates to the `create-cli` skill.

`skill-repair` reads an existing skill and produces a structured improvement report covering seven dimensions: frontmatter quality, execution modifiers, intensional vs extensional instruction, agentic/deterministic split, verbosity, workflow clarity, and anatomy completeness. The report distinguishes violations (something wrong) from gaps (something absent that would raise quality). It knows what a well-formed skill looks like at each complexity tier — simple, standard, complex — and can identify when a skill is missing infrastructure like reference files, scripts, or examples that would concretely improve it.

Both skills share a `references/` library: a skill anatomy gold standard, a complete frontmatter options catalog with tool selection framework, and a script patterns reference with five signal patterns for recognizing CLI candidates.

```
/plugin install claude-skills@claudest
```

---

### claude-coding

Git workflow skills for Claude Code. Three skills covering the full coding commit loop.

Every coding session involves the same git decisions: what belongs in one commit vs multiple, whether you're on the right branch before pushing, what to call the PR. These skills encode the right defaults and handle the mechanical parts so the workflow stays uninterrupted.

`commit` analyzes your changes, groups files by purpose rather than directory, runs the project's linter if one is configured, and writes a conventional commit message. It handles multi-concern changes by splitting them and committing foundational changes first.

`push-pr` detects if you're on `main` with unpushed commits, cuts a feature branch before pushing, and creates or updates a PR. It calls `commit` first if there are uncommitted changes. New PRs are opened; subsequent pushes to the same branch add a comment with the new commits.

`clean-branches` finds merged and stale branches (no commits in 30+ days), shows them categorized as safe-to-delete vs stale, and confirms before touching anything. Protected branches (main, master, develop, release/*) are never touched. Remote deletion requires explicit confirmation.

```
/plugin install claude-coding@claudest
```

---

## Contributing

This is a curated set of tools I personally maintain, not an open-submission marketplace. If you find bugs or have suggestions, open an issue. If you want to run your own marketplace with your own battle-tested tools, fork this and make it yours.

## License

MIT
