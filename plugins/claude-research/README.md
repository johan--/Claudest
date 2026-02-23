# claude-research

Cross-platform research skills for Claude Code.

## Installation

```
/plugin marketplace add gupsammy/claudest
/plugin install claude-research@claudest
```

## Skills

### run-research

Multi-source research across Reddit, X/Twitter, YouTube, and the web. Surfaces what people are actually discussing, recommending, and debating right now. Classifies intent (recommendations, news, prompting, general) and produces a structured report with real citations and a stats block.

Triggers on "research a topic", "run-research", "what's happening with X", "find the best X", "X prompts", "latest on X", "X news".

**Prerequisites:**

```bash
# Reddit (optional but recommended)
pip install reddit-cli    # or from ~/repos/myrepos/reddit-cli

# X / Twitter (optional)
brew install bird         # or follow https://github.com/steipete/bird

# YouTube (optional)
pip install yt-dlp

# Web (optional — falls back to Claude's native WebSearch)
# brave-cli from ~/repos/myrepos/brave-cli
```

### search-youtube

YouTube research toolkit built on `yt-dlp`. Individual operations: search, transcript, metadata, audio extraction, channel scanning, and batch processing. Also runs as an autonomous research pipeline that searches, evaluates, downloads transcripts, and synthesizes a structured report.

Triggers on "search YouTube", "find videos about", "get a transcript", "download subtitles", "extract audio from YouTube", "scan a channel", "research a topic on YouTube".

**Prerequisite:**

```bash
pip install yt-dlp
```

## License

MIT
