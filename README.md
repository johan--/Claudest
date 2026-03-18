<div align="center">

<h1>Claudest</h1>

<p>A curated Claude Code plugin marketplace. Everything here is something I personally use, build, and iterate on across real projects. If it's in this marketplace, it works.</p>

![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Release](https://img.shields.io/github/v/release/gupsammy/claudest?style=flat-square)
![Stars](https://img.shields.io/github/stars/gupsammy/claudest?style=social)

</div>

---

## ⚡ Installation

Add the marketplace, then install any plugin:

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-memory@claudest
```

To enable auto-updates, run `/plugin`, go to the Marketplaces tab, and toggle auto-update for Claudest.

---

<a id="claude-memory"></a>

### 🧠 claude-memory &nbsp; ![v0.8.6](https://img.shields.io/badge/v0.8.6-blue?style=flat-square)

Conversation memory for Claude Code. Recall what happened yesterday, last week, or three weeks ago.

LLMs don't carry anything forward between sessions. Every conversation starts blank. Claude Code gives agents core memory (CLAUDE.md files loaded every session), procedural memory (skills and tool definitions), and archival memory (auto memory notes the agent writes for itself). What was missing: recall memory. The ability to search and retrieve actual past conversations.

That's what claude-memory provides. It stores every session in a SQLite database with full-text search (FTS5, BM25 ranking, zero external dependencies) and makes past conversations available to the agent in two ways.

First, automatic context injection. On every session start, a hook queries recent sessions and injects the most recent meaningful one into context. The agent already knows what you worked on last time before you say a word. This is what makes the plan-in-one-session, implement-in-the-next workflow possible.

Second, on-demand search. The `recall-conversations` skill lets the agent (or you) search conversation history by keywords, browse recent sessions, or run structured analyses like retrospectives and gap-finding. Ask "what did we decide about the API design?" and the agent searches your history. The search works because the agent constructs the queries, not you — it extracts keywords, sends them to FTS5, and iterates if the first results aren't good enough. No vector database, no embedding pipeline, no external dependencies. Just SQLite and Python's standard library.

The `extract-learnings` skill is a route from recall memory into archival memory. It reads past conversations, identifies non-obvious insights and gotchas worth preserving, and proposes placing them at the right layer in the memory hierarchy (global CLAUDE.md, repo CLAUDE.md, MEMORY.md, or topic files) with diffs and rationale. Learnings that would otherwise evaporate when context resets get distilled into persistent knowledge.

For the full story behind the architecture: [What I Learned Building a Memory System for My Coding Agent](https://www.reddit.com/r/ClaudeCode/comments/1r1w397/comment/o5294lk/).

```
/plugin install claude-memory@claudest
```

---

<a id="claude-research"></a>

### 🔍 claude-research &nbsp; ![v0.2.2](https://img.shields.io/badge/v0.2.2-blue?style=flat-square)

Cross-platform research skills for Claude Code. Two complementary tools: a multi-source deep research pipeline and a standalone YouTube research toolkit.

`run-research` is an autonomous research agent that queries Reddit, X/Twitter, YouTube, and the web simultaneously, then synthesizes what it finds. It classifies your intent — recommendations, news, prompting techniques, or general exploration — and shapes the queries accordingly. Each source runs in full before synthesis begins. Results are weighted by engagement (upvotes, likes, reposts) because engagement is aggregate human signal. A stats block at the end shows exactly what was searched: thread counts, upvote totals, video counts, transcripts read. Every cited claim traces back to a real source — @handles, subreddit names, channel names — never raw URLs.

Sources are detected at runtime. If reddit-cli, bird, or brave-cli aren't installed, the pipeline skips them silently and surfaces setup instructions at the end of the report. The web search falls back to Claude's native `WebSearch` when brave-cli isn't configured, so you always get results from at least one source.

`search-youtube` is a YouTube research toolkit built on `yt-dlp`. In toolkit mode, it exposes individual operations: search with filters (minimum duration, date range, view count), transcript extraction with language selection and optional timestamps, full metadata without downloading, audio in any format (mp3, m4a, opus, wav), channel scanning by tab (videos, shorts, streams, playlists), and batch processing from a URL list. In research mode, it runs as an adaptive multi-round discovery pipeline with parallel Task agents and niche-first heuristics. It adjusts search strategy across rounds based on what it finds — starting broad, drilling into the most content-rich sub-niches, pruning dead ends — and produces a structured report with source attribution, points of agreement, contradictions, and gaps in coverage.

```bash
# Prerequisites — install only what you need, each source is optional
pip install yt-dlp           # YouTube (used by both skills)
pip install reddit-cli       # Reddit
brew install bird            # X / Twitter
# brave-cli — one-command installer included in run-research skill output
# Web search falls back to Claude's native WebSearch if brave-cli is missing
```

```
/plugin install claude-research@claudest
```

---

<a id="claude-coding"></a>

### 💻 claude-coding &nbsp; ![v0.2.6](https://img.shields.io/badge/v0.2.6-blue?style=flat-square)

Coding workflow skills for Claude Code. Eight skills covering the commit loop, project maintenance, and documentation.

Every coding session involves the same decisions: what belongs in one commit vs multiple, whether you're on the right branch before pushing, what to call the PR, whether your project docs still reflect reality. These skills encode the right defaults and handle the mechanical parts so the workflow stays uninterrupted.

`commit` analyzes your changes, groups files by purpose rather than directory, runs the project's linter if one is configured, and writes a conventional commit message. It handles multi-concern changes by splitting them and committing foundational changes first.

`push-pr` detects if you're on `main` with unpushed commits, cuts a feature branch before pushing, and creates or updates a PR. It calls `commit` first if there are uncommitted changes. New PRs are opened; subsequent pushes to the same branch add a comment with the new commits.

`clean-branches` finds merged and stale branches (no commits in 30+ days), shows them categorized as safe-to-delete vs stale, and confirms before touching anything. Protected branches (main, master, develop, release/*) are never touched. Remote deletion requires explicit confirmation.

`update-claudemd` audits and optimizes your project's CLAUDE.md. Reads the current file, explores the codebase to verify accuracy, cuts anything that doesn't change how Claude acts in the next session, and rewrites for scannability. Creates a `.bak` backup before writing.

`make-readme` generates a professional `README.md` through a structured interview. Asks about project type, depth (minimal → 50 lines, standard → structured with sections and badges, comprehensive → full documentation with API reference, FAQ, and TOC), and header style, then writes the full file in one pass with shields.io badges and styled headers.

`make-changelog` creates or updates `CHANGELOG.md` from git history using Keep-a-Changelog format. Detects existing changelog state, determines the scope (fresh, fill, or unreleased-only), and launches one Haiku subagent per version range in parallel for token-efficient processing. Categorizes commits by user-observable impact rather than commit prefix.

`update-readme` refreshes an existing `README.md` using current codebase state and git history. Runs three parallel research agents (README audit, codebase scan, git history since last touch), updates the changelog first, then applies targeted edits in priority order: version numbers and badge URLs, stale content, new features, and missing or thin sections.

`setup-github-actions` scaffolds and validates GitHub Actions workflows for your project. Generates correct workflow YAML, sets up permissions and triggers, and validates the configuration against the current GitHub Actions schema.

```
/plugin install claude-coding@claudest
```

---

<a id="claude-skills"></a>

### ✍️ claude-skills &nbsp; ![v0.5.5](https://img.shields.io/badge/v0.5.5-blue?style=flat-square)

Skill authoring tools for Claude Code. Six complementary skills that cover the full lifecycle: generate skills, generate agents, audit, improve, repair agents, and CLI design.

Writing a good skill is harder than it looks. The description has to route correctly without being verbose — it's loaded on every session regardless of whether the skill fires, so every token costs something. The body has to be precise enough to produce consistent outcomes but loose enough that the model isn't re-generating boilerplate that should be a script. The agentic and deterministic parts of the workflow should be deliberately separated, not accidentally mixed. Most skills that feel "fine" are underspecified, over-verbose, or missing infrastructure they'd benefit from.

`create-skill` interviews you about requirements (or reads them from arguments), fetches the latest Claude Code documentation, and generates a skill or slash command with correct frontmatter, trigger phrases, progressive disclosure structure, and a script opportunity scan. It checks your workflow for steps that should be proper CLI tools — parameterized, dual-use, designed for both Claude invocation and direct terminal use — and either scaffolds them or delegates to the `create-cli` skill.

`repair-skill` reads an existing skill and produces a structured improvement report covering seven dimensions: frontmatter quality, execution modifiers, intensional vs extensional instruction, agentic/deterministic split, verbosity, workflow clarity, and anatomy completeness. The report distinguishes violations (something wrong) from gaps (something absent that would raise quality). It knows what a well-formed skill looks like at each complexity tier — simple, standard, complex — and can identify when a skill is missing infrastructure like reference files, scripts, or examples that would concretely improve it.

`improve-skill` asks the complementary question: not "is this skill structurally correct?" but "does it accomplish what users need?" It models user intent, walks through the skill as Claude with a real request to find stuck points and dead ends, verifies factual claims against current documentation, scans for missing adjacent capabilities, and reviews UX flow for friction. Findings are grouped by outcome type — new features, accuracy fixes, UX improvements, efficiency gains — and applied with user selection.

`create-agent` generates well-structured Claude Code agents — markdown files with YAML frontmatter that delegate complex multi-step work to autonomous subprocesses with isolated context windows. It fetches the latest agent documentation before generating, then interviews you about requirements: expert persona, tool access (allowed/disallowed), isolation level, model, and triggering conditions. It knows the critical distinction between agents (isolated context, second-person system prompt, spawned via Task tool) and skills (inline injection, imperative instructions, description routing) and designs the right artifact for each use case.

`repair-agent` reads an existing Claude Code agent file and audits it against the same rubric as `repair-skill` but applied to agent-specific concerns: system prompt quality, tool access scope, context isolation correctness, triggering conditions, and example block completeness. Returns a structured report with violations, gaps, and applied fixes.

`create-cli` designs a complete CLI surface before implementation — flags, subcommands, output format, error schema, and configuration — through a structured interview. Defaults to an agent-aware baseline (explicit `--json`/`--markdown`/`--text` output mode flags, structured error objects with executable hints, NDJSON for list commands) that serves both agent callers and humans at a terminal without ambiguity.

All six skills share a `references/` library: a skill anatomy gold standard, a complete frontmatter options catalog with tool selection framework, a script patterns reference with five signal patterns for recognizing CLI candidates, and agent-aware CLI design guidelines. A `skill-lint` agent runs automatically after `create-skill` and `improve-skill` to validate structural quality — checking discovery trigger coverage, edge case handling, description quality, and five other audit dimensions — before the skill is delivered.

```
/plugin install claude-skills@claudest
```

---

<a id="claude-thinking"></a>

### 🤔 claude-thinking &nbsp; ![v0.2.2](https://img.shields.io/badge/v0.2.2-blue?style=flat-square)

Structured thinking tools for Claude Code. Skills that use dialogue to help you clarify, stress-test, and articulate ideas, then produce a written artifact.

Some of the best thinking happens in conversation, but unstructured conversation wanders. These skills provide just enough framework to keep the dialogue productive: domain-calibrated questioning intensity, saturation detection so it knows when to stop, and structured output so the results are reusable.

`brainstorm` conducts an in-depth interview calibrated to the domain — adversarial probing for strategy, gentle exploration for personal decisions, Socratic depth for abstract topics. Detects saturation after 4+ rounds of recurring themes and produces a synthesis document (spec, brief, decision doc, reflection) with key themes, decisions, open questions, and constraints. User quotes are woven into the synthesis where apt, never dumped as raw transcript.

```
/plugin install claude-thinking@claudest
```

---

<a id="claude-content"></a>

### 🎬 claude-content &nbsp; ![v0.4.2](https://img.shields.io/badge/v0.4.2-blue?style=flat-square)

Content creation and processing tools for Claude Code. Six skills covering image generation and the full video/audio manipulation workflow.

Most content tasks involve the same small set of operations repeated across projects: compress this for web, convert to a different format, make it fit Instagram, extract the audio, generate a thumbnail. The individual FFmpeg commands are tedious to remember and easy to get wrong — the right CRF for H.265, the palette generation pipeline for GIF quality, the aspect ratio math for Reels. These skills encode the correct defaults so you don't have to look them up.

`generate-image` calls Google's Gemini image generation API for text-to-image, image-to-image editing, and multi-reference composition. Two model tiers: Nano Banana (default) for fast generation with extended aspect ratios up to 8:1 panoramic, thinking mode for complex spatial reasoning, and Google Search grounding for factual content; and Nano Banana Pro for higher-quality output at up to 2K resolution. Supports JPEG output with configurable quality for high-volume workflows. Requires `GEMINI_API_KEY` and `uv`.

`compress-video` profiles the source first, then applies quality-based (CRF) encoding to hit a visual quality target or size-based (2-pass) encoding to hit a file size target — whichever the workflow needs.

`convert-video` is the general-purpose manipulation skill: format conversion, trim, speed adjustment, slow motion, timelapse, frame extraction, resize, rotate, flip, remux. Multi-operation requests are chained into a single ffmpeg invocation — no intermediate files, no quality loss from repeated encode passes.

`make-gif` uses the mandatory 2-pass palette workflow: `palettegen` builds an optimal 256-color palette from the clip's actual colors, then `paletteuse` renders with it. Single-pass GIF encoding produces banding and color artifacts. This doesn't.

`share-social` prepares video for platform-specific upload requirements: 9:16 for Shorts/Reels/TikTok, 1:1 for square posts, platform bitrate targets, and correct container settings. Presets for Instagram, YouTube Shorts, TikTok, Twitter, Facebook, and LinkedIn.

`extract-audio` rips the audio track from any video with format selection built in: FLAC for lossless archival, MP3 VBR for transparent compression, AAC for maximum compatibility.

Requires `ffmpeg` and `ffprobe`. Image generation additionally requires `GEMINI_API_KEY` and `uv`.

```
/plugin install claude-content@claudest
```

---

<a id="claude-utilities"></a>

### 🔧 claude-utilities &nbsp; ![v0.2.2](https://img.shields.io/badge/v0.2.2-blue?style=flat-square)

Useful tools that don't fit in a specific plugin.

`convert-to-markdown` converts any webpage to clean markdown, stripping ads, navigation, popups, and cookie banners. Uses [ezycopy](https://github.com/gupsammy/EzyCopy) under the hood. Triggers on "convert this page to markdown", "extract this webpage", "save this article", "grab content from URL", "scrape this page".

```bash
# Prerequisite
curl -sSL https://raw.githubusercontent.com/gupsammy/EzyCopy/main/install.sh | sh
```

```
/plugin install claude-utilities@claudest
```

---

<a id="claude-claw"></a>

### 🦞 claude-claw &nbsp; ![v0.3.2](https://img.shields.io/badge/v0.3.2-blue?style=flat-square)

OpenClaw advisory, troubleshooting, and configuration guidance for Claude Code.

OpenClaw is a local AI gateway — it routes model requests, manages channels (Telegram, webhooks, API), and handles multi-model configuration. Getting it set up correctly involves enough moving parts (gateway config, channel setup, provider selection, health checks) that having an advisor baked into the agent is useful.

`claw-advisor` answers OpenClaw questions, suggests optimal configuration, and diagnoses issues. It uses two backends: `clawdocs` for documentation lookup (always available) and `openclaw` for live state inspection (when the gateway is running). It classifies the question — focused, broad, troubleshooting, or design — and shapes the research accordingly. Focused questions get a single doc fetch; broad or cross-cutting questions spawn parallel subagents, one per topic area; troubleshooting questions always consult three sources — the domain doc, the domain troubleshooting page, and the general troubleshooting guide — then cross-references with `openclaw doctor` output if available.

Responses are structured: direct answer first, then exact config keys with full dot-paths usable with `openclaw config get/set`, context on why the configuration is recommended, known gotchas, and a list of doc slugs consulted so you can dive deeper. It never invents OpenClaw flags or config keys — every claim traces back to fetched documentation.

`create-claw-skill` generates new OpenClaw-compatible skills from scratch. It adapts the standard Claude Code skill authoring workflow to the OpenClaw ecosystem: clawhub frontmatter conventions, OpenClaw-specific tool access patterns, and skill deployment via the claw marketplace.

```
/plugin install claude-claw@claudest
```

---

## 🤝 Contributing

This is a curated set of tools I personally maintain, not an open-submission marketplace. If you find bugs or have suggestions, open an issue. If you want to run your own marketplace with your own battle-tested tools, fork this and make it yours.

## 📄 License

MIT
